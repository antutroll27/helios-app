from __future__ import annotations

from time import monotonic

from fastapi import APIRouter, HTTPException, Query, Request

from backend.config import (
    PUBLIC_AQI_CACHE_TTL_SECONDS,
    PUBLIC_DONKI_CACHE_TTL_SECONDS,
    PUBLIC_ENVIRONMENT_CACHE_TTL_SECONDS,
    PUBLIC_ROUTE_MAX_REQUESTS,
    PUBLIC_ROUTE_WINDOW_SECONDS,
)
from backend.public.cache_service import (
    cache_key_for_coords,
    fetch_aqi_upstream,
    fetch_donki_summary_upstream,
    fetch_environment_upstream,
    read_cache,
    write_cache,
)

router = APIRouter()

_public_route_usage: dict[str, dict[str, float | int]] = {}


def _client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip", "").strip()
    if forwarded_for:
        return forwarded_for
    if real_ip:
        return real_ip
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _prune_public_usage(now: float) -> None:
    stale_hosts = [
        host
        for host, usage in _public_route_usage.items()
        if now - float(usage["window_started"]) >= PUBLIC_ROUTE_WINDOW_SECONDS
    ]
    for host in stale_hosts:
        _public_route_usage.pop(host, None)


def _enforce_public_rate_limit(request: Request) -> None:
    if PUBLIC_ROUTE_MAX_REQUESTS <= 0 or PUBLIC_ROUTE_WINDOW_SECONDS <= 0:
        return

    now = monotonic()
    _prune_public_usage(now)
    client_host = _client_identifier(request)
    usage = _public_route_usage.get(client_host)
    if usage is None or now - float(usage["window_started"]) >= PUBLIC_ROUTE_WINDOW_SECONDS:
        _public_route_usage[client_host] = {"window_started": now, "count": 1}
        return

    if int(usage["count"]) >= PUBLIC_ROUTE_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Public data rate limit exceeded.")

    usage["count"] = int(usage["count"]) + 1


@router.get("/aqi")
async def get_aqi(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    _enforce_public_rate_limit(request)
    db = request.app.state.supabase
    cache_key = cache_key_for_coords(lat, lng)
    cached = await read_cache(db, "aqi", cache_key)
    if cached is not None:
        return cached

    try:
        payload = await fetch_aqi_upstream(lat, lng)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AQI upstream fetch failed.") from exc

    write_cache(db, "aqi", cache_key, payload, PUBLIC_AQI_CACHE_TTL_SECONDS)
    return payload


@router.get("/environment")
async def get_environment(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    _enforce_public_rate_limit(request)
    db = request.app.state.supabase
    cache_key = cache_key_for_coords(lat, lng)
    cached = await read_cache(db, "environment", cache_key)
    if cached is not None:
        return cached

    try:
        payload = await fetch_environment_upstream(lat, lng)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Environment upstream fetch failed.") from exc

    write_cache(db, "environment", cache_key, payload, PUBLIC_ENVIRONMENT_CACHE_TTL_SECONDS)
    return payload


@router.get("/donki/summary")
async def get_donki_summary(request: Request):
    _enforce_public_rate_limit(request)
    db = request.app.state.supabase
    cache_key = "summary"
    cached = await read_cache(db, "donki_summary", cache_key)
    if cached is not None:
        return cached

    try:
        payload = await fetch_donki_summary_upstream()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="DONKI upstream fetch failed.") from exc

    write_cache(db, "donki_summary", cache_key, payload, PUBLIC_DONKI_CACHE_TTL_SECONDS)
    return payload
