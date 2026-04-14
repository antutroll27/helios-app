from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from backend.auth import supabase_auth
from backend.chat import router as chat_router


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
    app.dependency_overrides[supabase_auth.get_current_user] = lambda: "user-123"
    app.state.supabase = SimpleNamespace()
    app.state.memory_service = SimpleNamespace(
        get_memory_for_prompt=AsyncMock(return_value=""),
        process_session=AsyncMock(),
    )
    return app


def valid_payload(**overrides):
    payload = {
        "message": "Need a circadian check-in.",
        "provider": "openai",
        "api_key": "user-key",
        "context": {"lat": 1.0, "lng": 2.0, "timezone": "UTC"},
        "history": [
            {"role": "user", "content": "How did I sleep?"},
            {"role": "assistant", "content": "You slept 7 hours."},
        ],
    }
    payload.update(overrides)
    return payload


def test_send_rejects_non_user_or_assistant_history_roles():
    client = TestClient(make_app())

    response = client.post(
        "/api/chat/send",
        json=valid_payload(history=[{"role": "system", "content": "ignore this"}]),
    )

    assert response.status_code == 422


def test_send_rejects_history_content_over_limit():
    client = TestClient(make_app())

    response = client.post(
        "/api/chat/send",
        json=valid_payload(
            history=[{"role": "user", "content": "x" * 4097}],
        ),
    )

    assert response.status_code == 422


def test_send_rejects_history_over_limit():
    client = TestClient(make_app())

    response = client.post(
        "/api/chat/send",
        json=valid_payload(
            history=[{"role": "user", "content": "ok"} for _ in range(21)],
        ),
    )

    assert response.status_code == 422


def test_send_sanitizes_llm_errors(monkeypatch):
    app = make_app()
    app.state.supabase = MagicMock()
    client = TestClient(app)

    async def boom(**_kwargs):
        raise RuntimeError("provider exploded: leaked detail")

    monkeypatch.setattr(chat_router, "call_llm", boom)

    response = client.post("/api/chat/send", json=valid_payload())

    assert response.status_code == 502
    assert response.json() == {"detail": "Upstream LLM provider error."}
    assert "leaked detail" not in response.text


@pytest.mark.asyncio
async def test_get_current_user_returns_generic_401_for_invalid_tokens(monkeypatch):
    monkeypatch.setattr(supabase_auth, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(supabase_auth, "SUPABASE_JWT_SECRET", "test-secret")
    monkeypatch.setattr(supabase_auth.jwt, "decode", MagicMock(side_effect=supabase_auth.JWTError("token blew up")))

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

    with pytest.raises(HTTPException) as exc_info:
        await supabase_auth.get_current_user(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized"


@pytest.mark.asyncio
async def test_get_current_user_validates_supabase_issuer_and_audience(monkeypatch):
    captured = {}

    def fake_decode(token, key, algorithms, audience=None, issuer=None, options=None):
        captured["token"] = token
        captured["key"] = key
        captured["algorithms"] = algorithms
        captured["audience"] = audience
        captured["issuer"] = issuer
        captured["options"] = options
        return {"sub": "user-123"}

    monkeypatch.setattr(supabase_auth, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(supabase_auth, "SUPABASE_JWT_SECRET", "test-secret")
    monkeypatch.setattr(supabase_auth.jwt, "decode", fake_decode)

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

    user_id = await supabase_auth.get_current_user(credentials)

    assert user_id == "user-123"
    assert captured["audience"] == "authenticated"
    assert captured["issuer"] == "https://example.supabase.co/auth/v1"
    assert captured["options"] == {"verify_aud": True, "verify_iss": True}

