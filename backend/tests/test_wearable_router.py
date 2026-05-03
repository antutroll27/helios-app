from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.research.chronotype_engine import SleepLog
from backend.wearable import router as wearable_router


class FakeParser:
    source_name = "fake"
    max_upload_bytes = 4

    def __init__(self):
        self.parse_calls = 0

    def can_handle(self, filename: str) -> bool:
        return filename.endswith(".fake")

    def parse(self, data: bytes, filename: str) -> list[SleepLog]:
        self.parse_calls += 1
        return [
            SleepLog(
                date="2026-05-01",
                sleep_onset=datetime(2026, 5, 1, 23, 0),
                wake_time=datetime(2026, 5, 2, 7, 0),
                total_sleep_min=480,
                hrv_avg=42,
                sleep_score=88,
                source=self.source_name,
            ),
            SleepLog(
                date="2026-05-02",
                sleep_onset=datetime(2026, 5, 2, 23, 30),
                wake_time=datetime(2026, 5, 3, 7, 30),
                total_sleep_min=450,
                hrv_avg=44,
                sleep_score=84,
                source=self.source_name,
            ),
        ]


class FakeTable:
    def __init__(self, name: str):
        self.name = name
        self.rows = []
        self.updated = []

    def insert(self, payload):
        self.rows.append(payload)
        return self

    def upsert(self, payload, on_conflict=None):
        self.rows.extend(payload)
        self.on_conflict = on_conflict
        return self

    def update(self, payload):
        self.updated.append(payload)
        return self

    def eq(self, *_args):
        return self

    def execute(self):
        if self.name == "data_imports" and self.rows:
            return SimpleNamespace(data=[{"id": "import-123"}])
        return SimpleNamespace(data=self.rows)


class FakeSupabase:
    def __init__(self):
        self.tables = {}

    def table(self, name: str):
        self.tables.setdefault(name, FakeTable(name))
        return self.tables[name]


async def fake_auth(request: Request) -> str:
    request.state.auth_session = {"id": "session-123", "user_id": "user-123"}
    return "user-123"


def build_app(parser: FakeParser, monkeypatch) -> FastAPI:
    app = FastAPI()
    app.include_router(wearable_router.router, prefix="/api/wearable")
    app.dependency_overrides[wearable_router.get_current_user_from_session] = fake_auth
    app.state.supabase = FakeSupabase()
    monkeypatch.setattr(wearable_router, "_PARSERS", [parser])
    return app


def test_upload_rejects_parser_specific_size_before_parsing(monkeypatch):
    parser = FakeParser()
    client = TestClient(build_app(parser, monkeypatch))

    response = client.post(
        "/api/wearable/upload",
        files={"file": ("sleep.fake", b"12345", "application/octet-stream")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "File exceeds 4 byte limit for fake."
    assert parser.parse_calls == 0


def test_upload_returns_summary_without_raw_logs(monkeypatch):
    parser = FakeParser()
    parser.max_upload_bytes = 1024
    client = TestClient(build_app(parser, monkeypatch))

    response = client.post(
        "/api/wearable/upload",
        files={"file": ("sleep.fake", b"ok", "application/octet-stream")},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["import_id"] == "import-123"
    assert payload["source"] == "fake"
    assert payload["records"] == 2
    assert payload["date_range"] == {"from": "2026-05-01", "to": "2026-05-02"}
    assert payload["summary"] == {
        "avg_total_sleep_min": 465,
        "avg_hrv": 43,
        "avg_sleep_score": 86,
    }
    assert "logs" not in payload
