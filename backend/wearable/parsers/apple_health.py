"""
HELIOS Backend — Apple Health Parser
Parses Apple HealthKit XML export into SleepLog entries.

Apple Health exports via: Health app → profile photo → Export All Health Data
Produces a ZIP containing apple_health_export/export.xml.

Large files (1 GB+) are handled with streaming iterparse.

Sleep record types parsed:
    HKCategoryValueSleepAnalysisInBed       — in-bed window (used for date grouping)
    HKCategoryValueSleepAnalysisAsleep      — legacy "asleep" (iOS <16)
    HKCategoryValueSleepAnalysisAsleepCore  — light/core sleep (iOS 16+)
    HKCategoryValueSleepAnalysisAsleepREM   — REM sleep (iOS 16+)
    HKCategoryValueSleepAnalysisAsleepDeep  — deep sleep (iOS 16+)
    HKCategoryValueSleepAnalysisAwake       — awake periods during sleep (iOS 16+)

HRV: HKQuantityTypeIdentifierHeartRateVariabilitySDNN
     Apple Watch measures SDNN; SDNN ≈ rMSSD for normal sinus rhythm.
     Stored as hrv_avg with source=apple_health.

Resting HR: HKQuantityTypeIdentifierRestingHeartRate (daily value, bpm).

References:
- Apple HealthKit reference: developer.apple.com/documentation/healthkit
- Chinoy 2021 (npj Digit Med): Apple Watch sleep staging accuracy 78% vs PSG
- Shaffer 2017 (Front Public Health): SDNN ↔ rMSSD equivalence at rest
"""

import io
import zipfile
import sys
import os
from datetime import datetime, timedelta
from typing import Optional
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'research'))
from chronotype_engine import SleepLog


# ─── HK Type Constants ────────────────────────────────────────────────────────

_SLEEP_TYPE   = "HKCategoryTypeIdentifierSleepAnalysis"
_HRV_TYPE     = "HKQuantityTypeIdentifierHeartRateVariabilitySDNN"
_RHR_TYPE     = "HKQuantityTypeIdentifierRestingHeartRate"
_SKIN_TEMP    = "HKQuantityTypeIdentifierAppleSkinTemperatureVariation"  # Watch Ultra/Series 8+

# Sleep value → stage label
_SLEEP_VALUES = {
    "HKCategoryValueSleepAnalysisInBed":      "inbed",
    "HKCategoryValueSleepAnalysisAsleep":     "asleep",    # legacy
    "HKCategoryValueSleepAnalysisAsleepCore": "light",
    "HKCategoryValueSleepAnalysisAsleepREM":  "rem",
    "HKCategoryValueSleepAnalysisAsleepDeep": "deep",
    "HKCategoryValueSleepAnalysisAwake":      "awake",
}

# Prefer Apple Watch over iPhone data (Watch has sensors; Phone infers from motion)
_SOURCE_PRIORITY = {"apple watch": 3, "iphone": 2, "clock": 1}


def _source_priority(name: str) -> int:
    n = name.lower()
    for key, pri in _SOURCE_PRIORITY.items():
        if key in n:
            return pri
    return 0


def _parse_apple_ts(ts: str) -> Optional[datetime]:
    """Parse Apple Health datetime: '2023-01-14 23:30:00 +0700'."""
    if not ts:
        return None
    # Strip timezone offset — Apple exports in local time + offset; we keep local
    ts = ts.strip()
    if " +" in ts:
        ts = ts[:ts.rfind(" +")]
    elif " -" in ts[10:]:
        idx = ts[10:].rfind(" -") + 10
        ts = ts[:idx]
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _duration_min(start: datetime, end: datetime) -> int:
    delta = end - start
    if delta.total_seconds() < 0:
        return 0
    return int(delta.total_seconds() / 60)


class AppleHealthParser:
    """
    Parses Apple Health export.xml (via streaming iterparse) into SleepLog entries.
    Accepts the ZIP or the raw XML file.
    """

    @property
    def source_name(self) -> str:
        return "apple_health"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return "apple" in lower or lower.endswith(".xml")

    def parse(self, data: bytes, filename: str) -> list[SleepLog]:
        lower = filename.lower()
        if lower.endswith(".zip"):
            return self._parse_zip(data)
        if lower.endswith(".xml"):
            return self._parse_xml(io.BytesIO(data))
        raise ValueError(f"AppleHealthParser: unsupported extension in '{filename}'.")

    # ─── ZIP ──────────────────────────────────────────────────────────────────

    def _parse_zip(self, data: bytes) -> list[SleepLog]:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            xml_names = [
                n for n in zf.namelist()
                if n.lower().endswith("export.xml") or
                   (n.lower().endswith(".xml") and "cda" not in n.lower())
            ]
            if not xml_names:
                raise ValueError("No export.xml found in Apple Health ZIP.")

            with zf.open(xml_names[0]) as f:
                return self._parse_xml(f)

    # ─── XML streaming ────────────────────────────────────────────────────────

    def _parse_xml(self, fileobj) -> list[SleepLog]:
        """
        Stream-parse HealthKit XML.

        Collects:
          - sleep intervals per day grouped by night
          - daily HRV (SDNN nightly average from Watch)
          - daily resting HR
          - daily skin temp variation (Watch Ultra/S8+)
        """
        # Accumulators keyed by "wake date" (YYYY-MM-DD string)
        # sleep_intervals: date → list of (stage, start, end, source_priority)
        sleep_intervals: dict[str, list] = {}
        hrv_readings: dict[str, list[float]] = {}    # date → [sdnn values]
        rhr_readings: dict[str, list[float]] = {}    # date → [rhr values]
        skin_temp: dict[str, float] = {}             # date → latest delta

        for _event, elem in ET.iterparse(fileobj, events=("end",)):
            if elem.tag != "Record":
                elem.clear()
                continue

            rec_type = elem.get("type", "")
            source   = elem.get("sourceName", "")

            if rec_type == _SLEEP_TYPE:
                value = elem.get("value", "")
                stage = _SLEEP_VALUES.get(value)
                if stage and stage != "inbed":
                    start = _parse_apple_ts(elem.get("startDate", ""))
                    end   = _parse_apple_ts(elem.get("endDate", ""))
                    if start and end and end > start:
                        # Assign to the night that ends on wake_date
                        wake_date = end.date()
                        # Overnight: if end is before noon, it's the same calendar night
                        key = wake_date.isoformat()
                        if key not in sleep_intervals:
                            sleep_intervals[key] = []
                        sleep_intervals[key].append(
                            (stage, start, end, _source_priority(source))
                        )

            elif rec_type == _HRV_TYPE:
                val = elem.get("value")
                date_str = elem.get("startDate", "")[:10]
                if val and date_str:
                    hrv_readings.setdefault(date_str, []).append(float(val))

            elif rec_type == _RHR_TYPE:
                val = elem.get("value")
                date_str = elem.get("startDate", "")[:10]
                if val and date_str:
                    rhr_readings.setdefault(date_str, []).append(float(val))

            elif rec_type == _SKIN_TEMP:
                val = elem.get("value")
                date_str = elem.get("startDate", "")[:10]
                if val and date_str:
                    skin_temp[date_str] = float(val)

            elem.clear()

        return self._build_logs(sleep_intervals, hrv_readings, rhr_readings, skin_temp)

    # ─── Aggregation ──────────────────────────────────────────────────────────

    def _build_logs(
        self,
        sleep_intervals: dict,
        hrv_readings: dict,
        rhr_readings: dict,
        skin_temp: dict,
    ) -> list[SleepLog]:
        logs: list[SleepLog] = []

        for date, intervals in sleep_intervals.items():
            if not intervals:
                continue

            # Keep only highest-priority source for each interval
            # (prefer Apple Watch over iPhone)
            max_priority = max(i[3] for i in intervals)
            filtered = [i for i in intervals if i[3] == max_priority] or intervals

            # Find overall sleep window
            all_starts = [i[1] for i in filtered]
            all_ends   = [i[2] for i in filtered]
            sleep_onset = min(all_starts)
            wake_time   = max(all_ends)

            # Aggregate stage durations (minutes)
            stage_mins: dict[str, int] = {"light": 0, "rem": 0, "deep": 0, "awake": 0, "asleep": 0}
            for stage, start, end, _ in filtered:
                stage_mins[stage] = stage_mins.get(stage, 0) + _duration_min(start, end)

            # Total sleep: prefer explicit asleep stages; fall back to legacy "asleep"
            has_stages = (stage_mins["light"] + stage_mins["rem"] + stage_mins["deep"]) > 0
            if has_stages:
                total_min = stage_mins["light"] + stage_mins["rem"] + stage_mins["deep"]
                deep_min  = stage_mins["deep"]  or None
                rem_min   = stage_mins["rem"]   or None
            else:
                # Legacy pre-iOS16 data: only "asleep" value
                total_min = stage_mins["asleep"]
                deep_min  = None
                rem_min   = None

            if total_min < 60:
                continue    # skip naps / noise

            # HRV: Apple Watch records SDNN nightly; take mean over the wake date
            hrv_day = hrv_readings.get(date, [])
            hrv_avg: Optional[float] = round(sum(hrv_day) / len(hrv_day), 1) if hrv_day else None

            # Resting HR
            rhr_day = rhr_readings.get(date, [])
            rhr: Optional[float] = round(sum(rhr_day) / len(rhr_day), 1) if rhr_day else None

            logs.append(SleepLog(
                date=date,
                sleep_onset=sleep_onset,
                wake_time=wake_time,
                total_sleep_min=total_min,
                deep_sleep_min=deep_min,
                rem_sleep_min=rem_min,
                hrv_avg=hrv_avg,
                skin_temp_delta=skin_temp.get(date),
                resting_hr=rhr,
                sleep_score=None,   # Apple Health has no scalar sleep score
                source="apple_health",
            ))

        logs.sort(key=lambda x: x.date)
        return logs
