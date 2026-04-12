# Backend Wiring + Hermes Memory — Design Spec

**Date:** 2026-04-12  
**Scope:** Route authenticated chat through the FastAPI backend (Spec #2) and wire Hermes per-user memory persistence to Supabase (Spec #3). Guest access and direct LLM calls are fully preserved.

---

## 1. Overview

HELIOS currently calls LLM providers directly from the browser for all users. This spec adds a server-side code path for authenticated users:

- **Guest users:** app works exactly as today — direct browser-to-LLM, no backend involvement
- **Authenticated users:** chat routes through the FastAPI backend, which injects Hermes memory into the system prompt, persists the conversation to Supabase, and triggers Hermes learning when the session ends

Hermes memory is a per-user markdown file in `public.user_memories`. It is completely private — one row per user, RLS-enforced. It starts as a blank template and evolves over time as Hermes extracts circadian insights from each conversation.

---

## 2. Architecture

### Data flow — authenticated user

```
User types message
  → useAI.sendMessage() detects auth.isAuthenticated
  → POST /api/chat/send  (Authorization: Bearer <jwt>)
      → JWT validated (supabase_auth.get_current_user)
      → memory_service.get_memory_for_prompt(user_id)   ← loads markdown from user_memories
      → build_system_prompt(..., memory_block=memory)
      → llm_proxy.call_llm(provider, api_key, prompt, history)
      → INSERT chat_sessions row (if new session)
      → INSERT chat_messages rows (user + assistant)
      → return { message, visual_cards, session_id }
  ← frontend stores session_id for next message

Session ends (unmount or 10 min inactivity)
  → POST /api/chat/end-session
      → UPDATE chat_sessions SET ended_at = now()
      → BackgroundTask: memory_service.process_session(user_id, session_id, provider, api_key)
          → SELECT messages FROM chat_messages WHERE session_id = ?
          → HermesLearner.process_session(messages, current_memory, provider, api_key)
          → UPSERT user_memories SET memory_md = updated_memory
```

### Data flow — guest user

```
User types message
  → useAI.sendMessage() detects !auth.isAuthenticated
  → direct fetch to LLM provider API (unchanged from today)
  → parse response → display
  (no session tracking, no memory, no backend involved)
```

---

## 3. Hermes Memory Model

Hermes memory is a single markdown file per user. It is private (RLS: `user_id = auth.uid()`), stored in `public.user_memories`, and never shared between users.

**Default template** (set on first session if no row exists):
```markdown
# HELIOS User Memory

## Chronotype & Sleep
- No data yet

## Caffeine
- No data yet

## Light Exposure
- No data yet

## Protocol Adherence
- No data yet

## Health & Biometrics
- No data yet

## Lifestyle Context
- No data yet

## Preferences
- No data yet

## Last Updated
- Never
```

**After a few sessions it evolves:**
```markdown
## Chronotype & Sleep
- Usual sleep: 00:30, wake: 08:00 — late chronotype
- Reported poor sleep on high Kp nights (mentioned twice)

## Caffeine
- Drinks 2 cups before 10am, sensitive to afternoon caffeine

## Last Updated
- 2026-04-12T14:32:00Z
```

**Hermes runs after session end, not during** — memory updates are never on the critical path of a chat message. Sessions with fewer than 4 messages (2 exchanges) are skipped.

---

## 4. Backend Changes

### 4.1 `backend/main.py`

Add Supabase client and MemoryService initialization to the lifespan startup. Store on `app.state` so routers can access via `request.app.state`.

```python
from contextlib import asynccontextmanager
from supabase import create_client, Client
from memory.memory_service import MemoryService
from config import SUPABASE_URL, SUPABASE_KEY

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

app = FastAPI(lifespan=lifespan)
```

### 4.2 `backend/chat/router.py`

Three surgical changes. The existing rate limiting, provider resolution, and Hermes queuing logic are preserved.

**Change 1 — Memory load (line ~112):**
```python
# Before:
memory_block = ""  # TODO: fetch from MemoryService

# After:
memory_service: MemoryService = request.app.state.memory_service
memory_block = await memory_service.get_memory_for_prompt(user_id)
```

**Change 2 — Session + message persistence (after LLM call):**
```python
# Upsert chat_sessions row
if not request.session_id:
    # New session — insert
    session_result = supabase.table("chat_sessions").insert({
        "user_id": user_id,
        "started_at": datetime.utcnow().isoformat(),
    }).execute()
    session_id = session_result.data[0]["id"]
else:
    # Verify the session exists in DB (client may send stale session_id after server restart)
    existing = supabase.table("chat_sessions").select("id") \
        .eq("id", request.session_id).eq("user_id", user_id).execute()
    if existing.data:
        session_id = request.session_id
    else:
        # Session not found — create a new one
        session_result = supabase.table("chat_sessions").insert({
            "user_id": user_id,
            "started_at": datetime.utcnow().isoformat(),
        }).execute()
        session_id = session_result.data[0]["id"]

# Persist user message + assistant response
# Persistence failures are logged but not surfaced to the user (LLM response already returned)
try:
    supabase.table("chat_messages").insert([
        {"session_id": session_id, "role": "user",      "content": request.message},
        {"session_id": session_id, "role": "assistant",  "content": ai_message, "visual_cards": visual_cards},
    ]).execute()
    # message_count is derived from COUNT(chat_messages) at query time — no explicit increment needed
except Exception as e:
    print(f"[helios] chat_messages insert failed: {e}")
```

**Change 3 — Hermes background task:**
```python
# Before:
updated_memory = await HermesLearner.process_session(messages, _user_memories.get(user_id, ""), provider, api_key)
_user_memories[user_id] = updated_memory

# After (in end-session route handler, using FastAPI BackgroundTasks):
background_tasks.add_task(memory_service.process_session, user_id, session_id, provider, api_key)
# add_task schedules it after the HTTP response is returned — Hermes never blocks the end-session call
# The end-session route handler must accept `background_tasks: BackgroundTasks` as a parameter
```

**Remove:** `_sessions`, `_session_meta`, `_user_memories` in-memory dicts.

### 4.3 `backend/memory/memory_service.py`

Add a `session_id`-aware `process_session` that fetches messages from Supabase instead of taking them as a parameter:

```python
async def process_session(
    self,
    user_id: str,
    session_id: str,
    provider: str,
    api_key: str,
) -> str:
    # Fetch messages from DB — `timestamp` column defined in backend/schema.sql chat_messages table
    result = self.supabase.table("chat_messages") \
        .select("role, content") \
        .eq("session_id", session_id) \
        .order("timestamp") \
        .execute()
    messages = result.data  # [{"role": "user", "content": "..."}, ...]

    if len(messages) < 4:  # Skip sessions with < 2 exchanges
        return

    # get_memory returns raw markdown string (internal use)
    # get_memory_for_prompt (used in router) returns the same markdown, formatted for system prompt injection
    # Both read from user_memories; they may be the same method or two thin wrappers — implementer decides
    current_memory = await self.get_memory(user_id)
    updated_memory = await HermesLearner.process_session(
        messages, current_memory, provider, api_key
    )
    await self.save_memory(user_id, updated_memory)

    # Mark session as hermes-processed
    self.supabase.table("chat_sessions") \
        .update({"hermes_processed": True}) \
        .eq("id", session_id) \
        .execute()
```

### 4.4 `backend/requirements.txt`

Add:
```
supabase>=2.0.0
```

### 4.5 `backend/railway.toml`

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

# Note: Do NOT set PORT here — Railway injects $PORT dynamically and setting it
# to a fixed value may conflict. Remove this block entirely; use $PORT in startCommand only.
```

---

## 5. Frontend Changes

### 5.1 `src/composables/useAI.ts`

Add auth detection at the top of `sendMessage()`. If authenticated and `VITE_BACKEND_URL` is set, route to backend.

**Dependency:** `useAuthStore` from `@/stores/auth` — this store was created in the auth spec (Spec #1) and already exists in the codebase. The `session.access_token` (JWT) and `isAuthenticated` getter are used here.

```typescript
import { useAuthStore } from '@/stores/auth'
import { useGeoStore }  from '@/stores/geo'

export function useAI() {
  const auth = useAuthStore()
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

  async function sendMessage(
    userMessage: string,
    provider: string,
    apiKey: string,
    conversationHistory: ClaudeMessage[] = [],
    sessionId?: string,
  ): Promise<AIResponse & { sessionId?: string }> {
    
    // Authenticated path — route through backend
    if (auth.isAuthenticated && auth.session && BACKEND_URL) {
      const geo   = useGeoStore()
      const response = await fetch(`${BACKEND_URL}/api/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.session.access_token}`,
        },
        body: JSON.stringify({
          message:    userMessage,
          provider,
          api_key:    apiKey,
          session_id: sessionId ?? null,
          context: {
            lat:      geo.lat,
            lng:      geo.lng,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          },
          history: conversationHistory,
        }),
      })
      if (!response.ok) throw new Error(`Backend error: ${response.status}`)
      const data = await response.json()
      return {
        message:     data.message,
        visualCards: data.visual_cards ?? [],
        sessionId:   data.session_id,
      }
    }

    // Guest path — direct LLM call (unchanged)
    // ... existing sendMessage logic ...
  }
}
```

### 5.2 `src/components/ChatInterface.vue`

Two additions only — no visual changes:

```typescript
import { ref, onUnmounted } from 'vue'
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

const sessionId = ref<string | null>(null)
let inactivityTimer: ReturnType<typeof setTimeout> | null = null

// Store session_id from first backend response
function onMessageReceived(response: AIResponse & { sessionId?: string }) {
  if (response.sessionId) sessionId.value = response.sessionId
  // Reset 10-min inactivity timer
  if (inactivityTimer) clearTimeout(inactivityTimer)
  inactivityTimer = setTimeout(endSession, 10 * 60 * 1000)
}

async function endSession() {
  // Guard: prevent double-call (inactivity timer + unmount firing simultaneously)
  if (!sessionId.value || !BACKEND_URL) return
  const id = sessionId.value
  sessionId.value = null  // clear immediately to prevent re-entry
  const auth = useAuthStore()
  if (!auth.isAuthenticated || !auth.session) return
  fetch(`${BACKEND_URL}/api/chat/end-session?session_id=${id}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${auth.session.access_token}` },
  }).catch(() => {})  // fire-and-forget, don't block unmount
}

onUnmounted(() => {
  if (inactivityTimer) clearTimeout(inactivityTimer)
  endSession()  // sessionId already guarded inside; safe to call even if timer already fired
})
```

Pass `sessionId.value` into each `sendMessage()` call after the first.

---

## 6. Environment Variables

### Frontend (`.env` + Vercel dashboard)

```
VITE_BACKEND_URL=https://your-railway-app.railway.app
```

### Backend (`backend/.env` + Railway dashboard)

```
SUPABASE_URL=https://zciyjaaigefeearpzsip.supabase.co
SUPABASE_KEY=<service role key — from Supabase dashboard → Settings → API>
SUPABASE_JWT_SECRET=<JWT secret — from Supabase dashboard → Settings → API>
ENCRYPTION_KEY=<44-char Fernet key — generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
SHARED_LLM_PROVIDER=kimi
SHARED_LLM_KEY=<DeepInfra API key for shared/free tier>
CORS_ORIGINS=http://localhost:5173,https://helios-app-six.vercel.app
```

---

## 7. File Summary

| File | Action |
|---|---|
| `backend/main.py` | Modify — init Supabase client + MemoryService in lifespan |
| `backend/chat/router.py` | Modify — wire MemoryService, persist sessions/messages, remove in-memory dicts |
| `backend/memory/memory_service.py` | Modify — add session_id-aware `process_session` that fetches from DB |
| `backend/requirements.txt` | Modify — add `supabase>=2.0.0` |
| `backend/railway.toml` | Create — Railway deployment config |
| `backend/.env` | Create — backend environment variables (not committed) |
| `src/composables/useAI.ts` | Modify — add auth branch, session_id tracking |
| `src/components/ChatInterface.vue` | Modify — track sessionId, end-session on unmount + inactivity |
| `.env` | Modify — add `VITE_BACKEND_URL` |

**Unchanged:** `hermes_learner.py`, `memory_service.py` (except one method addition), `llm_proxy.py`, `supabase_auth.py`, `prompt_builder.py`, all Vue pages and stores.

---

## 8. What This Spec Does NOT Include

- Password reset / profile editing (auth spec deferred these)
- Live data injection into backend system prompt (Phase 5 — astral, NOAA, Open-Meteo)
- Wearable data import (Phase 4)
- Chat history UI (viewing past sessions) — memory is the persistence layer for now
- API key encryption/storage in Supabase (Phase 3 — settings UI)
- Streaming responses (SSE/WebSockets)
