"""
HELIOS — Wearable Pipeline
Unified abstraction over device-specific parsers → SleepLog list.

Supports:
  oura        — ZIP export or JSON (fully implemented via OuraParser)
  fitbit      — Google Takeout ZIP (stub — CSV sleep export)
  garmin      — GarminDB/FIT export (stub)
  whoop       — CSV export (stub)
  samsung     — Samsung Health ZIP (stub)
  apple_health— HealthKit XML export (stub)

All parsers return list[SleepLog] matching the chronotype_engine.SleepLog dataclass.
"""

import io
import json
import logging
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ─── SleepLog (mirrors chronotype_engine.SleepLog exactly) ──────────────────

from dataclasses import dataclass


@dataclass
class SleepLog:
    date: str
    sleep_onset: datetime
    wake_time: datetime
    total_sleep_min: int
    deep_sleep_min: Optional[int] = None
    rem_sleep_min: Optional[int] = None
    hrv_avg: Optional[float] = None
    skin_temp_delta: Optional[float] = None
    resting_hr: Optional[float] = None
    sleep_score: Optional[int] = None
    source: str = "manual"


# ─── Base Parser ─────────────────────────────────────────────────────────────

class WearableParser(ABC):
    """
    Abstract base for all device parsers.

    Subclasses implement `parse(data: bytes, filename: str) -> list[SleepLog]`.
    The pipeline calls `can_handle(filename)` to route files automatically.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Identifier string used in SleepLog.source."""

    @abstractmethod
    def can_handle(self, filename: str) -> bool:
        """Return True if this parser can process the given filename."""

    @abstractmethod
    def parse(self, data: bytes, filename: str) -> list[SleepLog]:
        """
        Parse raw file bytes into SleepLog records.

        Args:
            data: Raw file bytes (ZIP or JSON or CSV).
            filename: Original filename for format detection.

        Returns:
            List of SleepLog objects sorted ascending by date.

        Raises:
            ValueError: If file is corrupt or format is unrecognised.
        """


# ─── Oura Parser (fully implemented — delegates to parsers/oura.py) ──────────

class OuraPipelineParser(WearableParser):
    """Wraps the existing OuraParser for use in the pipeline."""

    @property
    def source_name(self) -> str:
        return "oura"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return lower.endswith(".zip") or (lower.endswith(".json") and "oura" in lower)

    def parse(self, data: bytes, filename: str) -> list[SleepLog]:
        # Import here to avoid circular imports with backend path wiring
        try:
            from wearable.parsers.oura import OuraParser
        except ImportError:
            from backend.wearable.parsers.oura import OuraParser

        raw_logs = OuraParser().parse(data, filename)

        result = []
        for r in raw_logs:
            result.append(SleepLog(
                date=r["date"],
                sleep_onset=datetime.fromisoformat(r["sleep_onset"]),
                wake_time=datetime.fromisoformat(r["wake_time"]),
                total_sleep_min=r["total_sleep_min"],
                deep_sleep_min=r.get("deep_sleep_min"),
                rem_sleep_min=r.get("rem_sleep_min"),
                hrv_avg=r.get("hrv_avg"),
                skin_temp_delta=r.get("skin_temp_delta"),
                resting_hr=r.get("resting_hr"),
                sleep_score=r.get("sleep_score"),
                source="oura",
            ))
        return sorted(result, key=lambda x: x.date)


# ─── Stub Parsers ────────────────────────────────────────────────────────────

class _StubParser(WearableParser):
    """Base for parsers that are not yet implemented."""

    def parse(self, data: bytes, filename: str) -> list[SleepLog]:
        raise NotImplementedError(
            f"{self.source_name.capitalize()} parser is not yet implemented. "
            "Export your data from the Oura app and upload the ZIP file instead."
        )


class FitbitParser(_StubParser):
    @property
    def source_name(self) -> str:
        return "fitbit"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return "fitbit" in lower or (lower.endswith(".zip") and "google" in lower)


class GarminParser(_StubParser):
    @property
    def source_name(self) -> str:
        return "garmin"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return "garmin" in lower or lower.endswith(".fit")


class WhoopParser(_StubParser):
    @property
    def source_name(self) -> str:
        return "whoop"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return "whoop" in lower and lower.endswith(".csv")


class SamsungParser(_StubParser):
    @property
    def source_name(self) -> str:
        return "samsung"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return "samsung" in lower or "shealth" in lower


class AppleHealthParser(_StubParser):
    @property
    def source_name(self) -> str:
        return "apple_health"

    def can_handle(self, filename: str) -> bool:
        lower = filename.lower()
        return "apple" in lower or lower.endswith(".xml")


# ─── Pipeline ─────────────────────────────────────────────────────────────────

_PARSERS: list[WearableParser] = [
    OuraPipelineParser(),
    FitbitParser(),
    GarminParser(),
    WhoopParser(),
    SamsungParser(),
    AppleHealthParser(),
]


def detect_parser(filename: str) -> Optional[WearableParser]:
    """
    Return the first parser that claims it can handle *filename*, or None.

    Priority follows _PARSERS order — OuraParser is checked first since
    generic ZIP files are more likely to be Oura exports.
    """
    for parser in _PARSERS:
        if parser.can_handle(filename):
            return parser
    return None


def parse_wearable_file(data: bytes, filename: str) -> list[SleepLog]:
    """
    Parse a wearable export file into SleepLog records.

    Auto-detects the device type from the filename.

    Args:
        data: Raw file bytes.
        filename: Original filename (used for parser routing).

    Returns:
        List of SleepLog objects sorted ascending by date.

    Raises:
        ValueError: If no parser can handle the file or parsing fails.
        NotImplementedError: If the detected parser is not yet implemented.
    """
    parser = detect_parser(filename)
    if parser is None:
        raise ValueError(
            f"Unrecognised wearable file format: '{filename}'. "
            "Supported: Oura ZIP/JSON. Upload an Oura export to get started."
        )
    logger.info("[pipeline] Routing '%s' → %s parser", filename, parser.source_name)
    return parser.parse(data, filename)


def supported_sources() -> list[dict]:
    """Return metadata for all parsers (implemented + stub)."""
    return [
        {
            "source": p.source_name,
            "implemented": not isinstance(p, _StubParser),
        }
        for p in _PARSERS
    ]
