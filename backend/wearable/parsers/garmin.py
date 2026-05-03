"""
HELIOS Backend — Garmin Connect Parser
Parses Garmin Connect bulk data export (JSON) into SleepLog entries.

Garmin Connect export via: Garmin Connect web → top-right avatar →
    Account Settings → Data Management → Export Your Data → Download zip.

ZIP structure:
    DI_CONNECT/
    └── DI-Connect-Wellness_YYYY-MM-DD_YYYY-MM-DD/
        └── wellnessSleepFile_XXXXXXXXXX.json

Each wellness sleep file is a JSON array of daily sleep records.

Garmin JSON record format (two common schema variants handled here):

  Variant A — modern Connect export:
    {
      "calendarDate": "2023-01-15",
      "startLocal": "2023-01-14 23:30:00",
      "endLocal":   "2023-01-15 07:15:00",
      "sleepTimeSeconds":  23400,
      "deepSleepSeconds":  4200,
      "lightSleepSeconds": 14400,
      "remSleepSeconds":   4800,
      "awakeSleepSeconds": 1800,
      "averageHRV": 42,
      "averageRespiration": 15.5,
      "overallSleepScore": {"value": 78}
    }

  Variant B — older export / GarminDB format:
    {
      "calendarDate": "2023-01-15",
      "sleepStartTimestampLocal": 1673804400,   ← UNIX seconds
      "sleepEndTimestampLocal":   1673834200,
      "sleepTimeSeconds": 23400,
      "deepSleepSeconds": 4200,
      "lightSleepSeconds": 14400,
      "remSleepSeconds":  4800,
      "awakeSleepSeconds": 1800,
      "averageHRV": 42,
      "sleepScoreValue": 78
    }

FIT binary files are NOT parsed here (requires the optional fitparse library).
If a user uploads a .fit file a clear error is returned.

References:
- de Zambotti 2019 (Sleep Med Clin): Garmin HRV validation vs ECG
- Garmin Health SDK: developer.garmin.com/health-sdk/overview/
"""

import io
import json
import zipfile
import sys
import os
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'research'))
from chronotype_engine import SleepLog


def _parse_garmin_ts(ts: str) -> Optional[datetime]:
    """Parse Garmin local-time string: '2023-01-14 23:30:00' or '2023-01-14T23:30:00'."""
    if not ts or ts.strip() == "":
        return None
    ts = ts.strip().replace("T", " ")
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _unix_to_dt(unix_sec: Optional[int]) -> Optional[datetime]:
    """Convert UNIX seconds to naive datetime (local, as Garmin exports local timestamps)."""
    if unix_sec is None:
        return None
    try:
        return datetime.fromtimestamp(int(unix_sec))
    except (ValueError, OSError, OverflowError):
        return None


class GarminParser:
    """
    Parses Garmin Connect bulk export ZIP (wellness sleep JSON files) into SleepLog entries.
    """

    @property
    def source_name(self) -> str:
        return "garmin"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        # .fit files cannot be parsed without fitparse — reject with helpful error
        if lower.endswith(".fit"):
            return True   # accept so we can give a clear error message
        return "garmin" in lower and lower.endswith(".zip")

    def parse(self, data: bytes, filename: str) -> list[SleepLog]:
        lower = filename.lower()
        if lower.endswith(".fit"):
            raise NotImplementedError(
                "Garmin FIT binary files require the 'fitparse' library which is not "
                "installed. Export your data from Garmin Connect web (Account Settings → "
                "Data Management → Export Your Data) and upload the ZIP file instead."
            )
        if lower.endswith(".zip"):
            return self._parse_zip(data)
        raise ValueError(f"GarminParser: expected a .zip export, got '{filename}'.")

    # ─── ZIP ──────────────────────────────────────────────────────────────────

    def _parse_zip(self, data: bytes) -> list[SleepLog]:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            sleep_files = [
                n for n in zf.namelist()
                if "wellnesssleepfile" in n.lower() and n.lower().endswith(".json")
            ]
            # Fall back: any JSON whose name contains "sleep"
            if not sleep_files:
                sleep_files = [
                    n for n in zf.namelist()
                    if "sleep" in n.lower() and n.lower().endswith(".json")
                ]
            if not sleep_files:
                raise ValueError(
                    "Garmin export: no wellnessSleepFile_*.json found. "
                    "Download the full Connect export (not just activity files)."
                )

            records: list[dict] = []
            for sf in sleep_files:
                try:
                    raw = json.loads(zf.read(sf))
                    if isinstance(raw, list):
                        records.extend(raw)
                    elif isinstance(raw, dict):
                        records.append(raw)
                except Exception:
                    continue

        return self._records_to_logs(records)

    # ─── Conversion ───────────────────────────────────────────────────────────

    def _records_to_logs(self, records: list[dict]) -> list[SleepLog]:
        logs: list[SleepLog] = []

        for rec in records:
            log = self._record_to_log(rec)
            if log is not None:
                logs.append(log)

        logs.sort(key=lambda x: x.date)
        return logs

    def _record_to_log(self, rec: dict) -> Optional[SleepLog]:
        date = rec.get("calendarDate")
        if not date:
            return None

        # ── Sleep window (try both variants) ──────────────────────────────────
        sleep_onset = _parse_garmin_ts(rec.get("startLocal", ""))
        wake_time   = _parse_garmin_ts(rec.get("endLocal", ""))

        if sleep_onset is None:
            sleep_onset = _unix_to_dt(rec.get("sleepStartTimestampLocal"))
        if wake_time is None:
            wake_time = _unix_to_dt(rec.get("sleepEndTimestampLocal"))

        if sleep_onset is None or wake_time is None or wake_time <= sleep_onset:
            return None

        # ── Duration fields (stored in seconds) ───────────────────────────────
        def _sec_to_min(key: str) -> Optional[int]:
            v = rec.get(key)
            if v is None:
                return None
            try:
                return int(v) // 60
            except (TypeError, ValueError):
                return None

        total_min = _sec_to_min("sleepTimeSeconds")
        if total_min is None or total_min < 60:
            return None

        deep_min  = _sec_to_min("deepSleepSeconds")
        rem_min   = _sec_to_min("remSleepSeconds")

        # ── Sleep score ───────────────────────────────────────────────────────
        # Variant A: overallSleepScore.value
        # Variant B: sleepScoreValue (int)
        sleep_score: Optional[int] = None
        score_obj = rec.get("overallSleepScore")
        if isinstance(score_obj, dict):
            v = score_obj.get("value")
            if v is not None:
                try:
                    sleep_score = int(v)
                except (TypeError, ValueError):
                    pass
        if sleep_score is None:
            v = rec.get("sleepScoreValue")
            if v is not None:
                try:
                    sleep_score = int(v)
                except (TypeError, ValueError):
                    pass

        # ── HRV ──────────────────────────────────────────────────────────────
        hrv: Optional[float] = None
        v = rec.get("averageHRV")
        if v is not None:
            try:
                hrv = float(v)
            except (TypeError, ValueError):
                pass

        # ── Resting HR ───────────────────────────────────────────────────────
        rhr: Optional[float] = None
        for key in ("restingHeartRate", "averageHR", "lowestHeartRate"):
            if key in rec:
                try:
                    rhr = float(rec[key])
                    break
                except (TypeError, ValueError):
                    continue

        return SleepLog(
            date=date,
            sleep_onset=sleep_onset,
            wake_time=wake_time,
            total_sleep_min=total_min,
            deep_sleep_min=deep_min,
            rem_sleep_min=rem_min,
            hrv_avg=hrv,
            skin_temp_delta=None,   # not in Connect export
            resting_hr=rhr,
            sleep_score=sleep_score,
            source="garmin",
        )
