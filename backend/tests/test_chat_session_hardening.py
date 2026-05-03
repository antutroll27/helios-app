from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from backend.auth import supabase_auth
from backend.chat import router as chat_router


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(chat_router.router, prefix="/api/chat")
    app.dependency_overrides[supabase_auth.get_current_user] = lambda: "user-123"
    app.state.supabase = MagicMock()
    app.state.session_service = SimpleNamespace(
        sessions={
            "session-123": {
                "id": "session-123",
                "user_id": "user-123",
                "csrf_token_hash": "good-token",
            }
        },
        validate_csrf=lambda session, token: bool(token) and token == session["csrf_token_hash"],
    )
    app.state.memory_service = SimpleNamespace(
        get_memory_for_prompt=AsyncMock(return_value=""),
        process_session=AsyncMock(),
    )

    async def fake_cookie_auth(request: Request):
        request.state.auth_session = app.state.session_service.sessions["session-123"]
        return "user-123"

    app.dependency_overrides[supabase_auth.get_current_user_from_session] = fake_cookie_auth
    return app


def test_shared_usage_limit_denies_from_atomic_rpc(monkeypatch):
    app = build_app()
    client = TestClient(app)
    monkeypatch.setattr(chat_router, "SHARED_LLM_KEY", "shared-key")
    monkeypatch.setattr(chat_router, "SHARED_LLM_PROVIDER", "gemini")
    app.state.supabase.rpc.return_value.execute.return_value = SimpleNamespace(
        data={"allowed": False, "count": chat_router.SHARED_LLM_RATE_LIMIT, "limit": chat_router.SHARED_LLM_RATE_LIMIT}
    )

    response = client.post(
        "/api/chat/send",
        json={
            "message": "hello",
            "context": {"lat": 1.0, "lng": 2.0, "timezone": "UTC"},
            "history": [],
        },
        headers={"X-HELIOS-CSRF": "good-token"},
    )

    assert response.status_code == 429
    app.state.supabase.rpc.assert_called_once()


def test_shared_usage_consumption_uses_atomic_db_rpc(monkeypatch):
    db = MagicMock()
    db.rpc.return_value.execute.return_value = SimpleNamespace(
        data={"allowed": True, "count": 1, "limit": 20}
    )
    monkeypatch.setattr(chat_router, "SHARED_LLM_RATE_LIMIT", 20)

    usage = chat_router._consume_shared_llm_usage(db, "user-123")

    db.rpc.assert_called_once_with(
        "consume_shared_llm_usage",
        {"p_user_id": "user-123", "p_limit": 20},
    )
    assert usage == {"allowed": True, "count": 1, "limit": 20}


def test_shared_usage_consumption_rejects_when_rpc_denies(monkeypatch):
    db = MagicMock()
    db.rpc.return_value.execute.return_value = SimpleNamespace(
        data={"allowed": False, "count": 20, "limit": 20}
    )
    monkeypatch.setattr(chat_router, "SHARED_LLM_RATE_LIMIT", 20)

    with pytest.raises(HTTPException) as exc_info:
        chat_router._consume_shared_llm_usage(db, "user-123")

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Daily AI limit reached. Add your own API key in Settings for unlimited access."


def test_end_session_returns_already_processing_when_hermes_lock_is_set():
    app = build_app()
    client = TestClient(app)
    session_query = app.state.supabase.table.return_value.select.return_value
    session_query.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(
        data=[
            {
                "provider": "kimi",
                "encrypted_api_key": None,
                "ended_at": None,
                "hermes_processed": False,
                "hermes_processing": True,
            }
        ]
    )

    response = client.post(
        "/api/chat/end-session?session_id=session-123",
        headers={"X-HELIOS-CSRF": "good-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "already_processing", "session_id": "session-123"}
