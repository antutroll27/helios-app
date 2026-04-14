from fastapi import FastAPI
from fastapi.testclient import TestClient
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from backend.public import router as public_router


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(public_router.router, prefix="/api/public", tags=["public"])
    app.state.supabase = MagicMock()
    return app


def test_environment_rejects_invalid_lat():
    client = TestClient(build_app())

    response = client.get("/api/public/environment?lat=999&lng=88")

    assert response.status_code == 422


def test_aqi_returns_cached_payload_without_upstream_fetch(monkeypatch):
    app = build_app()
    cache_row = {
        "payload": {"aqi_level": 42, "aqi_label": "Good", "pm25": 10},
        "expires_at": "2999-01-01T00:00:00+00:00",
    }
    query = app.state.supabase.table.return_value.select.return_value
    query.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[cache_row])

    fetch_upstream = AsyncMock()
    monkeypatch.setattr("backend.public.cache_service.fetch_aqi_upstream", fetch_upstream)

    client = TestClient(app)
    response = client.get("/api/public/aqi?lat=22.5&lng=88.3")

    assert response.status_code == 200
    assert response.json()["aqi_level"] == 42
    fetch_upstream.assert_not_awaited()


def test_environment_refreshes_when_cache_misses(monkeypatch):
    app = build_app()
    monkeypatch.setattr("backend.public.router.read_cache", AsyncMock(return_value=None))
    monkeypatch.setattr(
        "backend.public.router.fetch_environment_upstream",
        AsyncMock(
            return_value={
                "uv_index_now": 0,
                "uv_index_max": 6,
                "temperature_now": 24,
                "temperature_night": 20,
                "humidity": 75,
                "sunshine_duration_min": 420,
                "aqi_level": 61,
                "aqi_label": "Moderate",
                "pm25": 18,
            }
        ),
    )
    write_cache = MagicMock()
    monkeypatch.setattr("backend.public.router.write_cache", write_cache)

    client = TestClient(app)
    response = client.get("/api/public/environment?lat=22.5&lng=88.3")

    assert response.status_code == 200
    assert response.json()["temperature_now"] == 24
    write_cache.assert_called_once()
