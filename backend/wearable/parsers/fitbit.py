"""
HELIOS Backend — Fitbit Data Parser
Parses Google Takeout Fitbit export ZIP into SleepLog entries.

Google Takeout ZIP structure:
    Takeout/
    └── Fitbit/
        └── Global Export Data/
            ├── sleep-YYYY-MM-DD.json   ← one file per date range (array of sessions)
            └── hrv-YYYY-MM-DD.json     ← rMSSD per day (optional)

sleep-*.json record format:
    {
        "dateOfSleep": "2023-01-15",
        "startTime": "2023-01-14T23:30:00",
        "endTime": "2023-01-15T07:15:00",
        "minutesToFallAsleep": 12,
        "minutesAsleep": 432,
        "minutesAwake": 23,
        "timeInBed": 465,
        "efficiency": 93,
        "isMainSleep": true,
        "type": "stages",
        "levels": {
            "summary": {
                "deep":  {"minutes": 92},
                "light": {"minutes": 195},
                "rem":   {"minutes": 98},
                "wake":  {"minutes": 23}
            }
        }
    }

hrv-*.json format:
    {"hrv": [{"dateTime": "2023-01-15", "value": {"rmssd": 42.3}}]}

References:
- Fitbit Web API v1.2 docs: https://dev.fitbit.com/build/reference/web-api/sleep/
- Kubota 2021 (J Sleep Res): Fitbit Charge 4 PSG CCC for sleep stages r=0.83–0.91
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


def _parse_fitbit_ts(ts: str) -> datetime:
    """Parse Fitbit local-time string: 2023-01-14T23:30:00 or 2023-01-14 23:30:00."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognised Fitbit timestamp: {ts!r}")


class FitbitParser:
    """
    Parses Fitbit data from a Google Takeout ZIP.

    Handles:
    - Google Takeout Fitbit ZIP (Takeout/Fitbit/Global Export Data/*.json)
    - Direct sleep-*.json or hrv-*.json files
    """

    @property
    def source_name(self) -> str:
        return "fitbit"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return "fitbit" in lower or ("takeout" in lower and lower.endswith(".zip"))

    def parse(self, data: bytes, filename: str) -> list[SleepLog]:
        lower = filename.lower()
        if lower.endswith(".zip"):
            return self._parse_zip(data)
        if lower.endswith(".json"):
            return self._parse_sleep_file(json.loads(data))
        raise ValueError(f"FitbitParser: unsupported file extension in '{filename}'.")

    # ─── ZIP ──────────────────────────────────────────────────────────────────

    def _parse_zip(self, data: bytes) -> list[SleepLog]:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()

            # Collect all sleep-*.json and hrv-*.json entries
            sleep_files = [n for n in names if self._is_sleep_file(n)]
            hrv_files   = [n for n in names if self._is_hrv_file(n)]

            # Aggregate HRV: date → rMSSD
            hrv_map: dict[str, float] = {}
            for hf in hrv_files:
                try:
                    raw = json.loads(zf.read(hf))
                    for entry in raw.get("hrv", []):
                        dt = entry.get("dateTime", "")
                        val = entry.get("value", {}).get("rmssd")
                        if dt and val is not None:
                            hrv_map[dt[:10]] = float(val)
                except Exception:
                    continue

            # Aggregate all sleep sessions
            all_sessions: list[dict] = []
            for sf in sleep_files:
                try:
                    raw = json.loads(zf.read(sf))
                    if isinstance(raw, list):
                        all_sessions.extend(raw)
                    elif isinstance(raw, dict) and "sleep" in raw:
                        all_sessions.extend(raw["sleep"])
                except Exception:
                    continue

        return self._sessions_to_logs(all_sessions, hrv_map)

    # ─── Single file ──────────────────────────────────────────────────────────

    def _parse_sleep_file(self, raw) -> list[SleepLog]:
        if isinstance(raw, list):
            sessions = raw
        elif isinstance(raw, dict) and "sleep" in raw:
            sessions = raw["sleep"]
        else:
            return []
        return self._sessions_to_logs(sessions, {})

    # ─── Conversion ───────────────────────────────────────────────────────────

    def _sessions_to_logs(
        self,
        sessions: list[dict],
        hrv_map: dict[str, float],
    ) -> list[SleepLog]:
        logs: list[SleepLog] = []

        # De-duplicate on dateOfSleep — keep main sleep per date
        best: dict[str, dict] = {}
        for s in sessions:
            date = s.get("dateOfSleep", "")
            if not date:
                continue
            is_main = s.get("isMainSleep", False)
            minutes_asleep = s.get("minutesAsleep", 0)
            # Prefer isMainSleep=true; break ties by longer sleep
            prev = best.get(date)
            if prev is None:
                best[date] = s
            elif is_main and not prev.get("isMainSleep", False):
                best[date] = s
            elif is_main == prev.get("isMainSleep", False) and minutes_asleep > prev.get("minutesAsleep", 0):
                best[date] = s

        for date, s in best.items():
            log = self._session_to_log(date, s, hrv_map.get(date))
            if log is not None:
                logs.append(log)

        logs.sort(key=lambda x: x.date)
        return logs

    def _session_to_log(
        self,
        date: str,
        s: dict,
        hrv_rmssd: Optional[float],
    ) -> Optional[SleepLog]:
        start_str = s.get("startTime")
        end_str   = s.get("endTime")
        minutes_asleep = s.get("minutesAsleep")

        if not all([start_str, end_str, minutes_asleep]):
            return None

        try:
            sleep_onset = _parse_fitbit_ts(start_str)
            # Apply sleep latency so onset = actual sleep (not in-bed)
            latency = s.get("minutesToFallAsleep", 0) or 0
            from datetime import timedelta
            sleep_onset = sleep_onset + timedelta(minutes=latency)
            wake_time = _parse_fitbit_ts(end_str)
        except ValueError:
            return None

        # Stage breakdown (only if type == "stages")
        levels = s.get("levels", {}).get("summary", {})
        deep_min  = levels.get("deep",  {}).get("minutes") if levels else None
        rem_min   = levels.get("rem",   {}).get("minutes") if levels else None

        # Fitbit efficiency (0-100) maps well to sleep score
        sleep_score = s.get("efficiency")
        if sleep_score is not None:
            sleep_score = int(sleep_score)

        return SleepLog(
            date=date,
            sleep_onset=sleep_onset,
            wake_time=wake_time,
            total_sleep_min=int(minutes_asleep),
            deep_sleep_min=int(deep_min) if deep_min is not None else None,
            rem_sleep_min=int(rem_min)   if rem_min  is not None else None,
            hrv_avg=hrv_rmssd,
            skin_temp_delta=None,   # not in standard Fitbit export
            resting_hr=None,        # Fitbit REST API only; not in Takeout sleep files
            sleep_score=sleep_score,
            source="fitbit",
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _is_sleep_file(name: str) -> bool:
        lower = name.lower()
        base = lower.split("/")[-1]
        return base.startswith("sleep-") and base.endswith(".json")

    @staticmethod
    def _is_hrv_file(name: str) -> bool:
        lower = name.lower()
        base = lower.split("/")[-1]
        return base.startswith("hrv-") and base.endswith(".json")
