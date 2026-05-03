"""
HELIOS Backend — Lab Research Routes
Wraps exercise timing, meal window, supplement, HRV/sleep regularity,
cold exposure, and jet lag optimizer models as FastAPI endpoints.

Routes:
  GET /api/lab/exercise-timing    — Phase shift for exercise hour + chronotype
  GET /api/lab/meal-window        — TRF score for first/last meal + sleep time
  GET /api/lab/supplements        — Ranked supplement list for goal + biometrics context
  GET /api/lab/sleep-regularity   — SRI + bedtime std-dev from sleep window list
  GET /api/lab/nocturnal-hrv      — Interpret a single night's rMSSD value
  GET /api/lab/cold-exposure      — NE/dopamine/DOMS model for cold water immersion
  GET /api/lab/jetlag-plan        — Day-by-day light schedule for jet lag recovery

Generic calculators stay public. Routes that accept personal sleep, HRV, age,
travel, or biometric context require auth.
Registered in main.py as:
    app.include_router(lab_router, prefix="/api/lab", tags=["lab"])
"""

import sys
import os
import logging
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.auth.supabase_auth import get_current_user_from_session

# Add backend/research/ to path (same pattern as circadian/router.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'research'))

from exercise_timing_model import calculate_exercise_phase_shift
from meal_timing_model import calculate_meal_window
from supplement_model import rank_supplements
from hrv_sleep_model import SleepWindow, analyse_sleep_regularity, interpret_nocturnal_hrv
from cold_exposure_model import analyse_cold_exposure
from jetlag_optimizer import generate_jetlag_plan

logger = logging.getLogger(__name__)
router = APIRouter()

# Public routes in this file are limited to generic calculators. Endpoints that
# accept sleep, HRV, age, travel, or other personal context require auth below.

# ─── Exercise Timing ─────────────────────────────────────────────────────────

@router.get("/exercise-timing")
async def get_exercise_timing(
    hour: float = Query(..., ge=0.0, lt=24.0, description="Exercise time as decimal hour (e.g. 7.5 = 07:30)"),
    chronotype: str = Query(default="mid", description="Chronotype: 'early' | 'mid' | 'late'"),
):
    """
    Return the estimated circadian phase shift from exercising at *hour*
    for the given *chronotype* (Youngstedt 2019 PRC + Thomas 2020 scaling).

    Positive shift_min = phase advance (sleep/wake earlier).
    Negative shift_min = phase delay (sleep/wake later).
    """
    if chronotype not in ("early", "mid", "late"):
        raise HTTPException(status_code=422, detail="chronotype must be 'early', 'mid', or 'late'.")

    return calculate_exercise_phase_shift(hour=hour, chronotype=chronotype)


# ─── Meal Window ──────────────────────────────────────────────────────────────

@router.get("/meal-window")
async def get_meal_window(
    first_meal_hour: float = Query(..., ge=0.0, lt=24.0, description="First caloric intake (decimal hour, e.g. 8.0)"),
    last_meal_hour: float = Query(..., ge=0.0, lt=24.0, description="Last caloric intake (decimal hour, e.g. 18.5)"),
    sleep_hour: float = Query(..., ge=0.0, lt=30.0, description="Sleep onset (decimal hour; may exceed 24 for after-midnight, e.g. 25.5)"),
):
    """
    Score a time-restricted feeding window.

    Returns a 0–100 score plus glucose benefit annotation.
    Validation: first_meal < last_meal < sleep_hour (same-day times).
    """
    result = calculate_meal_window(
        first_meal_hour=first_meal_hour,
        last_meal_hour=last_meal_hour,
        sleep_hour=sleep_hour,
    )

    if not result.get("valid", True):
        raise HTTPException(status_code=422, detail=result["error"])

    return result


# ─── Supplement Ranking ───────────────────────────────────────────────────────

@router.get("/supplements")
async def get_supplement_ranking(
    goal: str = Query(
        default="sleep_onset",
        description="Goal: 'sleep_onset' | 'recovery_support' | 'stress_resilience' | 'jet_lag_support' | 'circadian_realignment'",
    ),
    chronotype: str = Query(default="mid", description="Chronotype: 'early' | 'mid' | 'late'"),
    travel_state: str = Query(default="none", description="Travel: 'none' | 'eastbound_shift' | 'westbound_shift'"),
    hrv: Optional[float] = Query(default=None, ge=0.0, le=200.0, description="Average HRV rMSSD in ms"),
    sleep_score: Optional[float] = Query(default=None, ge=0.0, le=100.0, description="Average sleep score 0–100"),
    total_sleep_hours: Optional[float] = Query(default=None, ge=0.0, le=24.0, description="Average total sleep hours"),
    _user_id: str = Depends(get_current_user_from_session),
):
    """
    Return all four supplements ranked by contextual relevance score (0–5).

    Scoring uses goal, chronotype, travel state, and optional biometric signals
    (HRV, sleep score, total sleep hours). Ties broken by goal-specific priority.
    """
    valid_goals = ("sleep_onset", "recovery_support", "stress_resilience", "jet_lag_support", "circadian_realignment")
    if goal not in valid_goals:
        raise HTTPException(status_code=422, detail=f"goal must be one of: {', '.join(valid_goals)}")
    if chronotype not in ("early", "mid", "late"):
        raise HTTPException(status_code=422, detail="chronotype must be 'early', 'mid', or 'late'.")
    if travel_state not in ("none", "eastbound_shift", "westbound_shift"):
        raise HTTPException(status_code=422, detail="travel_state must be 'none', 'eastbound_shift', or 'westbound_shift'.")

    return rank_supplements(
        goal=goal,
        chronotype=chronotype,
        travel_state=travel_state,
        hrv=hrv,
        sleep_score=sleep_score,
        total_sleep_hours=total_sleep_hours,
    )


# ─── Sleep Regularity ─────────────────────────────────────────────────────────

class SleepWindowIn(BaseModel):
    date: str
    sleep_onset: str   # ISO datetime string
    wake_time: str     # ISO datetime string


@router.post("/sleep-regularity")
async def get_sleep_regularity(
    windows: List[SleepWindowIn],
    _user_id: str = Depends(get_current_user_from_session),
):
    """
    Compute Sleep Regularity Index (SRI) and timing variability.

    POST body: list of {date, sleep_onset, wake_time} objects (ISO datetimes).
    Minimum 2 nights; 7+ recommended for a reliable SRI.
    """
    if len(windows) < 2:
        raise HTTPException(status_code=422, detail="At least 2 sleep windows required.")

    try:
        parsed = [
            SleepWindow(
                date=w.date,
                sleep_onset=__import__("datetime").datetime.fromisoformat(w.sleep_onset),
                wake_time=__import__("datetime").datetime.fromisoformat(w.wake_time),
            )
            for w in windows
        ]
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid datetime format: {e}")

    return analyse_sleep_regularity(parsed)


@router.get("/nocturnal-hrv")
async def get_nocturnal_hrv(
    hrv_rmssd: float = Query(..., ge=0.0, le=200.0, description="Nocturnal rMSSD in ms"),
    age: Optional[int] = Query(default=None, ge=10, le=100, description="Age in years (optional, for age-adjusted reference)"),
    _user_id: str = Depends(get_current_user_from_session),
):
    """Interpret a single night's nocturnal rMSSD value with age-adjusted reference band."""
    return interpret_nocturnal_hrv(hrv_rmssd=hrv_rmssd, age=age)


# ─── Cold Exposure ────────────────────────────────────────────────────────────

@router.get("/cold-exposure")
async def get_cold_exposure(
    temp_c: float = Query(..., ge=1.0, le=30.0, description="Water temperature °C (effective range 5–20°C)"),
    duration_min: float = Query(..., ge=0.5, le=30.0, description="Immersion duration in minutes"),
    hours_before_sleep: float = Query(default=10.0, ge=0.0, le=24.0, description="Hours between session end and sleep onset"),
    post_exercise: bool = Query(default=False, description="True if used immediately after training"),
    habituated: bool = Query(default=False, description="True if practicing CWI regularly for 4+ weeks"),
):
    """
    Model norepinephrine, dopamine, and DOMS-reduction response to cold water immersion.
    Returns timing advisory and safety cautions.
    """
    return analyse_cold_exposure(
        temp_c=temp_c,
        duration_min=duration_min,
        hours_before_sleep=hours_before_sleep,
        post_exercise=post_exercise,
        habituated=habituated,
    )


# ─── Jet Lag Plan ─────────────────────────────────────────────────────────────

@router.get("/jetlag-plan")
async def get_jetlag_plan(
    origin_offset_h: float = Query(..., ge=-12.0, le=14.0, description="Origin UTC offset in hours (e.g. 7.0 for Bangkok)"),
    destination_offset_h: float = Query(..., ge=-12.0, le=14.0, description="Destination UTC offset in hours (e.g. 9.0 for Tokyo)"),
    travel_date: str = Query(..., description="Departure date as YYYY-MM-DD"),
    usual_sleep_h: float = Query(default=23.0, ge=18.0, le=30.0, description="Habitual sleep onset as decimal hour in origin tz"),
    usual_wake_h: float = Query(default=7.0, ge=0.0, le=14.0, description="Habitual wake time as decimal hour in origin tz"),
    chronotype: str = Query(default="mid", description="Chronotype: 'early' | 'mid' | 'late'"),
    use_melatonin: bool = Query(default=True, description="Include melatonin timing in plan"),
    _user_id: str = Depends(get_current_user_from_session),
):
    """
    Generate a day-by-day light exposure + melatonin schedule to minimise jet lag.
    Based on Kronauer PRC and Eastman & Burgess 2009 timing rules.
    """
    if chronotype not in ("early", "mid", "late"):
        raise HTTPException(status_code=422, detail="chronotype must be 'early', 'mid', or 'late'.")

    try:
        parsed_date = date.fromisoformat(travel_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="travel_date must be YYYY-MM-DD.")

    return generate_jetlag_plan(
        origin_offset_h=origin_offset_h,
        destination_offset_h=destination_offset_h,
        travel_date=parsed_date,
        usual_sleep_h=usual_sleep_h,
        usual_wake_h=usual_wake_h,
        chronotype=chronotype,
        use_melatonin=use_melatonin,
    )
