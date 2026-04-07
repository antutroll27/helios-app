"""
HELIOS Backend — Chat Router
Handles chat messages with Hermes memory enrichment.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.auth.supabase_auth import get_current_user
from backend.chat.llm_proxy import call_llm, parse_ai_response
from backend.chat.prompt_builder import build_system_prompt
from backend.memory.hermes_learner import HermesLearner

router = APIRouter()


# ─── In-memory session store (Phase 1 — move to Supabase in production) ─────

_sessions: dict[str, list[dict]] = {}  # session_id -> messages
_session_meta: dict[str, dict] = {}    # session_id -> {user_id, provider, api_key}


# ─── Request / Response Models ───────────────────────────────────────────────

class ChatContext(BaseModel):
    lat: float
    lng: float
    timezone: str

class ChatRequest(BaseModel):
    message: str
    provider: str
    api_key: str
    session_id: Optional[str] = None
    context: ChatContext
    history: list[dict] = []

class ChatResponse(BaseModel):
    message: str
    visual_cards: list[dict]
    session_id: str


# ─── Memory-enriched chat endpoint ──────────────────────────────────────────

@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Main chat endpoint with Hermes memory injection.

    1. Fetch user's memory.md (learned insights from past sessions)
    2. Build enriched system prompt (scientific KB + live data + memories)
    3. Proxy to user's chosen LLM
    4. Store messages in session for later Hermes processing
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Fetch user's memory for prompt enrichment
    # TODO: Wire to MemoryService.get_memory_for_prompt(user_id) when Supabase is connected
    memory_block = ""  # Will be populated from Supabase user_memories table

    # Build enriched system prompt
    system_prompt = build_system_prompt(
        lat=request.context.lat,
        lng=request.context.lng,
        timezone=request.context.timezone,
        user_id=user_id,
        memory_block=memory_block,
    )

    # Build conversation
    messages = request.history + [{"role": "user", "content": request.message}]

    # Call LLM
    try:
        raw_response = await call_llm(
            provider=request.provider,
            api_key=request.api_key,
            system_prompt=system_prompt,
            messages=messages,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {e}")

    # Parse response
    parsed = parse_ai_response(raw_response)

    # Store in session for Hermes processing on end-session
    if session_id not in _sessions:
        _sessions[session_id] = []
        _session_meta[session_id] = {
            "user_id": user_id,
            "provider": request.provider,
            "api_key": request.api_key,
        }
    _sessions[session_id].append({"role": "user", "content": request.message})
    _sessions[session_id].append({"role": "assistant", "content": parsed["message"]})

    return ChatResponse(
        message=parsed["message"],
        visual_cards=parsed["visual_cards"],
        session_id=session_id,
    )


# ─── Session end → Hermes learns ────────────────────────────────────────────

async def _hermes_background_task(session_id: str):
    """
    Background task: Hermes processes the session transcript,
    extracts circadian insights, and updates the user's memory.md.
    Uses the user's own LLM key — zero extra cost.
    """
    messages = _sessions.get(session_id, [])
    meta = _session_meta.get(session_id, {})

    if not messages or len(messages) < 4:  # Need at least 2 exchanges
        return

    user_id = meta.get("user_id", "")
    provider = meta.get("provider", "")
    api_key = meta.get("api_key", "")

    if not user_id or not api_key:
        return

    # TODO: Replace with MemoryService when Supabase is connected
    # For now, use in-memory store
    from backend.memory.hermes_learner import DEFAULT_MEMORY
    current_memory = _user_memories.get(user_id, DEFAULT_MEMORY)

    learner = HermesLearner()
    updated_memory = await learner.process_session(
        messages=messages,
        current_memory=current_memory,
        provider=provider,
        api_key=api_key,
    )

    _user_memories[user_id] = updated_memory
    print(f"Hermes updated memory for user {user_id[:8]}... ({len(messages)} messages processed)")

    # Cleanup session data
    _sessions.pop(session_id, None)
    _session_meta.pop(session_id, None)


# In-memory user memories (move to Supabase in production)
_user_memories: dict[str, str] = {}


@router.post("/end-session")
async def end_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
):
    """
    End a chat session and trigger Hermes background learning.
    Hermes analyzes the conversation, extracts insights, and updates
    the user's memory.md — all using the user's own LLM key.
    """
    messages = _sessions.get(session_id, [])
    has_enough = len(messages) >= 4

    if has_enough:
        background_tasks.add_task(_hermes_background_task, session_id)

    return {
        "status": "ok",
        "session_id": session_id,
        "messages_in_session": len(messages),
        "hermes_queued": has_enough,
    }


@router.get("/history")
async def get_history(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """Get messages for a chat session."""
    messages = _sessions.get(session_id, [])
    return {"session_id": session_id, "messages": messages}


@router.get("/memory")
async def get_user_memory(
    user_id: str = Depends(get_current_user),
):
    """Get the user's current memory file (what Hermes has learned)."""
    from backend.memory.hermes_learner import DEFAULT_MEMORY
    memory = _user_memories.get(user_id, DEFAULT_MEMORY)
    return {"user_id": user_id, "memory_md": memory}


@router.delete("/memory")
async def reset_user_memory(
    user_id: str = Depends(get_current_user),
):
    """Reset the user's memory (GDPR delete / fresh start)."""
    from backend.memory.hermes_learner import DEFAULT_MEMORY
    _user_memories[user_id] = DEFAULT_MEMORY
    return {"status": "ok", "message": "Memory reset to default."}
