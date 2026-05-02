"""
HELIOS Backend — Memory Routes
Exposes per-user Hermes memory over HTTP.

Routes:
  GET    /api/memories/me  — fetch the authenticated user's memory markdown
  DELETE /api/memories/me  — reset memory to default (GDPR erasure)
"""

import logging
from fastapi import APIRouter, Depends, Request

from backend.auth.supabase_auth import get_current_user_from_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me")
async def get_my_memory(
    request: Request,
    user_id: str = Depends(get_current_user_from_session),
):
    """Return the authenticated user's Hermes memory as markdown."""
    memory_service = request.app.state.memory_service
    memory_md = await memory_service.get_memory(user_id)
    return {"user_id": user_id, "memory_md": memory_md}


@router.delete("/me")
async def reset_my_memory(
    request: Request,
    user_id: str = Depends(get_current_user_from_session),
):
    """Reset the authenticated user's memory to default (GDPR erasure)."""
    memory_service = request.app.state.memory_service
    await memory_service.reset_memory(user_id)
    logger.info("[memory] Reset memory for user %s", user_id)
    return {"status": "reset", "user_id": user_id}
