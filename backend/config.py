"""
HELIOS Backend — Configuration
Loads all settings from environment variables.
"""

import os
from dotenv import load_dotenv

# trust-boundary hardening checklist:
# 1. backend-only AQI/NASA tokens
# 2. public cache TTLs
# 3. anonymous public route throttles

load_dotenv()

# ─── Supabase ────────────────────────────────────────────────────────────────

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # service role key (server-side)
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

# ─── Encryption ──────────────────────────────────────────────────────────────

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")  # Fernet key for API key encryption

# ─── Shared LLM Key (for users without their own API key) ───────────────────
# Users who don't configure their own key get the shared "house" model.
# This keeps the onboarding frictionless — they can always add their own later.
# Rate-limited per user to prevent abuse.

SHARED_LLM_PROVIDER = os.environ.get("SHARED_LLM_PROVIDER", "kimi")  # cheapest default
SHARED_LLM_KEY = os.environ.get("SHARED_LLM_KEY", "")
SHARED_LLM_RATE_LIMIT = int(os.environ.get("SHARED_LLM_RATE_LIMIT", "20"))  # msgs/day per user
NASA_API_KEY = os.environ.get("NASA_API_KEY", os.environ.get("VITE_NASA_API_KEY", "DEMO_KEY"))
AQICN_TOKEN = os.environ.get("AQICN_TOKEN", os.environ.get("VITE_AQICN_TOKEN", ""))

# ─── CORS ────────────────────────────────────────────────────────────────────

CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:5174,https://helios-app-six.vercel.app"
).split(",")

PUBLIC_ENVIRONMENT_CACHE_TTL_SECONDS = int(os.environ.get("PUBLIC_ENVIRONMENT_CACHE_TTL_SECONDS", "600"))
PUBLIC_AQI_CACHE_TTL_SECONDS = int(os.environ.get("PUBLIC_AQI_CACHE_TTL_SECONDS", "300"))
PUBLIC_DONKI_CACHE_TTL_SECONDS = int(os.environ.get("PUBLIC_DONKI_CACHE_TTL_SECONDS", "600"))
PUBLIC_ROUTE_WINDOW_SECONDS = int(os.environ.get("PUBLIC_ROUTE_WINDOW_SECONDS", "60"))
PUBLIC_ROUTE_MAX_REQUESTS = int(os.environ.get("PUBLIC_ROUTE_MAX_REQUESTS", "60"))
SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "helios_session")
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "lax")
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "168"))
SESSION_REFRESH_MINUTES = int(os.environ.get("SESSION_REFRESH_MINUTES", "30"))

# ─── LLM Provider Configs (mirrors useAI.ts PROVIDER_CONFIGS) ────────────────

PROVIDER_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-5.4",
    },
    "claude": {
        "base_url": "https://api.anthropic.com/v1/messages",
        "model": "claude-sonnet-4-6",
    },
    "gemini": {
        "base_url": "https://api.aimlapi.com/v1/chat/completions",
        "model": "google/gemini-3-1-flash-lite-preview",
    },
    "grok": {
        "base_url": "https://api.x.ai/v1/chat/completions",
        "model": "grok-4.20-0309-non-reasoning",
    },
    "perplexity": {
        "base_url": "https://api.perplexity.ai/chat/completions",
        "model": "sonar-pro",
    },
    "kimi": {
        "base_url": "https://api.deepinfra.com/v1/openai/chat/completions",
        "model": "moonshotai/Kimi-K2.5",
    },
    "glm": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-5.1",
    },
}
