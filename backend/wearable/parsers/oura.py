"""
HELIOS Backend — Oura Ring Data Parser
Parses Oura Ring data export (ZIP of JSON files) into SleepLog entries.

Supports:
- Oura export ZIP (cloud.ouraring.com → Settings → Download My Data)
- Individual sleep.json / daily_sleep.json files
- Oura API v2 response format (same schema as export)

Export structure:
    oura_export/
    ├── sleep.json          → per-period sleep data (main + naps)
    ├── daily_sleep.json    → daily sleep score
    ├── daily_readiness.json → readiness score + temp deviation
    ├── heartrate.json      → 5-min interval HR (large file)
    └── ...

Field mapping (Oura → SleepLog):
    day                         → date
    bedtime_start + latency     → sleep_onset (true sleep onset)
    bedtime_end                 → wake_time
    total_sleep_duration / 60   → total_sleep_min (seconds → minutes)
    deep_sleep_duration / 60    → deep_sleep_min
    rem_sleep_duration / 60     → rem_sleep_min
    average_hrv                 → hrv_avg (rMSSD in ms)
    readiness.temperature_deviation → skin_temp_delta (°C from baseline)
    lowest_heart_rate           → resting_hr
    daily_sleep.score           → sleep_score (joined on day)

References:
- Oura API v2 docs: https://cloud.ouraring.com/v2/docs
- Zambotti et al. (2022, JMIR 24:e35528): Oura HRV accuracy CCC=0.97 vs ECG
"""

import json
import zipfile
import io
from datetime import datetime, timedelta
from typing import Optional
import sys
import os

# Add backend/research/ to path for SleepLog import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'research'))
from chronotype_engine import SleepLog


def _seconds_to_min(seconds: Optional[int]) -> Optional[int]:
    """Convert seconds to minutes, handling None."""
    if seconds is None:
        return None
    return seconds // 60


def _parse_iso_datetime(iso_str: str) -> datetime:
    """Parse ISO 8601 datetime string with timezone offset."""
    return datetime.fromisoformat(iso_str)


# ─── Core Parser ─────────────────────────────────────────────────────────────

class OuraParser:
    """
    Parses Oura Ring export data into HELIOS SleepLog entries.

    Handles three input modes:
    1. ZIP file (bytes) — the standard Oura export download
    2. Directory of JSON files — extracted ZIP
    3. Raw JSON dicts — from Oura API v2 responses

    Usage:
        parser = OuraParser()
        logs = parser.parse_zip(zip_bytes)
        # or
        logs = parser.parse_json(sleep_json, daily_sleep_json)
    """

    def parse(self, file_content: bytes, filename: str) -> list[SleepLog]:
        """
        Auto-detect format and parse.
        Implements the WearableParser protocol.
        """
        if filename.endswith('.zip'):
            return self.parse_zip(file_content)
        elif filename.endswith('.json'):
            data = json.loads(file_content)
            # Detect if it's a sleep.json file
            if isinstance(data, dict) and "data" in data:
                records = data["data"]
                if records and "bedtime_start" in records[0]:
                    return self.parse_sleep_records(records)
            return []
        else:
            return []

    def parse_zip(self, zip_bytes: bytes) -> list[SleepLog]:
        """
        Parse a complete Oura export ZIP file.

        The ZIP contains sleep.json, daily_sleep.json, and other files.
        We extract sleep data and join with daily_sleep for the score.
        """
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()

            # Find sleep.json (may be in a subdirectory)
            sleep_file = self._find_file(names, "sleep.json")
            daily_sleep_file = self._find_file(names, "daily_sleep.json")

            if not sleep_file:
                return []

            sleep_data = json.loads(zf.read(sleep_file))

            daily_sleep_data = None
            if daily_sleep_file:
                daily_sleep_data = json.loads(zf.read(daily_sleep_file))

        sleep_records = sleep_data.get("data", [])
        daily_records = daily_sleep_data.get("data", []) if daily_sleep_data else []

        return self._convert_records(sleep_records, daily_records)

    def parse_json(
        self,
        sleep_json: dict,
        daily_sleep_json: Optional[dict] = None,
    ) -> list[SleepLog]:
        """
        Parse Oura API v2 JSON responses directly.
        Same schema as the export files.
        """
        sleep_records = sleep_json.get("data", [])
        daily_records = daily_sleep_json.get("data", []) if daily_sleep_json else []
        return self._convert_records(sleep_records, daily_records)

    def parse_sleep_records(self, records: list[dict]) -> list[SleepLog]:
        """Parse a list of sleep record dicts (from sleep.json data array)."""
        return self._convert_records(records, [])

    # ─── Internal ────────────────────────────────────────────────────────────

    def _convert_records(
        self,
        sleep_records: list[dict],
        daily_records: list[dict],
    ) -> list[SleepLog]:
        """Convert Oura records to SleepLog entries."""

        # Build sleep score lookup: day -> score
        score_map: dict[str, int] = {}
        for rec in daily_records:
            day = rec.get("day", "")
            score = rec.get("score")
            if day and score is not None:
                score_map[day] = score

        logs: list[SleepLog] = []

        for rec in sleep_records:
            log = self._record_to_sleep_log(rec, score_map)
            if log is not None:
                logs.append(log)

        # Sort by date
        logs.sort(key=lambda x: x.date)
        return logs

    def _record_to_sleep_log(
        self,
        rec: dict,
        score_map: dict[str, int],
    ) -> Optional[SleepLog]:
        """Convert a single Oura sleep record to a SleepLog."""

        # Filter: only main sleep periods, not naps or rest
        sleep_type = rec.get("type", "")
        if sleep_type not in ("long_sleep", "sleep", ""):
            return None

        # Required fields
        day = rec.get("day")
        bedtime_start_str = rec.get("bedtime_start")
        bedtime_end_str = rec.get("bedtime_end")
        total_duration = rec.get("total_sleep_duration")

        if not all([day, bedtime_start_str, bedtime_end_str, total_duration]):
            return None

        # Parse timestamps
        try:
            bedtime_start = _parse_iso_datetime(bedtime_start_str)
            bedtime_end = _parse_iso_datetime(bedtime_end_str)
        except (ValueError, TypeError):
            return None

        # True sleep onset = bedtime_start + latency
        latency_sec = rec.get("latency") or 0
        sleep_onset = bedtime_start + timedelta(seconds=latency_sec)

        # Temperature deviation (nested under readiness, may be None)
        skin_temp_delta = None
        readiness = rec.get("readiness")
        if isinstance(readiness, dict):
            skin_temp_delta = readiness.get("temperature_deviation")

        # Sleep score from daily_sleep join
        sleep_score = score_map.get(day)

        return SleepLog(
            date=day,
            sleep_onset=sleep_onset,
            wake_time=bedtime_end,
            total_sleep_min=total_duration // 60,
            deep_sleep_min=_seconds_to_min(rec.get("deep_sleep_duration")),
            rem_sleep_min=_seconds_to_min(rec.get("rem_sleep_duration")),
            hrv_avg=rec.get("average_hrv"),
            skin_temp_delta=skin_temp_delta,
            resting_hr=rec.get("lowest_heart_rate"),
            sleep_score=sleep_score,
            source="oura",
        )

    @staticmethod
    def _find_file(names: list[str], target: str) -> Optional[str]:
        """Find a file in a ZIP, handling subdirectories."""
        for name in names:
            if name.endswith(target) or name.endswith(f"/{target}"):
                return name
        return None


# ─── Biometric Extraction (beyond SleepLog) ──────────────────────────────────

class OuraBiometricParser:
    """
    Extracts additional biometric data from Oura exports
    that goes beyond the SleepLog dataclass.

    Returns structured dicts for storage in biometric_logs table.
    """

    @staticmethod
    def parse_heartrate(hr_json: dict) -> list[dict]:
        """
        Parse heartrate.json into timestamped HR readings.
        Each record: {bpm, source, timestamp}
        """
        records = hr_json.get("data", [])
        return [
            {
                "timestamp": rec["timestamp"],
                "metric": "hr",
                "value": rec["bpm"],
                "source": "oura",
            }
            for rec in records
            if "bpm" in rec and "timestamp" in rec
        ]

    @staticmethod
    def parse_hrv_timeseries(sleep_record: dict) -> list[dict]:
        """
        Extract 5-min interval HRV time series from a sleep record.
        The hrv field contains {interval, items[], timestamp}.
        """
        hrv_data = sleep_record.get("hrv")
        if not hrv_data or not hrv_data.get("items"):
            return []

        interval_sec = hrv_data.get("interval", 300)  # 5 min default
        start = _parse_iso_datetime(hrv_data["timestamp"])
        entries = []

        for i, value in enumerate(hrv_data["items"]):
            if value is not None:
                ts = start + timedelta(seconds=i * interval_sec)
                entries.append({
                    "timestamp": ts.isoformat(),
                    "metric": "hrv_rmssd",
                    "value": float(value),
                    "source": "oura",
                })

        return entries

    @staticmethod
    def parse_spo2(spo2_json: dict) -> list[dict]:
        """Parse daily_spo2.json into SpO2 readings."""
        records = spo2_json.get("data", [])
        entries = []
        for rec in records:
            spo2 = rec.get("spo2_percentage", {})
            avg = spo2.get("average")
            if avg is not None:
                entries.append({
                    "timestamp": rec.get("day", "") + "T00:00:00",
                    "metric": "spo2",
                    "value": avg,
                    "source": "oura",
                })
        return entries


# ─── Example Usage ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = OuraParser()

    # Simulate an Oura export with sample data
    sample_sleep = {
        "data": [
            {
                "id": "abc-123",
                "day": "2026-04-05",
                "bedtime_start": "2026-04-04T23:30:00+07:00",
                "bedtime_end": "2026-04-05T07:15:00+07:00",
                "total_sleep_duration": 25200,  # 7h in seconds
                "deep_sleep_duration": 5400,     # 1.5h
                "rem_sleep_duration": 6300,       # 1.75h
                "light_sleep_duration": 13500,    # 3.75h
                "awake_time": 2700,               # 45 min
                "latency": 720,                   # 12 min to fall asleep
                "average_heart_rate": 54,
                "lowest_heart_rate": 48,
                "average_hrv": 42,
                "average_breath": 15.5,
                "efficiency": 88,
                "type": "long_sleep",
                "readiness": {
                    "score": 83,
                    "temperature_deviation": -0.14,
                    "temperature_trend_deviation": 0.02,
                },
                "hrv": {
                    "interval": 300,
                    "items": [35, 38, 42, 48, 45, 40, 38, 35],
                    "timestamp": "2026-04-04T23:30:00+07:00",
                },
            },
            {
                "id": "def-456",
                "day": "2026-04-06",
                "bedtime_start": "2026-04-06T01:15:00+07:00",
                "bedtime_end": "2026-04-06T09:30:00+07:00",
                "total_sleep_duration": 27000,  # 7.5h
                "deep_sleep_duration": 4800,     # 1.33h
                "rem_sleep_duration": 7200,       # 2h
                "light_sleep_duration": 15000,
                "awake_time": 2400,
                "latency": 900,                   # 15 min
                "average_heart_rate": 56,
                "lowest_heart_rate": 50,
                "average_hrv": 38,
                "average_breath": 16.0,
                "efficiency": 85,
                "type": "long_sleep",
                "readiness": {
                    "score": 76,
                    "temperature_deviation": 0.21,
                    "temperature_trend_deviation": 0.05,
                },
                "hrv": None,
            },
            {
                "id": "ghi-789",
                "day": "2026-04-06",
                "bedtime_start": "2026-04-06T14:00:00+07:00",
                "bedtime_end": "2026-04-06T14:30:00+07:00",
                "total_sleep_duration": 1500,    # 25 min nap
                "deep_sleep_duration": 0,
                "rem_sleep_duration": 0,
                "light_sleep_duration": 1500,
                "awake_time": 300,
                "latency": 300,
                "average_heart_rate": 60,
                "lowest_heart_rate": 55,
                "average_hrv": 35,
                "average_breath": 14.0,
                "efficiency": 75,
                "type": "rest",  # This should be filtered out
                "readiness": None,
                "hrv": None,
            },
        ]
    }

    sample_daily_sleep = {
        "data": [
            {"day": "2026-04-05", "score": 85},
            {"day": "2026-04-06", "score": 72},
        ]
    }

    print("=" * 60)
    print("HELIOS Oura Parser — Sample Data Test")
    print("=" * 60)

    # Parse sleep records
    logs = parser.parse_json(sample_sleep, sample_daily_sleep)

    print(f"\nParsed {len(logs)} sleep logs (naps filtered out):\n")

    for log in logs:
        print(f"  Date: {log.date}")
        print(f"  Sleep onset: {log.sleep_onset.strftime('%H:%M')} (bedtime + latency)")
        print(f"  Wake time: {log.wake_time.strftime('%H:%M')}")
        print(f"  Total sleep: {log.total_sleep_min} min ({log.total_sleep_min / 60:.1f}h)")
        print(f"  Deep: {log.deep_sleep_min} min | REM: {log.rem_sleep_min} min")
        print(f"  HRV (rMSSD): {log.hrv_avg} ms")
        print(f"  Resting HR: {log.resting_hr} bpm")
        print(f"  Skin temp delta: {log.skin_temp_delta}°C")
        print(f"  Sleep score: {log.sleep_score}")
        print(f"  Source: {log.source}")
        print()

    # Test biometric extraction
    bio_parser = OuraBiometricParser()
    hrv_series = bio_parser.parse_hrv_timeseries(sample_sleep["data"][0])
    print(f"HRV time series extracted: {len(hrv_series)} readings (5-min intervals)")
    if hrv_series:
        print(f"  First: {hrv_series[0]['value']} ms at {hrv_series[0]['timestamp']}")
        print(f"  Last:  {hrv_series[-1]['value']} ms at {hrv_series[-1]['timestamp']}")

    # Verify nap was filtered
    print(f"\nNap record filtered: {'ghi-789' not in [l.date + l.source for l in logs]}")
    print(f"Only main sleep periods included: {len(logs)} of {len(sample_sleep['data'])} records")
