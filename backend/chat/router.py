"""
HELIOS Backend — Chat Router
Handles chat messages with Hermes memory enrichment.
"""

import logging
from datetime import datetime, UTC
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request

logger = logging.getLogger(__name__)
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from backend.auth.supabase_auth import (
    get_current_user_from_session,
    encrypt_api_key,
    decrypt_api_key,
)
from backend.chat.llm_proxy import call_llm, parse_ai_response
from backend.chat.prompt_builder import build_system_prompt
from backend.config import SHARED_LLM_PROVIDER, SHARED_LLM_KEY, SHARED_LLM_RATE_LIMIT

router = APIRouter()

MAX_CHAT_HISTORY_MESSAGES = 20
MAX_CHAT_CONTENT_CHARS = 4096
CSRF_HEADER_NAME = "X-HELIOS-CSRF"


# ─── Request / Response Models ───────────────────────────────────────────────

class ChatContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: Optional[float] = None
    lng: Optional[float] = None
    timezone: Optional[str] = None
    location: Optional[dict] = None
    solar: Optional[dict] = None
    space_weather: Optional[dict] = None
    environment: Optional[dict] = None
    protocol: Optional[dict] = None
    user: Optional[dict] = None


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: StrictStr = Field(min_length=1, max_length=MAX_CHAT_CONTENT_CHARS)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: StrictStr = Field(min_length=1, max_length=MAX_CHAT_CONTENT_CHARS)
    provider: Optional[StrictStr] = None   # None = use shared key
    api_key: Optional[StrictStr] = None    # None = use shared key
    session_id: Optional[StrictStr] = None
    context: ChatContext
    history: Annotated[list[ChatHistoryMessage], Field(default_factory=list, max_length=MAX_CHAT_HISTORY_MESSAGES)]

class ChatResponse(BaseModel):
    message: str
    visual_cards: list[dict]
    session_id: str
    using_shared_key: bool


def _resolve_location_context(context: ChatContext) -> tuple[float, float, str, Optional[str]]:
    location = context.location or {}
    lat = context.lat if context.lat is not None else location.get("lat")
    lng = context.lng if context.lng is not None else location.get("lng")
    timezone = context.timezone if context.timezone else location.get("timezone")
    location_name = location.get("location_name")

    if lat is None or lng is None or timezone is None:
        raise HTTPException(status_code=422, detail="Context location requires lat, lng, and timezone.")

    return float(lat), float(lng), str(timezone), location_name


def require_csrf(request: Request) -> None:
    session = getattr(request.state, "auth_session", None)
    token = request.headers.get(CSRF_HEADER_NAME)
    if not session or not request.app.state.session_service.validate_csrf(session, token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")


# ─── Shared key rate limiting (durable, per-user daily count) ──────────────

def _shared_usage_date() -> str:
    return datetime.now(UTC).date().isoformat()


def _normalize_shared_usage_rpc_result(data) -> dict:
    if isinstance(data, list):
        return data[0] if data else {}
    if isinstance(data, dict):
        return data
    return {}


def _consume_shared_llm_usage(db, user_id: str) -> dict:
    """Atomically consume one shared-key daily quota slot in Postgres."""
    result = db.rpc(
        "consume_shared_llm_usage",
        {
            "p_user_id": user_id,
            "p_limit": SHARED_LLM_RATE_LIMIT,
        },
    ).execute()
    usage = _normalize_shared_usage_rpc_result(getattr(result, "data", None))

    if not usage.get("allowed"):
        raise HTTPException(
            status_code=429,
            detail="Daily AI limit reached. Add your own API key in Settings for unlimited access.",
        )

    return usage


# ─── Memory-enriched chat endpoint ──────────────────────────────────────────

@router.post("/send", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    request: Request,
    user_id: str = Depends(get_current_user_from_session),
):
    """
    Main chat endpoint with Hermes memory injection.
    Supports BYOK (user provides provider+key) or shared key (rate-limited).
    Messages are persisted to Supabase for Hermes learning on session end.
    """
    require_csrf(request)
    supabase = request.app.state.supabase
    memory_service = request.app.state.memory_service

    # Resolve provider + key
    using_shared = not body.api_key or not body.provider
    if using_shared:
        if not SHARED_LLM_KEY:
            raise HTTPException(status_code=503, detail="Shared AI is not configured. Please add your own API key in Settings.")
        provider = SHARED_LLM_PROVIDER
        api_key = SHARED_LLM_KEY
        _consume_shared_llm_usage(supabase, user_id)
    else:
        provider = body.provider
        api_key = body.api_key

    # Fetch user's memory for prompt enrichment
    memory_block = await memory_service.get_memory_for_prompt(user_id)
    lat, lng, timezone, location_name = _resolve_location_context(body.context)
    user_context = body.context.user or {}

    # Build enriched system prompt
    system_prompt = build_system_prompt(
        lat=lat,
        lng=lng,
        timezone=timezone,
        user_id=user_id,
        memory_block=memory_block,
        user_sleep_time=user_context.get("sleep_time", "23:00"),
        user_chronotype=user_context.get("chronotype", "intermediate"),
        user_context=user_context,
        location_name=location_name,
        solar_context=body.context.solar,
        space_weather_context=body.context.space_weather,
        environment_context=body.context.environment,
        protocol_context=body.context.protocol,
    )

    # Build conversation
    messages = [message.model_dump() for message in body.history] + [{"role": "user", "content": body.message}]

    # Call LLM
    try:
        raw_response = await call_llm(
            provider=provider,
            api_key=api_key,
            system_prompt=system_prompt,
            messages=messages,
        )
    except Exception as e:
        logger.error("[helios] LLM call failed: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail="Upstream LLM provider error.")

    parsed = parse_ai_response(raw_response)

    # --- Session persistence ---
    enc_key = encrypt_api_key(api_key) if not using_shared else None

    if not body.session_id:
        # New session — create row in DB
        session_result = supabase.table("chat_sessions").insert({
            "user_id": user_id,
            "provider": provider,
            "encrypted_api_key": enc_key,
        }).execute()
        session_id = session_result.data[0]["id"]
    else:
        # Verify session exists in DB (client may send stale session_id after server restart)
        existing = supabase.table("chat_sessions").select("id") \
            .eq("id", body.session_id).eq("user_id", user_id).execute()
        if existing.data:
            session_id = body.session_id
        else:
            # Session not found — create a fresh one
            session_result = supabase.table("chat_sessions").insert({
                "user_id": user_id,
                "provider": provider,
                "encrypted_api_key": enc_key,
            }).execute()
            session_id = session_result.data[0]["id"]

    # Persist user message + assistant response
    # Failures are logged but not surfaced — LLM response already returned
    try:
        supabase.table("chat_messages").insert([
            {"session_id": session_id, "role": "user", "content": body.message},
            {"session_id": session_id, "role": "assistant", "content": parsed["message"],
             "visual_cards": parsed["visual_cards"]},
        ]).execute()
    except Exception as e:
        logger.warning("[helios] chat_messages insert failed: %s", e)

    return ChatResponse(
        message=parsed["message"],
        visual_cards=parsed["visual_cards"],
        session_id=session_id,
        using_shared_key=using_shared,
    )


# ─── Session end → Hermes learns ────────────────────────────────────────────

@router.post("/end-session")
async def end_session(
    session_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_from_session),
):
    """
    End a chat session and trigger Hermes background learning.
    Fetches provider+key from the session row — no credentials needed from client.
    """
    require_csrf(request)
    supabase = request.app.state.supabase
    memory_service = request.app.state.memory_service

    # Fetch session row (verify ownership + get credentials for Hermes)
    session_result = supabase.table("chat_sessions") \
        .select("provider, encrypted_api_key, ended_at, hermes_processed, hermes_processing") \
        .eq("id", session_id).eq("user_id", user_id) \
        .execute()

    if not session_result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session_row = session_result.data[0]

    if session_row.get("hermes_processed") or session_row.get("hermes_processing"):
        return {"status": "already_processing", "session_id": session_id}

    if session_row.get("ended_at"):
        return {"status": "already_ended", "session_id": session_id}

    # Count messages to decide whether Hermes should run
    count_result = supabase.table("chat_messages") \
        .select("id", count="exact") \
        .eq("session_id", session_id) \
        .execute()
    message_count = count_result.count or 0

    update_payload = {"ended_at": datetime.now(UTC).isoformat()}
    if message_count >= 4:
        update_payload["hermes_processing"] = True

    update_result = supabase.table("chat_sessions") \
        .update(update_payload) \
        .eq("id", session_id) \
        .eq("user_id", user_id) \
        .eq("hermes_processed", False) \
        .eq("hermes_processing", False) \
        .is_("ended_at", "null") \
        .execute()

    if not update_result.data:
        latest_session = supabase.table("chat_sessions") \
            .select("ended_at, hermes_processed, hermes_processing") \
            .eq("id", session_id).eq("user_id", user_id) \
            .execute()
        latest_row = latest_session.data[0] if latest_session.data else {}
        if latest_row.get("hermes_processed") or latest_row.get("hermes_processing"):
            return {"status": "already_processing", "session_id": session_id}
        return {"status": "already_ended", "session_id": session_id}

    hermes_queued = False
    if message_count >= 4:
        provider = session_row.get("provider", SHARED_LLM_PROVIDER)
        enc_key = session_row.get("encrypted_api_key")
        try:
            api_key = decrypt_api_key(enc_key) if enc_key else SHARED_LLM_KEY
        except Exception as e:
            logger.warning("[helios] Decryption failed for session %s, falling back to shared key: %s", session_id, e)
            api_key = SHARED_LLM_KEY

        background_tasks.add_task(
            memory_service.process_session,
            user_id, session_id, provider, api_key,
        )
        hermes_queued = True

    return {
        "status": "ok",
        "session_id": session_id,
        "messages_in_session": message_count,
        "hermes_queued": hermes_queued,
    }


@router.get("/history")
async def get_history(
    session_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_from_session),
):
    """Get messages for a chat session from Supabase."""
    supabase = request.app.state.supabase

    # Verify session ownership
    session_check = supabase.table("chat_sessions").select("id") \
        .eq("id", session_id).eq("user_id", user_id).execute()
    if not session_check.data:
        raise HTTPException(status_code=404, detail="Session not found")

    result = supabase.table("chat_messages") \
        .select("role, content, timestamp") \
        .eq("session_id", session_id) \
        .order("timestamp") \
        .execute()

    return {"session_id": session_id, "messages": result.data or []}


@router.get("/memory")
async def get_user_memory(
    request: Request,
    user_id: str = Depends(get_current_user_from_session),
):
    """Get the user's current Hermes memory file."""
    memory_service = request.app.state.memory_service
    memory_md = await memory_service.get_memory(user_id)
    return {"user_id": user_id, "memory_md": memory_md}


@router.delete("/memory")
async def reset_user_memory(
    request: Request,
    user_id: str = Depends(get_current_user_from_session),
):
    """Reset the user's memory (GDPR delete / fresh start)."""
    require_csrf(request)
    memory_service = request.app.state.memory_service
    await memory_service.reset_memory(user_id)
    return {"status": "ok", "message": "Memory reset to default."}
