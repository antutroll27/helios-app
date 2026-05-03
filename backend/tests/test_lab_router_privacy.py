from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.lab.router import router as lab_router


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(lab_router, prefix="/api/lab")
    return app


def test_generic_lab_calculators_remain_public():
    client = TestClient(build_app())

    response = client.get("/api/lab/exercise-timing", params={"hour": 7.5, "chronotype": "mid"})

    assert response.status_code == 200


def test_personal_context_lab_routes_require_auth():
    client = TestClient(build_app())

    supplement_response = client.get("/api/lab/supplements")
    sleep_response = client.post(
        "/api/lab/sleep-regularity",
        json=[
            {
                "date": "2026-05-01",
                "sleep_onset": "2026-05-01T23:00:00",
                "wake_time": "2026-05-02T07:00:00",
            },
            {
                "date": "2026-05-02",
                "sleep_onset": "2026-05-02T23:30:00",
                "wake_time": "2026-05-03T07:30:00",
            },
        ],
    )
    hrv_response = client.get("/api/lab/nocturnal-hrv", params={"hrv_rmssd": 42})
    jetlag_response = client.get(
        "/api/lab/jetlag-plan",
        params={
            "origin_offset_h": 5.5,
            "destination_offset_h": 9,
            "travel_date": "2026-05-04",
        },
    )

    assert supplement_response.status_code == 401
    assert sleep_response.status_code == 401
    assert hrv_response.status_code == 401
    assert jetlag_response.status_code == 401
