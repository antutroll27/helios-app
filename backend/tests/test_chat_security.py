from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from backend.auth import supabase_auth
from backend.chat import router as chat_router


class FakeSessionService:
    def __init__(self):
        self.sessions = {
            "session-123": {
                "id": "session-123",
                "user_id": "user-123",
                "email_snapshot": "user@example.com",
                "csrf_token_hash": "good-token",
            }
        }

    def get_active_session(self, session_id: str):
        return self.sessions.get(session_id)

    def validate_csrf(self, session, token: str | None):
        return bool(token) and token == session["csrf_token_hash"]


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
    app.dependency_overrides[supabase_auth.get_current_user] = lambda: "user-123"
    app.state.supabase = SimpleNamespace()
    app.state.session_service = FakeSessionService()
    app.state.memory_service = SimpleNamespace(
        get_memory_for_prompt=AsyncMock(return_value=""),
        process_session=AsyncMock(),
    )

    async def fake_cookie_auth(request: Request):
        request.state.auth_session = app.state.session_service.sessions["session-123"]
        return "user-123"

    app.dependency_overrides[supabase_auth.get_current_user_from_session] = fake_cookie_auth
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
        headers={"X-HELIOS-CSRF": "good-token"},
    )

    assert response.status_code == 422


def test_send_rejects_history_content_over_limit():
    client = TestClient(make_app())

    response = client.post(
        "/api/chat/send",
        json=valid_payload(
            history=[{"role": "user", "content": "x" * 4097}],
        ),
        headers={"X-HELIOS-CSRF": "good-token"},
    )

    assert response.status_code == 422


def test_send_rejects_history_over_limit():
    client = TestClient(make_app())

    response = client.post(
        "/api/chat/send",
        json=valid_payload(
            history=[{"role": "user", "content": "ok"} for _ in range(21)],
        ),
        headers={"X-HELIOS-CSRF": "good-token"},
    )

    assert response.status_code == 422


def test_send_sanitizes_llm_errors(monkeypatch):
    app = make_app()
    app.state.supabase = MagicMock()
    client = TestClient(app)

    async def boom(**_kwargs):
        raise RuntimeError("provider exploded: leaked detail")

    monkeypatch.setattr(chat_router, "call_llm", boom)

    response = client.post(
        "/api/chat/send",
        json=valid_payload(),
        headers={"X-HELIOS-CSRF": "good-token"},
    )

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


@pytest.mark.asyncio
async def test_session_auth_rejects_bearer_token_without_backend_cookie(monkeypatch):
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(session_service=FakeSessionService())),
        cookies={},
        state=SimpleNamespace(),
    )
    monkeypatch.setattr(supabase_auth, "get_current_user", AsyncMock(return_value="user-123"))

    with pytest.raises(HTTPException) as exc_info:
        await supabase_auth.get_current_user_from_session(request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized"


def test_send_rejects_missing_csrf_when_cookie_session_is_used(monkeypatch):
    app = FastAPI()
    app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
    app.state.supabase = MagicMock()
    app.state.session_service = FakeSessionService()
    app.state.memory_service = SimpleNamespace(
        get_memory_for_prompt=AsyncMock(return_value=""),
        process_session=AsyncMock(),
    )
    client = TestClient(app)
    client.cookies.set("helios_session", "session-123")

    async def fake_call_llm(**_kwargs):
        return {"message": "ok", "visual_cards": []}

    monkeypatch.setattr(chat_router, "call_llm", fake_call_llm)
    monkeypatch.setattr(chat_router, "parse_ai_response", lambda payload: payload)

    response = client.post("/api/chat/send", json=valid_payload())

    assert response.status_code == 403


def test_send_accepts_cookie_session_and_csrf(monkeypatch):
    app = FastAPI()
    app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
    app.state.supabase = MagicMock()
    app.state.session_service = FakeSessionService()
    app.state.memory_service = SimpleNamespace(
        get_memory_for_prompt=AsyncMock(return_value=""),
        process_session=AsyncMock(),
    )
    client = TestClient(app)
    client.cookies.set("helios_session", "session-123")

    async def fake_call_llm(**_kwargs):
        return {"message": "ok", "visual_cards": []}

    monkeypatch.setattr(chat_router, "call_llm", fake_call_llm)
    monkeypatch.setattr(chat_router, "parse_ai_response", lambda payload: payload)
    monkeypatch.setattr(chat_router, "encrypt_api_key", lambda api_key: f"enc:{api_key}")
    app.state.supabase.table.return_value.insert.return_value.execute.return_value = SimpleNamespace(
        data=[{"id": "new-session-1"}]
    )

    response = client.post(
        "/api/chat/send",
        json=valid_payload(),
        headers={"X-HELIOS-CSRF": "good-token"},
    )

    assert response.status_code == 200

