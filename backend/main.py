"""
HELIOS Backend — FastAPI Application
Circadian intelligence engine with persistent memory and learning.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from backend.config import CORS_ORIGINS, SUPABASE_URL, SUPABASE_KEY
from backend.memory.memory_service import MemoryService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    app.state.supabase = supabase
    app.state.memory_service = MemoryService(supabase)
    print("[helios] Supabase client initialized")
    yield
    # Shutdown — nothing to teardown for Supabase client
    print("[helios] Shutting down")


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
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "helios-backend"}


# ─── Routers (imported as phases are built) ──────────────────────────────────

# Phase 1: Chat
from backend.chat.router import router as chat_router
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

# Phase 2: Memory (uncomment when built)
# from backend.memory.router import router as memory_router
# app.include_router(memory_router, prefix="/api/memories", tags=["memory"])

# Phase 4: Wearable (uncomment when built)
# from backend.wearable.router import router as wearable_router
# app.include_router(wearable_router, prefix="/api/wearable", tags=["wearable"])

# Phase 5: Circadian (uncomment when built)
# from backend.circadian.router import router as circadian_router
# app.include_router(circadian_router, prefix="/api", tags=["circadian"])
