import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from backend.public.cache_service import read_cache
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


def test_read_cache_treats_invalid_expiry_as_cache_miss():
    db = MagicMock()
    query = db.table.return_value.select.return_value
    query.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(
        data=[{"payload": {"aqi_level": 40}, "expires_at": "not-a-real-date"}]
    )

    result = asyncio.run(read_cache(db, "aqi", "22.500:88.300"))

    assert result is None


def test_public_routes_rate_limit_by_forwarded_ip(monkeypatch):
    app = build_app()
    monkeypatch.setattr(public_router, "PUBLIC_ROUTE_MAX_REQUESTS", 1)
    monkeypatch.setattr(public_router, "PUBLIC_ROUTE_WINDOW_SECONDS", 60)
    monkeypatch.setattr(public_router, "read_cache", AsyncMock(return_value={"aqi_level": 42}))
    public_router._public_route_usage.clear()

    client = TestClient(app)
    headers = {"x-forwarded-for": "203.0.113.9"}

    first = client.get("/api/public/aqi?lat=22.5&lng=88.3", headers=headers)
    second = client.get("/api/public/aqi?lat=22.5&lng=88.3", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 429
