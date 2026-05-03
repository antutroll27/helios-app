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

    def exchange_code_for_session(self, payload):
        assert payload["auth_code"] == "oauth-code-123"
        assert payload["code_verifier"] == "verifier-123"
        assert payload["redirect_to"] == "http://testserver/api/auth/oauth/callback"
        return SimpleNamespace(
            user=SimpleNamespace(id="user-789", email="google@example.com"),
            session=SimpleNamespace(access_token="backend-only-token"),
        )


class FakeUsersTable:
    def __init__(self):
        self.inserted = []
        self.on_conflict = None

    def insert(self, payload):
        self.inserted.append(payload)
        return self

    def upsert(self, payload, on_conflict=None):
        self.inserted.append(payload)
        self.on_conflict = on_conflict
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
        assert user_id in {"user-123", "user-456", "user-789"}
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


def test_oauth_start_redirects_to_supabase_and_sets_pkce_cookies(monkeypatch):
    monkeypatch.setattr("backend.auth.router._generate_pkce_verifier", lambda: "verifier-123")
    monkeypatch.setattr("backend.auth.router._generate_oauth_state", lambda: "state-123")
    monkeypatch.setattr("backend.auth.router.SUPABASE_URL", "https://zciyjaaigefeearpzsip.supabase.co")

    client = TestClient(build_app(), follow_redirects=False)

    response = client.get(
        "/api/auth/oauth/start",
        params={"provider": "google", "redirect": "/lab", "return_origin": "http://localhost:5173"},
    )

    assert response.status_code == 307
    assert response.cookies.get("helios_oauth_state") == "state-123"
    assert response.cookies.get("helios_oauth_verifier") == "verifier-123"
    assert response.cookies.get("helios_oauth_redirect") == "%2Flab"
    assert response.cookies.get("helios_oauth_origin") == "http%3A%2F%2Flocalhost%3A5173"
    assert response.headers["location"].startswith("https://zciyjaaigefeearpzsip.supabase.co/auth/v1/authorize?")
    assert "provider=google" in response.headers["location"]
    assert "code_challenge=" in response.headers["location"]


def test_legacy_browser_token_oauth_exchange_is_not_registered():
    client = TestClient(build_app(), follow_redirects=False)

    response = client.post("/api/auth/oauth", json={"access_token": "supabase-token"})

    assert response.status_code == 404


def test_oauth_callback_exchanges_code_server_side_and_redirects(monkeypatch):
    monkeypatch.setattr("backend.auth.router.SUPABASE_URL", "https://zciyjaaigefeearpzsip.supabase.co")

    client = TestClient(build_app(), follow_redirects=False)
    client.cookies.set("helios_oauth_state", "state-123")
    client.cookies.set("helios_oauth_verifier", "verifier-123")
    client.cookies.set("helios_oauth_redirect", "/lab")
    client.cookies.set("helios_oauth_origin", "http://localhost:5173")

    response = client.get("/api/auth/oauth/callback", params={"code": "oauth-code-123", "state": "state-123"})

    assert response.status_code == 307
    assert response.headers["location"] == "http://localhost:5173/lab"
    assert response.cookies.get("helios_session") == "session-123"
    assert response.cookies.get("helios_oauth_state") is None
    assert response.cookies.get("helios_oauth_verifier") is None
