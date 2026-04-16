"""
HELIOS Backend — Circadian Research Routes
Wraps Python research modules as FastAPI endpoints.

Routes:
  GET /api/circadian/chronotype       — MCTQ chronotype from sleep_logs
  GET /api/circadian/protocol-score   — ProtocolScorer effectiveness from protocol_logs
  GET /api/circadian/space-weather    — SpaceWeatherBioModel advisory (public, no auth)

Registered in main.py as:
    app.include_router(circadian_router, prefix="/api/circadian", tags=["circadian"])
"""

import sys
import os
import logging
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, Query, Request

# Add research/ to path (same pattern as backend/wearable/parsers/oura.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'research'))
from chronotype_engine import ChronotypeEngine, ProtocolScorer, SleepLog, ProtocolLog
from space_weather_bio import SpaceWeatherBioModel, SpaceWeatherReading

from backend.auth.supabase_auth import get_current_user_from_session

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _row_to_sleep_log(row: dict) -> SleepLog:
    """Convert Supabase sleep_logs row to SleepLog dataclass."""
    return SleepLog(
        date=row["date"],
        sleep_onset=datetime.fromisoformat(row["sleep_onset"]),
        wake_time=datetime.fromisoformat(row["wake_time"]),
        total_sleep_min=row["total_sleep_min"],
        deep_sleep_min=row.get("deep_sleep_min"),
        rem_sleep_min=row.get("rem_sleep_min"),
        hrv_avg=row.get("hrv_avg"),
        skin_temp_delta=row.get("skin_temp_delta"),
        resting_hr=row.get("resting_hr"),
        sleep_score=row.get("sleep_score"),
        source=row.get("source", "manual"),
    )


def _fetch_sleep_logs(supabase, user_id: str, days: int) -> list[SleepLog]:
    try:
        result = (
            supabase.table("sleep_logs")
            .select("*")
            .eq("user_id", user_id)
            .order("date", desc=True)
            .limit(days)
            .execute()
        )
        return [_row_to_sleep_log(row) for row in (result.data or [])]
    except Exception as e:
        logger.error("[circadian] sleep_logs fetch failed for user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Failed to fetch sleep data.")


# ─── Chronotype ──────────────────────────────────────────────────────────────

@router.get("/chronotype")
async def get_chronotype(
    request: Request,
    days: int = Query(default=30, ge=7, le=90, description="Days of sleep data to analyse"),
    user_id: str = Depends(get_current_user_from_session),
):
    """
    Derive MCTQ chronotype (MSFsc, social jet lag) from uploaded sleep logs.
    Requires at least 7 days of data — 14+ recommended for high confidence.
    """
    supabase = request.app.state.supabase
    logs = _fetch_sleep_logs(supabase, user_id, days)

    if not logs:
        raise HTTPException(
            status_code=404,
            detail="No sleep data found. Upload an Oura export via POST /api/wearable/upload first.",
        )

    engine = ChronotypeEngine()
    return engine.chronotype_from_logs(logs)


# ─── Protocol Score ───────────────────────────────────────────────────────────

@router.get("/protocol-score")
async def get_protocol_score(
    request: Request,
    days: int = Query(default=30, ge=7, le=90),
    user_id: str = Depends(get_current_user_from_session),
):
    """
    Score protocol effectiveness: HELIOS recommendations vs actual sleep outcomes.
    Requires both sleep_logs (from wearable) and protocol_logs (from app usage).
    """
    supabase = request.app.state.supabase

    # Fetch sleep logs
    sleep_logs = _fetch_sleep_logs(supabase, user_id, days)
    if not sleep_logs:
        raise HTTPException(status_code=404, detail="No sleep data found.")

    sleep_by_date = {log.date: log for log in sleep_logs}
    dates = list(sleep_by_date.keys())

    # Fetch protocol logs for the same dates
    try:
        proto_result = (
            supabase.table("protocol_logs")
            .select("*")
            .eq("user_id", user_id)
            .in_("date", dates)
            .execute()
        )
        proto_rows = proto_result.data or []
    except Exception as e:
        logger.error("[circadian] protocol_logs fetch failed for user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Failed to fetch protocol data.")

    if not proto_rows:
        raise HTTPException(
            status_code=404,
            detail=(
                "No protocol data found for these dates. "
                "Protocol adherence requires HELIOS to have been used for at least 7 days."
            ),
        )

    scorer = ProtocolScorer()
    daily_scores = []

    for row in proto_rows:
        date = row["date"]
        sleep = sleep_by_date.get(date)
        if not sleep or not row.get("recommended_sleep") or not row.get("recommended_wake"):
            continue

        protocol = ProtocolLog(
            date=date,
            recommended_sleep=datetime.fromisoformat(row["recommended_sleep"]),
            actual_sleep=sleep.sleep_onset,
            recommended_wake=datetime.fromisoformat(row["recommended_wake"]),
            actual_wake=sleep.wake_time,
            kp_index=float(row.get("kp_index") or 0.0),
            disruption_score=int(row.get("disruption_score") or 0),
            social_jet_lag_min=int(row.get("social_jet_lag_min") or 0),
        )
        score = scorer.effectiveness_score(protocol, sleep)
        daily_scores.append({"date": date, **score})

    if not daily_scores:
        raise HTTPException(status_code=422, detail="Could not compute scores — date overlap issue.")

    daily_scores.sort(key=lambda s: s["date"])
    trend = scorer.trend_analysis(daily_scores)

    return {
        "days_analysed": len(daily_scores),
        "trend": trend,
        "daily_scores": daily_scores,
    }


# ─── Space Weather Advisory (public — no auth required) ──────────────────────

@router.get("/space-weather")
async def get_space_weather_advisory(
    kp: float = Query(..., ge=0.0, le=9.0, description="Current Kp index (0–9)"),
    bz: float = Query(default=0.0, description="IMF Bz component in nanoTesla (negative = southward)"),
    sw_speed: float = Query(default=400.0, ge=200.0, le=900.0, description="Solar wind speed km/s"),
    lat: float = Query(default=45.0, ge=-90.0, le=90.0, description="Observer latitude (default mid-latitude 45°N)"),
):
    """
    Public endpoint — no authentication required.
    Returns biological advisory for current space weather conditions.

    SpaceWeatherReading fields: kp_index, solar_wind_speed, bz, timestamp, latitude.
    composite_disruption() takes a single SpaceWeatherReading object (not keyword args).
    """
    try:
        reading = SpaceWeatherReading(
            kp_index=kp,
            solar_wind_speed=sw_speed,
            bz=bz,
            timestamp=datetime.now(UTC),
            latitude=lat,
        )
        model = SpaceWeatherBioModel()
        result = model.composite_disruption(reading)
        return result
    except Exception as e:
        logger.error("[circadian] Space weather model error: %s", e)
        raise HTTPException(status_code=500, detail="Space weather model error.")
