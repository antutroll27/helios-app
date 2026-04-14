from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from backend.config import AQICN_TOKEN, NASA_API_KEY

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
AQICN_URL = "https://api.waqi.info/feed/geo:{lat};{lng}/"
DONKI_BASE_URL = "https://api.nasa.gov/DONKI"


def cache_key_for_coords(lat: float, lng: float) -> str:
    return f"{lat:.3f}:{lng:.3f}"


def _parse_timestamp(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def read_cache(db, source: str, cache_key: str) -> dict[str, Any] | None:
    result = (
        db.table("public_api_cache")
        .select("payload, expires_at")
        .eq("source", source)
        .eq("cache_key", cache_key)
        .execute()
    )
    if not result.data:
        return None

    row = result.data[0]
    if _parse_timestamp(row["expires_at"]) <= datetime.now(UTC):
        return None

    return row["payload"]


def write_cache(db, source: str, cache_key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
    now = datetime.now(UTC)
    (
        db.table("public_api_cache")
        .upsert(
            {
                "source": source,
                "cache_key": cache_key,
                "payload": payload,
                "fetched_at": now.isoformat(),
                "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat(),
            },
            on_conflict="source,cache_key",
        )
        .execute()
    )


def _aqi_to_label(aqi: int) -> str:
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


async def fetch_open_meteo_upstream(lat: float, lng: float) -> dict[str, Any]:
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "uv_index,temperature_2m,relative_humidity_2m",
        "hourly": "temperature_2m",
        "daily": "uv_index_max,temperature_2m_max,temperature_2m_min,sunshine_duration",
        "timezone": "auto",
        "forecast_days": 3,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(OPEN_METEO_URL, params=params)
        response.raise_for_status()
        data = response.json()

    hourly_times = data.get("hourly", {}).get("time", [])
    hourly_temps = data.get("hourly", {}).get("temperature_2m", [])
    night_temps: list[float] = []
    for time_string, temperature in zip(hourly_times, hourly_temps, strict=False):
        hour = datetime.fromisoformat(time_string).hour
        if hour >= 22 or hour < 6:
            night_temps.append(float(temperature))

    daily = data.get("daily", {})
    if night_temps:
        temperature_night = round(sum(night_temps) / len(night_temps), 1)
    else:
        temp_min = float((daily.get("temperature_2m_min") or [0])[0])
        temp_max = float((daily.get("temperature_2m_max") or [0])[0])
        temperature_night = round((temp_min + temp_max) / 2, 1)

    current = data.get("current", {})
    sunshine_seconds = float((daily.get("sunshine_duration") or [0])[0] or 0)
    return {
        "uv_index_now": float(current.get("uv_index") or 0),
        "uv_index_max": float((daily.get("uv_index_max") or [0])[0] or 0),
        "temperature_now": float(current.get("temperature_2m") or 0),
        "temperature_night": temperature_night,
        "humidity": float(current.get("relative_humidity_2m") or 0),
        "sunshine_duration_min": round(sunshine_seconds / 60, 1),
    }


async def fetch_aqi_upstream(lat: float, lng: float) -> dict[str, Any]:
    if not AQICN_TOKEN:
        raise RuntimeError("AQICN_TOKEN not configured")

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            AQICN_URL.format(lat=lat, lng=lng),
            params={"token": AQICN_TOKEN},
        )
        response.raise_for_status()
        data = response.json()

    if data.get("status") != "ok":
        raise RuntimeError(f"AQICN upstream error: {data.get('status', 'unknown')}")

    aqi_level = int(data.get("data", {}).get("aqi") or 0)
    return {
        "aqi_level": aqi_level,
        "aqi_label": _aqi_to_label(aqi_level),
        "pm25": float(data.get("data", {}).get("iaqi", {}).get("pm25", {}).get("v") or 0),
    }


def _format_date(date_value: datetime) -> str:
    return date_value.strftime("%Y-%m-%d")


def _days_ago(count: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=count)


def _days_ahead(count: int) -> datetime:
    return datetime.now(UTC) + timedelta(days=count)


async def _fetch_donki_json(endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{DONKI_BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        data = response.json()
    return data if isinstance(data, list) else []


async def fetch_donki_summary_upstream() -> dict[str, Any]:
    api_key = NASA_API_KEY or "DEMO_KEY"
    upcoming_cmes = await _fetch_donki_json(
        "CMEAnalysis",
        {
            "startDate": _format_date(_days_ago(2)),
            "endDate": _format_date(_days_ahead(7)),
            "mostAccurateOnly": "true",
            "completeEntryOnly": "true",
            "speed": "500",
            "halfAngle": "30",
            "catalog": "ALL",
            "api_key": api_key,
        },
    )
    recent_storms = await _fetch_donki_json(
        "GST",
        {
            "startDate": _format_date(_days_ago(7)),
            "endDate": _format_date(datetime.now(UTC)),
            "api_key": api_key,
        },
    )
    active_flares = await _fetch_donki_json(
        "FLR",
        {
            "startDate": _format_date(_days_ago(1)),
            "endDate": _format_date(datetime.now(UTC)),
            "api_key": api_key,
        },
    )
    notifications = await _fetch_donki_json(
        "notifications",
        {
            "startDate": _format_date(_days_ago(3)),
            "endDate": _format_date(datetime.now(UTC)),
            "type": "all",
            "api_key": api_key,
        },
    )
    notifications = [
        entry
        for entry in notifications
        if entry.get("messageType") in {"GST", "CME", "IPS", "FLR"}
    ]

    next_geostorm_eta_hours: float | None = None
    for cme in upcoming_cmes:
        for enlil in cme.get("enlilList") or []:
            if not enlil.get("isEarthGB"):
                continue
            for impact in enlil.get("impactList") or []:
                if impact.get("location") != "Earth":
                    continue
                arrival_time = impact.get("arrivalTime")
                if not arrival_time:
                    continue
                hours_until = (_parse_timestamp(arrival_time) - datetime.now(UTC)).total_seconds() / 3600
                if hours_until <= 0:
                    continue
                rounded = round(hours_until, 1)
                if next_geostorm_eta_hours is None or rounded < next_geostorm_eta_hours:
                    next_geostorm_eta_hours = rounded

    return {
        "upcoming_cmes": upcoming_cmes,
        "recent_storms": recent_storms,
        "active_flares": active_flares,
        "notifications": notifications,
        "next_geostorm_eta_hours": next_geostorm_eta_hours,
    }


async def fetch_environment_upstream(lat: float, lng: float) -> dict[str, Any]:
    open_meteo_payload, aqi_payload = await _gather_environment_payloads(lat, lng)
    return {**open_meteo_payload, **aqi_payload}


async def _gather_environment_payloads(lat: float, lng: float) -> tuple[dict[str, Any], dict[str, Any]]:
    weather_payload, aqi_payload = await asyncio.gather(
        fetch_open_meteo_upstream(lat, lng),
        fetch_aqi_upstream(lat, lng),
    )
    return weather_payload, aqi_payload
