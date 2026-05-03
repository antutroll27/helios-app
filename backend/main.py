"""
HELIOS Backend — FastAPI Application
Circadian intelligence engine with persistent memory and learning.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from backend.config import CORS_ORIGINS, SUPABASE_URL, SUPABASE_KEY
from backend.auth.session_service import SessionService
from backend.memory.memory_service import MemoryService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources on startup; clean up on shutdown."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "[helios] SUPABASE_URL and SUPABASE_KEY must be set. "
            "Add them to backend/.env (see schema.sql for the project URL)."
        )
    # Startup
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    app.state.supabase = supabase
    app.state.session_service = SessionService(supabase)
    app.state.memory_service = MemoryService(supabase)
    logger.info("[helios] Supabase client initialized")
    yield
    # Shutdown — nothing to teardown for Supabase client
    logger.info("[helios] Shutting down")


app = FastAPI(
    title="HELIOS API",
    description="Circadian Intelligence Engine — Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-HELIOS-CSRF"],
)


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "helios-backend"}


# ─── Routers (imported as phases are built) ──────────────────────────────────

# Phase 1: Chat
from backend.chat.router import router as chat_router
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

from backend.public.router import router as public_router
app.include_router(public_router, prefix="/api/public", tags=["public"])

from backend.auth.router import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# Phase 2: Memory
from backend.memory.router import router as memory_router
app.include_router(memory_router, prefix="/api/memories", tags=["memory"])

# Phase 4: Wearable
from backend.wearable.router import router as wearable_router
app.include_router(wearable_router, prefix="/api/wearable", tags=["wearable"])

# Phase 5: Circadian
from backend.circadian.router import router as circadian_router
app.include_router(circadian_router, prefix="/api/circadian", tags=["circadian"])

# Phase 6: Lab (exercise timing, meal window, supplements)
from backend.lab.router import router as lab_router
app.include_router(lab_router, prefix="/api/lab", tags=["lab"])
