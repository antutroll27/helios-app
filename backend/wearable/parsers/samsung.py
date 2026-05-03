"""
HELIOS Backend — Samsung Health Parser
Parses Samsung Health export ZIP into SleepLog entries.

Samsung Health export via: app → Profile → Data → Export as file
Produces a ZIP with a timestamped folder containing CSV files.

Key files inside the ZIP:
    com.samsung.shealth.sleep.*.csv          ← daily sleep summary (one row/night)
    com.samsung.shealth.tracker.sleep_stage.*.csv  ← per-stage intervals (optional)

Sleep summary columns (prefixed with 'com.samsung.health.sleep.'):
    start_time       — "YYYY-MM-DD HH:MM:SS.mmm" local
    end_time         — "YYYY-MM-DD HH:MM:SS.mmm" local
    quality          — sleep quality score 0–100
    total_elapsed_time — total time in bed (ms)
    factor_deep      — proportion of total sleep in deep (0–1)
    factor_rem       — proportion in REM (0–1)
    factor_light     — proportion in light (0–1)
    factor_awake     — proportion awake (0–1)

Sleep stage columns (prefixed with 'com.samsung.health.sleep_stage.'):
    start_time, end_time, stage
    Stage codes: 40101=awake, 40102=light, 40103=deep, 40104=REM

Samsung does not export HRV or resting HR in the standard sleep CSV; those
require the biometric_logs or stress tables (not parsed here).

References:
- Lee 2021 (Sensors): Galaxy Watch3 PSG comparison, SE=0.79 for stages
- Samsung Health Open API docs: developer.samsung.com/health
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


# Samsung stage code → name
_STAGE_CODES = {
    "40101": "awake",
    "40102": "light",
    "40103": "deep",
    "40104": "rem",
}

# Column prefix strip
_SLEEP_PFX  = "com.samsung.health.sleep."
_STAGE_PFX  = "com.samsung.health.sleep_stage."


def _strip_prefix(key: str) -> str:
    """Remove Samsung column prefix, return bare name."""
    for pfx in (_SLEEP_PFX, _STAGE_PFX):
        if key.startswith(pfx):
            return key[len(pfx):]
    return key


def _parse_samsung_ts(ts: str) -> Optional[datetime]:
    """Parse Samsung timestamp: '2023-01-14 23:30:00.000'."""
    if not ts or ts.strip() == "":
        return None
    ts = ts.strip()
    if "." in ts:
        ts = ts[:ts.rfind(".")]
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _normalise_row(row: dict) -> dict:
    """Strip Samsung column prefixes so callers use bare names."""
    return {_strip_prefix(k): v for k, v in row.items()}


class SamsungParser:
    """
    Parses Samsung Health export ZIP into SleepLog entries.
    Prefers stage-level CSV for accuracy; falls back to summary factors.
    """

    @property
    def source_name(self) -> str:
        return "samsung"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return "samsung" in lower or "shealth" in lower

    def parse(self, data: bytes, filename: str) -> list[SleepLog]:
        if filename.lower().endswith(".zip"):
            return self._parse_zip(data)
        raise ValueError(f"SamsungParser: expected a .zip export, got '{filename}'.")

    # ─── ZIP ──────────────────────────────────────────────────────────────────

    def _parse_zip(self, data: bytes) -> list[SleepLog]:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()

            sleep_csv  = self._find_csv(names, "shealth.sleep.")
            stage_csv  = self._find_csv(names, "sleep_stage.")

            if not sleep_csv:
                raise ValueError("Samsung export: com.samsung.shealth.sleep.*.csv not found.")

            sleep_text = zf.read(sleep_csv).decode("utf-8-sig", errors="replace")
            stage_text = zf.read(stage_csv).decode("utf-8-sig", errors="replace") if stage_csv else None

        return self._build_logs(sleep_text, stage_text)

    # ─── Build ────────────────────────────────────────────────────────────────

    def _build_logs(
        self,
        sleep_text: str,
        stage_text: Optional[str],
    ) -> list[SleepLog]:

        # Parse stage intervals → sleep_id → {deep, rem, light, awake} mins
        stage_by_sleep_id: dict[str, dict[str, int]] = {}
        if stage_text:
            for row in csv.DictReader(io.StringIO(stage_text)):
                r = _normalise_row(row)
                sid = r.get("sleep_id", "").strip()
                code = str(r.get("stage", "")).strip()
                stage = _STAGE_CODES.get(code)
                if not sid or not stage or stage == "awake":
                    continue
                start = _parse_samsung_ts(r.get("start_time", ""))
                end   = _parse_samsung_ts(r.get("end_time", ""))
                if start and end and end > start:
                    dur = int((end - start).total_seconds() / 60)
                    bucket = stage_by_sleep_id.setdefault(sid, {"deep": 0, "rem": 0, "light": 0})
                    bucket[stage] = bucket.get(stage, 0) + dur

        # Parse sleep summary
        logs: list[SleepLog] = []

        # Samsung CSVs sometimes have a comment line at the top starting with '#'
        lines = [l for l in sleep_text.splitlines() if not l.startswith("#")]
        clean_text = "\n".join(lines)

        for row in csv.DictReader(io.StringIO(clean_text)):
            r = _normalise_row(row)
            log = self._row_to_log(r, stage_by_sleep_id)
            if log is not None:
                logs.append(log)

        logs.sort(key=lambda x: x.date)
        return logs

    def _row_to_log(
        self,
        r: dict,
        stage_by_id: dict,
    ) -> Optional[SleepLog]:
        start = _parse_samsung_ts(r.get("start_time", ""))
        end   = _parse_samsung_ts(r.get("end_time", ""))

        if start is None or end is None or end <= start:
            return None

        date = end.date().isoformat()

        # Total sleep from elapsed time (ms) or compute from timestamps
        elapsed_ms = r.get("total_elapsed_time") or r.get("duration")
        if elapsed_ms:
            try:
                total_min = int(float(elapsed_ms)) // 60000
            except (ValueError, TypeError):
                total_min = int((end - start).total_seconds() / 60)
        else:
            total_min = int((end - start).total_seconds() / 60)

        if total_min < 60:
            return None

        # Stage breakdown: prefer detail CSV, fall back to factor columns
        sleep_id = r.get("combined_id", "").strip()
        stages = stage_by_id.get(sleep_id)

        if stages:
            deep_min  = stages.get("deep")  or None
            rem_min   = stages.get("rem")   or None
        else:
            # Use factor_* columns as proportions of total_elapsed_time
            def _factor(name: str) -> Optional[int]:
                v = r.get(name)
                if v is None or v.strip() == "":
                    return None
                try:
                    return int(float(v) * total_min)
                except (ValueError, TypeError):
                    return None

            deep_min = _factor("factor_deep")
            rem_min  = _factor("factor_rem")

        # Quality score 0–100
        quality = r.get("quality")
        sleep_score: Optional[int] = None
        if quality and quality.strip():
            try:
                sleep_score = int(float(quality))
            except (ValueError, TypeError):
                pass

        return SleepLog(
            date=date,
            sleep_onset=start,
            wake_time=end,
            total_sleep_min=total_min,
            deep_sleep_min=deep_min,
            rem_sleep_min=rem_min,
            hrv_avg=None,           # not in standard Samsung sleep CSV
            skin_temp_delta=None,
            resting_hr=None,
            sleep_score=sleep_score,
            source="samsung",
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _find_csv(names: list[str], pattern: str) -> Optional[str]:
        """Return the first ZIP entry whose basename contains pattern."""
        for name in names:
            base = name.split("/")[-1].lower()
            if pattern in base and base.endswith(".csv"):
                return name
        return None
