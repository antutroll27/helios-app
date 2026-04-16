"""
HELIOS Backend — Wearable Upload Router
POST /api/wearable/upload — accepts Oura Ring ZIP or JSON export.
Parses with OuraParser (already implemented in parsers/oura.py), upserts to sleep_logs.

Registered in main.py as:
    app.include_router(wearable_router, prefix="/api/wearable", tags=["wearable"])
so the full endpoint path is POST /api/wearable/upload.
"""

import io
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File

from backend.auth.supabase_auth import get_current_user_from_session
from backend.wearable.parsers.oura import OuraParser

logger = logging.getLogger(__name__)
router = APIRouter()

_MAX_FILE_BYTES = 100 * 1024 * 1024  # 100 MB


def _sleep_log_to_row(log, user_id: str) -> dict:
    """
    Map OuraParser SleepLog dataclass to sleep_logs table columns.
    Note: SleepLog.alarm_used is intentionally omitted — schema.sql has no alarm_used column.
    Oura Ring exports don't provide alarm data anyway.
    """
    return {
        "user_id": user_id,
        "date": log.date,
        "sleep_onset": log.sleep_onset.isoformat(),
        "wake_time": log.wake_time.isoformat(),
        "total_sleep_min": log.total_sleep_min,
        "deep_sleep_min": log.deep_sleep_min,
        "rem_sleep_min": log.rem_sleep_min,
        "hrv_avg": log.hrv_avg,
        "skin_temp_delta": log.skin_temp_delta,
        "resting_hr": log.resting_hr,
        "sleep_score": log.sleep_score,
        "source": log.source or "oura",
    }


@router.post("/upload")
async def upload_wearable(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_from_session),
):
    """
    Accept Oura Ring data export (.zip or .json).
    Parse into SleepLog records, upsert to sleep_logs, return summary.

    File format guidance:
    - .zip: Full Oura export (preferred). Extracts sleep.json + daily_sleep.json automatically,
            so sleep_score is populated from daily_sleep data.
    - .json: Must be Oura's sleep.json format (contains bedtime_start, bedtime_end fields).
             Uploading daily_sleep.json or other Oura JSON files will return a 422 (no records).
             sleep_score will be None (no daily_sleep.json to join against).

    Conflict resolution: upsert on (user_id, date) — newer upload wins.
    Requires schema_v2.sql applied (adds UNIQUE constraint on sleep_logs).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    filename = file.filename.lower()
    if not (filename.endswith(".zip") or filename.endswith(".json")):
        raise HTTPException(status_code=400, detail="Upload must be a .zip or .json Oura export.")

    content = await file.read()
    if len(content) > _MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 100 MB limit.")

    supabase = request.app.state.supabase
    parser = OuraParser()

    # Parse
    try:
        if filename.endswith(".zip"):
            logs = parser.parse_zip(content)
        else:
            data = json.loads(content.decode("utf-8"))
            logs = parser.parse_json(data)
    except Exception as e:
        logger.warning("[wearable] Parse failed for %s: %s", filename, e)
        raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")

    if not logs:
        raise HTTPException(status_code=422, detail="No sleep records found in file.")

    # Record import
    try:
        import_result = supabase.table("data_imports").insert({
            "user_id": user_id,
            "filename": file.filename,
            "platform": "oura",
            "status": "processing",
            "records_imported": 0,
        }).execute()
        import_id = import_result.data[0]["id"]
    except Exception as e:
        logger.error("[wearable] data_imports insert failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to record import.")

    # Upsert sleep logs (conflict on user_id + date — requires schema_v2.sql UNIQUE constraint)
    rows = [_sleep_log_to_row(log, user_id) for log in logs]
    try:
        supabase.table("sleep_logs").upsert(
            rows,
            on_conflict="user_id,date",
        ).execute()
    except Exception as e:
        logger.error("[wearable] sleep_logs upsert failed: %s", e)
        supabase.table("data_imports").update({
            "status": "failed",
            "error_message": str(e),
        }).eq("id", import_id).execute()
        raise HTTPException(status_code=500, detail="Failed to save sleep data.")

    # Mark import complete
    supabase.table("data_imports").update({
        "status": "complete",
        "records_imported": len(logs),
    }).eq("id", import_id).execute()

    return {
        "import_id": import_id,
        "records": len(logs),
        "date_range": {
            "from": min(log.date for log in logs),
            "to": max(log.date for log in logs),
        },
        "logs": [
            {
                "date": log.date,
                "sleep_onset": log.sleep_onset.isoformat(),
                "wake_time": log.wake_time.isoformat(),
                "total_sleep_min": log.total_sleep_min,
                "hrv_avg": log.hrv_avg,
                "sleep_score": log.sleep_score,
                "source": log.source,
            }
            for log in logs
        ],
    }
