"""
HELIOS Backend — Configuration
Loads all settings from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Supabase ────────────────────────────────────────────────────────────────

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # service role key (server-side)
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

# ─── Encryption ──────────────────────────────────────────────────────────────

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")  # Fernet key for API key encryption

# ─── CORS ────────────────────────────────────────────────────────────────────

CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:5174,https://helios-app-six.vercel.app"
).split(",")

# ─── LLM Provider Configs (mirrors useAI.ts PROVIDER_CONFIGS) ────────────────

PROVIDER_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-5.3",
    },
    "claude": {
        "base_url": "https://api.anthropic.com/v1/messages",
        "model": "claude-opus-4-6",
    },
    "kimi": {
        "base_url": "https://api.deepinfra.com/v1/openai/chat/completions",
        "model": "moonshotai/Kimi-K2-Instruct",
    },
    "glm": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-4-flash",
    },
}
