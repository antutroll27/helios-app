"""
HELIOS Backend — Chat Router
Handles chat messages with Hermes memory enrichment.
"""

from datetime import datetime, UTC
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from backend.auth.supabase_auth import get_current_user, encrypt_api_key, decrypt_api_key
from backend.chat.llm_proxy import call_llm, parse_ai_response
from backend.chat.prompt_builder import build_system_prompt
from backend.config import SHARED_LLM_PROVIDER, SHARED_LLM_KEY, SHARED_LLM_RATE_LIMIT

router = APIRouter()

MAX_CHAT_HISTORY_MESSAGES = 20
MAX_CHAT_CONTENT_CHARS = 4096


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


# ─── Shared key rate limiting (in-memory, per-user daily count) ──────────────

_shared_key_usage: dict[str, dict] = {}  # user_id -> {date: str, count: int}


def _check_shared_rate_limit(user_id: str) -> bool:
    """Check if user is within the shared key daily rate limit."""
    today = datetime.now().strftime("%Y-%m-%d")
    usage = _shared_key_usage.get(user_id, {})
    if usage.get("date") != today:
        _shared_key_usage[user_id] = {"date": today, "count": 0}
    return _shared_key_usage[user_id]["count"] < SHARED_LLM_RATE_LIMIT


def _increment_shared_usage(user_id: str):
    """Increment shared key usage counter."""
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in _shared_key_usage or _shared_key_usage[user_id].get("date") != today:
        _shared_key_usage[user_id] = {"date": today, "count": 0}
    _shared_key_usage[user_id]["count"] += 1


# ─── Memory-enriched chat endpoint ──────────────────────────────────────────

@router.post("/send", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """
    Main chat endpoint with Hermes memory injection.
    Supports BYOK (user provides provider+key) or shared key (rate-limited).
    Messages are persisted to Supabase for Hermes learning on session end.
    """
    supabase = request.app.state.supabase
    memory_service = request.app.state.memory_service

    # Resolve provider + key
    using_shared = not body.api_key or not body.provider
    if using_shared:
        if not SHARED_LLM_KEY:
            raise HTTPException(status_code=503, detail="Shared AI is not configured. Please add your own API key in Settings.")
        if not _check_shared_rate_limit(user_id):
            raise HTTPException(status_code=429, detail="Daily AI limit reached. Add your own API key in Settings for unlimited access.")
        provider = SHARED_LLM_PROVIDER
        api_key = SHARED_LLM_KEY
        _increment_shared_usage(user_id)
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
    except Exception:
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
        print(f"[helios] chat_messages insert failed: {e}")

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
    user_id: str = Depends(get_current_user),
):
    """
    End a chat session and trigger Hermes background learning.
    Fetches provider+key from the session row — no credentials needed from client.
    """
    supabase = request.app.state.supabase
    memory_service = request.app.state.memory_service

    # Fetch session row (verify ownership + get credentials for Hermes)
    session_result = supabase.table("chat_sessions") \
        .select("provider, encrypted_api_key, ended_at") \
        .eq("id", session_id).eq("user_id", user_id) \
        .execute()

    if not session_result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session_row = session_result.data[0]

    # Guard: prevent double-processing if already ended (inactivity timer + unmount race)
    if session_row.get("ended_at"):
        return {"status": "already_ended", "session_id": session_id}

    # Mark session ended
    supabase.table("chat_sessions") \
        .update({"ended_at": datetime.now(UTC).isoformat()}) \
        .eq("id", session_id).execute()

    # Count messages to decide whether Hermes should run
    count_result = supabase.table("chat_messages") \
        .select("id", count="exact") \
        .eq("session_id", session_id) \
        .execute()
    message_count = count_result.count or 0

    hermes_queued = False
    if message_count >= 4:
        provider = session_row.get("provider", SHARED_LLM_PROVIDER)
        enc_key = session_row.get("encrypted_api_key")
        try:
            api_key = decrypt_api_key(enc_key) if enc_key else SHARED_LLM_KEY
        except Exception:
            api_key = SHARED_LLM_KEY  # fallback if decryption fails

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
    user_id: str = Depends(get_current_user),
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
    user_id: str = Depends(get_current_user),
):
    """Get the user's current Hermes memory file."""
    memory_service = request.app.state.memory_service
    memory_md = await memory_service.get_memory(user_id)
    return {"user_id": user_id, "memory_md": memory_md}


@router.delete("/memory")
async def reset_user_memory(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Reset the user's memory (GDPR delete / fresh start)."""
    memory_service = request.app.state.memory_service
    await memory_service.reset_memory(user_id)
    return {"status": "ok", "message": "Memory reset to default."}
