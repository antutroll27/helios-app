"""
HELIOS Backend — Whoop Data Parser
Parses Whoop physiological cycle CSV export into SleepLog entries.

Whoop exports via: App → Profile → Privacy & Security → Request My Data
Produces a ZIP containing physiological_cycles.csv (one row per 24h cycle).

Key columns:
    Cycle start time        — 24h cycle start (local time)
    Cycle end time          — 24h cycle end   (local time)
    Sleep onset             — actual sleep start (may be empty)
    Sleep end               — actual sleep end   (may be empty)
    Asleep duration (min)   — total sleep minutes
    In bed duration (min)   — total in-bed minutes
    Light sleep duration (min)
    Slow wave sleep duration (min)  ← SWS = deep sleep
    REM sleep duration (min)
    Awake duration (min)
    HRV (ms)                — nightly rMSSD
    Resting Heart Rate (bpm)
    Skin temp (celsius)     — absolute skin temperature (Whoop does not export delta)
    Recovery score %        — Whoop recovery score 0–100 (used as sleep_score proxy)

References:
- Dunican 2023 (J Sleep Res): WHOOP 4.0 sleep staging vs PSG, k=0.61 overall
- Whoop API v3.1 docs: https://developer.whoop.com/api
"""

import csv
import io
import zipfile
import sys
import os
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'research'))
from chronotype_engine import SleepLog


def _parse_whoop_ts(ts: str) -> Optional[datetime]:
    """
    Parse Whoop timestamp strings. Whoop uses local time in the export.
    Formats seen: '2023-01-14 23:30:00', '2023-01-14T23:30:00'.
    """
    if not ts or ts.strip() == "":
        return None
    ts = ts.strip().replace("T", " ")
    # Truncate sub-seconds if present
    if "." in ts:
        ts = ts[:ts.index(".")]
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _col(row: dict, *candidates: str) -> Optional[str]:
    """Return first non-empty value for candidate column names (case-insensitive)."""
    for key in row:
        for cand in candidates:
            if key.strip().lower() == cand.lower():
                val = row[key]
                return val.strip() if val and val.strip() else None
    return None


def _int_col(row: dict, *candidates: str) -> Optional[int]:
    v = _col(row, *candidates)
    if v is None:
        return None
    try:
        f = float(v)
        return int(f)
    except (ValueError, TypeError):
        return None


def _float_col(row: dict, *candidates: str) -> Optional[float]:
    v = _col(row, *candidates)
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


class WhoopParser:
    """
    Parses Whoop physiological_cycles.csv export into SleepLog entries.
    Accepts the CSV file directly or a ZIP containing it.
    """

    @property
    def source_name(self) -> str:
        return "whoop"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return "whoop" in lower and (lower.endswith(".csv") or lower.endswith(".zip"))

    def parse(self, data: bytes, filename: str) -> list[SleepLog]:
        lower = filename.lower()
        if lower.endswith(".zip"):
            return self._parse_zip(data)
        if lower.endswith(".csv"):
            return self._parse_csv(data.decode("utf-8-sig", errors="replace"))
        raise ValueError(f"WhoopParser: unsupported extension in '{filename}'.")

    # ─── ZIP ──────────────────────────────────────────────────────────────────

    def _parse_zip(self, data: bytes) -> list[SleepLog]:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            csv_names = [
                n for n in zf.namelist()
                if n.lower().endswith(".csv") and "physiological" in n.lower()
            ]
            # Fall back to any CSV if 'physiological' not found
            if not csv_names:
                csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                raise ValueError("No CSV file found in Whoop ZIP export.")

            text = zf.read(csv_names[0]).decode("utf-8-sig", errors="replace")

        return self._parse_csv(text)

    # ─── CSV ──────────────────────────────────────────────────────────────────

    def _parse_csv(self, text: str) -> list[SleepLog]:
        reader = csv.DictReader(io.StringIO(text))
        logs: list[SleepLog] = []

        for row in reader:
            log = self._row_to_log(row)
            if log is not None:
                logs.append(log)

        logs.sort(key=lambda x: x.date)
        return logs

    def _row_to_log(self, row: dict) -> Optional[SleepLog]:
        # Sleep boundaries — prefer explicit onset/end columns
        onset_str = _col(row, "Sleep onset", "Sleep Onset", "sleep_onset")
        end_str   = _col(row, "Sleep end", "Sleep End", "sleep_end")

        if onset_str:
            sleep_onset = _parse_whoop_ts(onset_str)
        else:
            # Fall back: cycle start time is close enough for sleep start
            sleep_onset = _parse_whoop_ts(
                _col(row, "Cycle start time", "Cycle Start Time", "cycle_start_time") or ""
            )

        if end_str:
            wake_time = _parse_whoop_ts(end_str)
        else:
            wake_time = _parse_whoop_ts(
                _col(row, "Cycle end time", "Cycle End Time", "cycle_end_time") or ""
            )

        if sleep_onset is None or wake_time is None:
            return None

        # Date = the day the user woke up
        date = wake_time.date().isoformat()

        # Duration
        total_min = _int_col(
            row,
            "Asleep duration (min)", "Asleep Duration (min)",
            "asleep_duration_min", "Sleep duration (min)",
        )
        if total_min is None or total_min <= 0:
            return None

        # Stage breakdown
        # "Slow wave sleep" = deep (SWS / NREM 3)
        deep_min = _int_col(
            row,
            "Slow wave sleep duration (min)", "Slow Wave Sleep Duration (min)",
            "slow_wave_sleep_duration_min", "SWS duration (min)",
        )
        rem_min = _int_col(
            row,
            "REM sleep duration (min)", "REM Sleep Duration (min)",
            "rem_sleep_duration_min",
        )

        # HRV — Whoop exports rMSSD nightly average
        hrv = _float_col(row, "HRV (ms)", "HRV", "hrv_ms", "hrv_rmssd")
        rhr = _float_col(
            row,
            "Resting Heart Rate (bpm)", "Resting Heart Rate",
            "resting_heart_rate_bpm", "rhr",
        )

        # Recovery score % → closest analog to sleep_score
        recovery = _float_col(
            row,
            "Recovery score %", "Recovery Score %",
            "recovery_score_pct", "recovery",
        )
        sleep_score = int(recovery) if recovery is not None else None

        # Whoop gives absolute skin temp (not delta vs baseline) — omit
        return SleepLog(
            date=date,
            sleep_onset=sleep_onset,
            wake_time=wake_time,
            total_sleep_min=total_min,
            deep_sleep_min=deep_min,
            rem_sleep_min=rem_min,
            hrv_avg=hrv,
            skin_temp_delta=None,
            resting_hr=rhr,
            sleep_score=sleep_score,
            source="whoop",
        )
