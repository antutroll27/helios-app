from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth.router import router as auth_router


class FakeAuthApi:
    def sign_in_with_password(self, payload):
        assert payload == {"email": "user@example.com", "password": "secret123"}
        return SimpleNamespace(
            user=SimpleNamespace(id="user-123", email="user@example.com"),
        )

    def sign_up(self, payload):
        assert payload == {"email": "new@example.com", "password": "secret123"}
        return SimpleNamespace(
            user=SimpleNamespace(id="user-456", email="new@example.com"),
            session=None,
        )


class FakeUsersTable:
    def __init__(self):
        self.inserted = []

    def insert(self, payload):
        self.inserted.append(payload)
        return self

    def execute(self):
        return SimpleNamespace(data=self.inserted)


class FakeSupabase:
    def __init__(self):
        self.auth = FakeAuthApi()
        self.users_table = FakeUsersTable()

    def table(self, name):
        assert name == "users"
        return self.users_table


class FakeSessionService:
    def __init__(self):
        self.revoked = []
        self.active = {
            "session-123": {
                "id": "session-123",
                "user_id": "user-123",
                "email_snapshot": "user@example.com",
                "csrf_token_hash": "hashed-token",
            }
        }

    def issue_session(self, user_id, ip, user_agent, email=None):
        assert user_id in {"user-123", "user-456"}
        return (
            {
                "id": "session-123",
                "user_id": user_id,
                "email_snapshot": email,
                "csrf_token_hash": "hashed-token",
            },
            "csrf-token-123",
        )

    def get_active_session(self, session_id):
        return self.active.get(session_id)

    def revoke_session(self, session_id):
        self.revoked.append(session_id)

    def rotate_csrf_token(self, session_id):
        assert session_id == "session-123"
        return "rotated-csrf-token"


def build_app():
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/auth")
    app.state.supabase = FakeSupabase()
    app.state.session_service = FakeSessionService()
    return app


def test_login_sets_http_only_cookie():
    client = TestClient(build_app())

    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.cookies.get("helios_session") == "session-123"
    assert response.json()["user"]["email"] == "user@example.com"
    assert response.json()["csrfToken"] == "csrf-token-123"


def test_signup_returns_confirmation_state():
    client = TestClient(build_app())

    response = client.post(
        "/api/auth/signup",
        json={"email": "new@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.json()["requiresConfirmation"] is True
    assert response.json()["user"]["email"] == "new@example.com"


def test_me_reads_cookie_session():
    client = TestClient(build_app())
    client.cookies.set("helios_session", "session-123")

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["user"]["id"] == "user-123"
    assert response.json()["csrfToken"] == "rotated-csrf-token"


def test_logout_clears_cookie_and_revokes_session():
    app = build_app()
    client = TestClient(app)
    client.cookies.set("helios_session", "session-123")

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert app.state.session_service.revoked == ["session-123"]
