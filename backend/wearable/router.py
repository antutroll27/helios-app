"""
HELIOS Backend - Wearable Upload Router.

POST /api/wearable/upload accepts export files from supported wearables.
GET  /api/wearable/sources lists supported devices and file formats.
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.auth.supabase_auth import get_current_user_from_session
from backend.wearable.parsers.apple_health import AppleHealthParser
from backend.wearable.parsers.fitbit import FitbitParser
from backend.wearable.parsers.garmin import GarminParser
from backend.wearable.parsers.oura import OuraParser
from backend.wearable.parsers.samsung import SamsungParser
from backend.wearable.parsers.whoop import WhoopParser

logger = logging.getLogger(__name__)
router = APIRouter()

_DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
_APPLE_HEALTH_MAX_UPLOAD_BYTES = 100 * 1024 * 1024
_STREAM_CHUNK_BYTES = 1024 * 1024

# Parser registry: checked in order; first match wins.
# Oura is last because generic .zip files should prefer named-device parsers.
_PARSERS = [
    FitbitParser(),
    WhoopParser(),
    GarminParser(),
    SamsungParser(),
    AppleHealthParser(),
    OuraParser(),
]


def _detect_parser(filename: str):
    """Return the first parser that claims it can handle filename, or None."""
    for parser in _PARSERS:
        if parser.can_handle(filename):
            return parser
    return None


def _max_upload_bytes(parser) -> int:
    explicit = getattr(parser, "max_upload_bytes", None)
    if isinstance(explicit, int) and explicit > 0:
        return explicit
    if getattr(parser, "source_name", None) == "apple_health":
        return _APPLE_HEALTH_MAX_UPLOAD_BYTES
    return _DEFAULT_MAX_UPLOAD_BYTES


def _format_byte_limit(limit: int) -> str:
    if limit < 1024:
        return f"{limit} byte"
    if limit < 1024 * 1024:
        return f"{limit // 1024} KB"
    return f"{limit // (1024 * 1024)} MB"


async def _read_upload_limited(file: UploadFile, max_bytes: int, source_name: str) -> bytes:
    content = bytearray()
    while True:
        chunk = await file.read(_STREAM_CHUNK_BYTES)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds {_format_byte_limit(max_bytes)} limit for {source_name}.",
            )
    return bytes(content)


def _sleep_log_to_row(log, user_id: str) -> dict:
    """Map SleepLog dataclass to sleep_logs table columns."""
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
        "source": log.source or "manual",
    }


def _average(values: list[float | int | None]) -> float | int | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    avg = sum(clean) / len(clean)
    return int(avg) if float(avg).is_integer() else round(avg, 1)


def _import_summary(logs) -> dict:
    return {
        "avg_total_sleep_min": _average([log.total_sleep_min for log in logs]),
        "avg_hrv": _average([log.hrv_avg for log in logs]),
        "avg_sleep_score": _average([log.sleep_score for log in logs]),
    }


@router.post("/upload")
async def upload_wearable(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_from_session),
):
    """
    Accept a wearable sleep export file, parse it, and upsert to sleep_logs.

    Conflict resolution: upsert on (user_id, date). Newer upload wins.
    The response intentionally returns only an import summary, not raw logs.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    filename = file.filename
    parser = _detect_parser(filename.lower())
    if parser is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unrecognised file format: '{filename}'. "
                "Supported: Oura (.zip/.json), Fitbit Takeout (.zip), "
                "Whoop (.csv/.zip), Garmin Connect (.zip), "
                "Samsung Health (.zip), Apple Health (.zip/export.xml)."
            ),
        )

    content = await _read_upload_limited(
        file,
        max_bytes=_max_upload_bytes(parser),
        source_name=parser.source_name,
    )

    supabase = request.app.state.supabase

    try:
        logs = parser.parse(content, filename)
    except NotImplementedError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.warning("[wearable] Parse failed for %s (%s): %s", filename, parser.source_name, e)
        raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")

    if not logs:
        raise HTTPException(
            status_code=422,
            detail=f"No sleep records found in file. Check the export format for {parser.source_name}.",
        )

    try:
        import_result = supabase.table("data_imports").insert(
            {
                "user_id": user_id,
                "filename": filename,
                "platform": parser.source_name,
                "status": "processing",
                "records_imported": 0,
            }
        ).execute()
        import_id = import_result.data[0]["id"]
    except Exception as e:
        logger.error("[wearable] data_imports insert failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to record import.")

    rows = [_sleep_log_to_row(log, user_id) for log in logs]
    try:
        supabase.table("sleep_logs").upsert(
            rows,
            on_conflict="user_id,date",
        ).execute()
    except Exception as e:
        logger.error("[wearable] sleep_logs upsert failed: %s", e)
        supabase.table("data_imports").update(
            {
                "status": "failed",
                "error_message": str(e),
            }
        ).eq("id", import_id).execute()
        raise HTTPException(status_code=500, detail="Failed to save sleep data.")

    supabase.table("data_imports").update(
        {
            "status": "complete",
            "records_imported": len(logs),
        }
    ).eq("id", import_id).execute()

    return {
        "import_id": import_id,
        "source": parser.source_name,
        "records": len(logs),
        "date_range": {
            "from": min(log.date for log in logs),
            "to": max(log.date for log in logs),
        },
        "summary": _import_summary(logs),
    }


@router.get("/sources")
async def get_supported_sources():
    """List all wearable parsers and their implementation status."""
    return {
        "sources": [
            {
                "source": p.source_name,
                "implemented": True,
                "file_formats": _format_hints(p),
            }
            for p in _PARSERS
        ]
    }


def _format_hints(parser) -> list[str]:
    hints = {
        "fitbit": [".zip (Google Takeout)"],
        "whoop": [".csv", ".zip"],
        "garmin": [".zip (Garmin Connect bulk export)"],
        "samsung": [".zip (Samsung Health export)"],
        "apple_health": [".zip (Apple Health export)", "export.xml"],
        "oura": [".zip (Oura export)", "sleep.json"],
    }
    return hints.get(parser.source_name, [".zip"])
