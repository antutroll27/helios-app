from backend.auth.session_service import SessionCookieSettings, SessionService


class FakeInsertOperation:
    def __init__(self, table):
        self.table = table

    def execute(self):
        return type("Response", (), {"data": [self.table.last_insert]})


class FakeSelectOperation:
    def __init__(self, table, columns):
        self.table = table
        self.columns = columns
        self.filters: list[tuple[str, object]] = []

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def is_(self, key, value):
        self.filters.append((key, None if value == "null" else value))
        return self

    def execute(self):
        rows = self.table.rows
        for key, value in self.filters:
            rows = [row for row in rows if row.get(key) == value]
        return type("Response", (), {"data": rows})


class FakeUpdateOperation:
    def __init__(self, table, payload):
        self.table = table
        self.payload = payload
        self.filters: list[tuple[str, object]] = []

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def execute(self):
        updated = []
        for row in self.table.rows:
            if all(row.get(key) == value for key, value in self.filters):
                row.update(self.payload)
                updated.append(dict(row))
        return type("Response", (), {"data": updated})


class FakeTable:
    def __init__(self):
        self.rows: list[dict] = []
        self.last_insert: dict | None = None

    def insert(self, payload):
        row = dict(payload)
        self.rows.append(row)
        self.last_insert = row
        return FakeInsertOperation(self)

    def select(self, columns):
        return FakeSelectOperation(self, columns)

    def update(self, payload):
        return FakeUpdateOperation(self, payload)


class FakeSupabase:
    def __init__(self):
        self.tables = {"app_sessions": FakeTable()}

    def table(self, name):
        return self.tables[name]


def test_session_cookie_defaults_are_strict_enough(monkeypatch):
    monkeypatch.setattr("backend.auth.session_service.SESSION_COOKIE_NAME", "helios_session")
    monkeypatch.setattr("backend.auth.session_service.SESSION_COOKIE_SAMESITE", "lax")
    monkeypatch.setattr("backend.auth.session_service.SESSION_COOKIE_SECURE", True)

    settings = SessionCookieSettings.from_config()

    assert settings.cookie_name == "helios_session"
    assert settings.same_site == "lax"
    assert settings.http_only is True
    assert settings.secure is True


def test_issue_session_creates_opaque_id_and_csrf():
    service = SessionService(FakeSupabase(), ttl_hours=24)

    session, csrf_token = service.issue_session(
        user_id="user-123",
        ip="1.2.3.4",
        user_agent="test-agent",
    )

    assert session["id"] != "user-123"
    assert csrf_token
    assert session["csrf_token_hash"] != csrf_token
    assert session["ip_hash"]
    assert session["user_agent_hash"]


def test_validate_csrf_accepts_matching_token():
    service = SessionService(FakeSupabase(), ttl_hours=24)
    session, csrf_token = service.issue_session(
        user_id="user-123",
        ip="1.2.3.4",
        user_agent="test-agent",
    )

    assert service.validate_csrf(session, csrf_token) is True
    assert service.validate_csrf(session, "wrong-token") is False
    assert service.validate_csrf(session, None) is False


def test_get_active_session_skips_revoked_rows():
    db = FakeSupabase()
    service = SessionService(db, ttl_hours=24)
    session, _csrf_token = service.issue_session(
        user_id="user-123",
        ip=None,
        user_agent=None,
    )

    assert service.get_active_session(session["id"])["user_id"] == "user-123"

    service.revoke_session(session["id"])

    assert service.get_active_session(session["id"]) is None


def test_rotate_csrf_token_updates_hash_and_returns_new_token():
    db = FakeSupabase()
    service = SessionService(db, ttl_hours=24)
    session, csrf_token = service.issue_session(
        user_id="user-123",
        ip=None,
        user_agent=None,
    )

    rotated_token = service.rotate_csrf_token(session["id"])
    rotated_session = service.get_active_session(session["id"])

    assert rotated_token != csrf_token
    assert rotated_session is not None
    assert service.validate_csrf(rotated_session, rotated_token) is True
