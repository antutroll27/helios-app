"""
HELIOS Backend — Chat Router
Handles chat messages, session management, and AI responses.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.auth.supabase_auth import get_current_user
from backend.chat.llm_proxy import call_llm, parse_ai_response
from backend.chat.prompt_builder import build_system_prompt

router = APIRouter()


# ─── Request / Response Models ───────────────────────────────────────────────

class ChatContext(BaseModel):
    lat: float
    lng: float
    timezone: str

class ChatRequest(BaseModel):
    message: str
    provider: str  # "openai" | "claude" | "kimi" | "glm"
    api_key: str   # user's API key (sent per-request for now, encrypted storage in v2)
    session_id: Optional[str] = None
    context: ChatContext
    history: list[dict] = []  # previous messages [{role, content}]

class ChatResponse(BaseModel):
    message: str
    visual_cards: list[dict]
    session_id: str


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Main chat endpoint. Enriches the system prompt with memories and live data,
    proxies to the user's chosen LLM, and stores the conversation.
    """
    # Generate session ID if new conversation
    session_id = request.session_id or str(uuid.uuid4())

    # Build enriched system prompt
    # Phase 2 will add Mem0 memory injection here
    system_prompt = build_system_prompt(
        lat=request.context.lat,
        lng=request.context.lng,
        timezone=request.context.timezone,
        user_id=user_id,
        # memory_block=""  # Phase 2: inject memories here
    )

    # Build conversation with user's new message
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

    # Parse response into message + visual cards
    parsed = parse_ai_response(raw_response)

    # TODO Phase 1.5: Store messages in Supabase
    # await store_message(session_id, "user", request.message)
    # await store_message(session_id, "assistant", parsed["message"], parsed["visual_cards"])

    return ChatResponse(
        message=parsed["message"],
        visual_cards=parsed["visual_cards"],
        session_id=session_id,
    )


@router.post("/end-session")
async def end_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
):
    """
    End a chat session and trigger Hermes background learning.
    Called when user closes chat or after inactivity timeout.
    """
    # TODO Phase 3: Trigger Hermes background processing
    # messages = await get_session_messages(session_id)
    # if len(messages) >= 3:
    #     background_tasks.add_task(process_session, session_id, user_id, messages)

    return {"status": "ok", "session_id": session_id, "hermes_queued": False}


@router.get("/history")
async def get_history(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """Get messages for a chat session."""
    # TODO: Fetch from Supabase chat_messages table
    return {"session_id": session_id, "messages": []}
