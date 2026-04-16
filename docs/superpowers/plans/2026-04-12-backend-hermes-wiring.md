# Backend Wiring + Hermes Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire authenticated chat through FastAPI with Supabase session persistence and per-user Hermes markdown memory, while leaving guest (direct LLM) path completely unchanged.

**Architecture:** Authenticated users are routed through `POST /api/chat/send` which injects Hermes memory into the system prompt, persists messages to `chat_sessions`/`chat_messages`, and triggers background Hermes learning on session end. Three in-memory dicts (`_sessions`, `_session_meta`, `_user_memories`) are replaced with Supabase. The frontend's `useAI.ts` gains an auth branch; `ChatInterface.vue` gains session tracking and an `endSession` call on unmount or 10-min inactivity.

**Tech Stack:** FastAPI + supabase-py v2, Fernet encryption (cryptography), Vue 3 + Pinia (`useAuthStore`, `useGeoStore`), Vitest (frontend), pytest + pytest-asyncio (backend)

---

## File Map

| File | Action | What changes |
|---|---|---|
| Supabase SQL editor | Schema migration | Add `provider`, `encrypted_api_key` cols to `chat_sessions` |
| `backend/main.py` | Modify | Supabase client + MemoryService init in lifespan |
| `backend/memory/memory_service.py` | Modify | Replace `process_session(messages)` with `process_session(session_id)` |
| `backend/memory/test_memory_service.py` | Create | pytest for new `process_session` |
| `backend/chat/router.py` | Modify | Wire memory_service, session persistence, end_session, aux routes |
| `backend/railway.toml` | Create | Railway deployment config |
| `src/composables/useAI.ts` | Modify | Auth branch (backend routing for authenticated users) |
| `src/components/ChatInterface.vue` | Modify | sessionId ref, endSession, inactivity timer |
| `.env` | Modify | Add `VITE_BACKEND_URL` |

---

## Task 1: Schema Migration — add provider + encrypted_api_key to chat_sessions

`chat_sessions` needs to store the provider and encrypted api_key used in the session so that `end_session` can retrieve them to run Hermes (without re-sending credentials from the frontend).

**Files:**
- Run SQL in Supabase SQL Editor (no file change, but record migration)

- [ ] **Step 1: Run migration in Supabase SQL Editor**

Open the Supabase project dashboard → SQL Editor → New query. Run:

```sql
ALTER TABLE public.chat_sessions
  ADD COLUMN IF NOT EXISTS provider TEXT,
  ADD COLUMN IF NOT EXISTS encrypted_api_key TEXT;
```

- [ ] **Step 2: Verify columns exist**

In SQL Editor:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'chat_sessions'
ORDER BY ordinal_position;
```

Expected: see `provider` (text) and `encrypted_api_key` (text) in the output.

- [ ] **Step 3: Commit note**

```bash
cd helios-app
git add -A
git commit -m "chore: schema migration — add provider + encrypted_api_key to chat_sessions"
```

---

## Task 2: Backend main.py — Supabase client + MemoryService in lifespan

The lifespan function currently just prints. We need it to create the Supabase service-role client and attach it + MemoryService to `app.state` so all routers can access them via `request.app.state`.

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Read the current file**

Read `backend/main.py` — focus on the `lifespan` function (lines 13–20) and imports (lines 6–10).

- [ ] **Step 2: Update imports at top of main.py**

Replace the existing imports block with:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from backend.config import CORS_ORIGINS, SUPABASE_URL, SUPABASE_KEY
from backend.memory.memory_service import MemoryService
```

- [ ] **Step 3: Replace lifespan function**

Replace the existing `lifespan` function body:

```python
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
```

- [ ] **Step 4: Start backend and verify no crash**

```bash
cd helios-app/backend
uvicorn main:app --reload --port 8001
```

Expected: `[helios] Supabase client initialized` in startup logs, no exceptions.

```bash
curl http://localhost:8001/api/health
```

Expected: `{"status":"ok","service":"helios-backend"}`

Kill the server with Ctrl+C.

- [ ] **Step 5: Commit**

```bash
git add backend/main.py
git commit -m "feat: init Supabase client + MemoryService in lifespan"
```

---

## Task 3: Backend memory_service.py — session_id-aware process_session

The current `process_session(user_id, messages, provider, api_key)` takes a messages list directly. The new version `process_session(user_id, session_id, provider, api_key)` fetches messages from `chat_messages` in Supabase, skips sessions with < 4 messages, runs Hermes, saves memory, and marks `chat_sessions.hermes_processed = True`.

The existing `get_memory`, `save_memory`, and `get_memory_for_prompt` methods are correct and unchanged.

**Files:**
- Modify: `backend/memory/memory_service.py`
- Create: `backend/memory/test_memory_service.py`

- [ ] **Step 1: Write the failing test first**

Create `backend/memory/test_memory_service.py`:

```python
"""Tests for MemoryService.process_session (session_id variant)."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


def make_supabase_mock(messages_data):
    """
    Build a mock supabase client whose .table() returns STABLE mocks per table name.
    Each table name always returns the same mock object so assertions work correctly
    (side_effect returning a new MagicMock each call would break assert_called_once).
    """
    db = MagicMock()

    messages_mock = MagicMock()
    messages_mock.select.return_value.eq.return_value.order.return_value.execute.return_value.data = messages_data

    memories_mock = MagicMock()
    memories_mock.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "memory_md": "# HELIOS User Memory\n\n## Chronotype\n- No data yet"
    }
    memories_mock.upsert.return_value.execute.return_value = MagicMock()

    sessions_mock = MagicMock()
    sessions_mock.update.return_value.eq.return_value.execute.return_value = MagicMock()

    _table_map = {
        "chat_messages": messages_mock,
        "user_memories": memories_mock,
        "chat_sessions": sessions_mock,
    }
    db.table.side_effect = lambda name: _table_map[name]

    # Expose individual table mocks for assertions
    db._sessions_mock = sessions_mock
    db._memories_mock = memories_mock

    return db


@pytest.mark.asyncio
async def test_process_session_skips_under_4_messages():
    """Sessions with fewer than 4 messages (2 exchanges) are skipped — no Hermes call."""
    from backend.memory.memory_service import MemoryService

    db = make_supabase_mock([
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ])
    service = MemoryService(db)

    result = await service.process_session("uid-1", "sess-1", "kimi", "key-1")

    assert result is None
    # Hermes learner should NOT have been called
    # (we verify by checking no upsert happened on user_memories)
    # The mock doesn't record calls across side_effect, so verify via result.


@pytest.mark.asyncio
async def test_process_session_runs_hermes_and_marks_processed():
    """process_session fetches messages, runs Hermes, saves memory, marks session processed."""
    from backend.memory.memory_service import MemoryService

    messages = [
        {"role": "user", "content": "how's my sleep?"},
        {"role": "assistant", "content": "Your sleep looks short."},
        {"role": "user", "content": "what should I do?"},
        {"role": "assistant", "content": "Try going to bed 30 min earlier."},
    ]
    db = make_supabase_mock(messages)
    service = MemoryService(db)

    updated = "# HELIOS User Memory\n\n## Chronotype\n- Late chronotype\n"
    with patch.object(service.learner, "process_session", new=AsyncMock(return_value=updated)):
        result = await service.process_session("uid-1", "sess-1", "kimi", "key-1")

    assert result == updated
    # hermes_processed flag should have been set — use the stable sessions_mock reference
    db._sessions_mock.update.assert_called_once_with({"hermes_processed": True})


@pytest.mark.asyncio
async def test_process_session_exact_4_messages_runs():
    """Boundary: exactly 4 messages should trigger Hermes."""
    from backend.memory.memory_service import MemoryService

    messages = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"},
        {"role": "assistant", "content": "d"},
    ]
    db = make_supabase_mock(messages)
    service = MemoryService(db)

    with patch.object(service.learner, "process_session", new=AsyncMock(return_value="updated")) as mock_hermes:
        await service.process_session("uid-1", "sess-1", "kimi", "key-1")

    mock_hermes.assert_called_once()
```

- [ ] **Step 2: Run tests — expect failure (method signature wrong)**

```bash
cd helios-app
python -m pytest backend/memory/test_memory_service.py -v
```

Expected: `FAILED` — either import error or `TypeError` from wrong signature.

- [ ] **Step 3: Update process_session in memory_service.py**

Replace the existing `process_session` method (lines 55–81) with:

```python
async def process_session(
    self,
    user_id: str,
    session_id: str,
    provider: str,
    api_key: str,
) -> str | None:
    """
    Process a completed chat session by fetching messages from Supabase.
    Skips sessions with fewer than 4 messages (2 full exchanges).
    Marks the session hermes_processed=True when done.

    Uses the user's own LLM key — zero extra cost.
    """
    # Fetch messages from DB — `timestamp` column defined in backend/schema.sql
    result = self.db.table("chat_messages") \
        .select("role, content") \
        .eq("session_id", session_id) \
        .order("timestamp") \
        .execute()
    messages = result.data  # [{"role": "user", "content": "..."}, ...]

    if len(messages) < 4:  # Need at least 2 full exchanges
        return None

    current_memory = await self.get_memory(user_id)
    updated_memory = await self.learner.process_session(
        messages=messages,
        current_memory=current_memory,
        provider=provider,
        api_key=api_key,
    )
    await self.save_memory(user_id, updated_memory)

    # Mark session as hermes-processed
    self.db.table("chat_sessions") \
        .update({"hermes_processed": True}) \
        .eq("id", session_id) \
        .execute()

    return updated_memory
```

- [ ] **Step 4: Run tests — expect pass**

```bash
python -m pytest backend/memory/test_memory_service.py -v
```

Expected: 3 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/memory/memory_service.py backend/memory/test_memory_service.py
git commit -m "feat: memory_service.process_session fetches from DB by session_id"
```

---

## Task 4: Backend router.py — wire memory_service + session persistence in send_message

Three changes to `send_message`:
1. Fetch memory from `MemoryService` instead of `memory_block = ""`
2. Create/verify session row in `chat_sessions` (DB), persist messages to `chat_messages`
3. Store `provider` and `encrypted_api_key` in the session row for later Hermes use

The `ChatRequest` parameter is renamed from `request` → `body` to free `request` for the FastAPI `Request` object (needed for `request.app.state`). All `request.xxx` field accesses inside `send_message` must become `body.xxx`.

Also remove the three in-memory dicts: `_sessions`, `_session_meta`, `_user_memories`.

**Files:**
- Modify: `backend/chat/router.py`

- [ ] **Step 1: Add new imports at top of router.py**

Add to the existing imports (after line 16):

```python
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from backend.auth.supabase_auth import get_current_user, encrypt_api_key, decrypt_api_key
from backend.config import SHARED_LLM_PROVIDER, SHARED_LLM_KEY, SHARED_LLM_RATE_LIMIT
```

Remove the `HermesLearner` import (line 16) — it's no longer called directly in the router.
Remove the local `from backend.config import SHARED_LLM_RATE_LIMIT` inside `_check_shared_rate_limit` (line 56) since it's now module-level.

- [ ] **Step 2: Remove in-memory session dicts**

Delete these three declarations (lines 22–24 and line 202):

```python
# DELETE these lines:
_sessions: dict[str, list[dict]] = {}
_session_meta: dict[str, dict] = {}
_user_memories: dict[str, str] = {}
```

Keep `_shared_key_usage` (rate limiting stays in-memory).

- [ ] **Step 3: Update send_message signature and body**

Replace the entire `send_message` function (lines 74–156) with:

```python
@router.post("/send", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    request: Request,
    background_tasks: BackgroundTasks,
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

    # Build enriched system prompt
    system_prompt = build_system_prompt(
        lat=body.context.lat,
        lng=body.context.lng,
        timezone=body.context.timezone,
        user_id=user_id,
        memory_block=memory_block,
    )

    # Build conversation
    messages = body.history + [{"role": "user", "content": body.message}]

    # Call LLM
    try:
        raw_response = await call_llm(
            provider=provider,
            api_key=api_key,
            system_prompt=system_prompt,
            messages=messages,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {e}")

    parsed = parse_ai_response(raw_response)

    # --- Session persistence ---
    enc_key = encrypt_api_key(api_key)  # always encrypt; decrypt in end_session for Hermes

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
```

- [ ] **Step 4: Verify dev server starts without import errors**

```bash
cd helios-app/backend
uvicorn main:app --reload --port 8001
```

Expected: startup logs, no `ImportError` or `AttributeError`.

- [ ] **Step 5: Commit**

```bash
git add backend/chat/router.py
git commit -m "feat: wire memory_service + Supabase session persistence in send_message"
```

---

## Task 5: Backend router.py — wire end_session + auxiliary routes

`end_session` must fetch `provider` and `encrypted_api_key` from the session DB row, update `ended_at`, check message count, and dispatch `memory_service.process_session` as a background task.

`get_history`, `get_memory`, `reset_memory` switch from in-memory dicts to Supabase.

Also delete the `_hermes_background_task` function — it's replaced by `memory_service.process_session`.

**Files:**
- Modify: `backend/chat/router.py`

- [ ] **Step 1: Delete _hermes_background_task function**

Delete the entire function `_hermes_background_task` (lines 161–198). It's fully replaced by `memory_service.process_session`.

- [ ] **Step 2: Replace end_session route**

Replace the `end_session` function (lines 205–227) with:

```python
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

    # Mark session ended
    supabase.table("chat_sessions") \
        .update({"ended_at": datetime.now(UTC).isoformat()}) \
        .eq("id", session_id).execute()

    # Count messages to decide whether Hermes should run
    count_result = supabase.table("chat_messages") \
        .select("id") \
        .eq("session_id", session_id) \
        .execute()
    message_count = len(count_result.data) if count_result.data else 0

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
```

- [ ] **Step 3: Replace get_history route**

Replace `get_history` function:

```python
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
```

- [ ] **Step 4: Replace get_user_memory and reset_user_memory routes**

```python
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
```

- [ ] **Step 5: Verify backend starts clean**

```bash
cd helios-app/backend
uvicorn main:app --reload --port 8001
```

Expected: startup without errors.

Manual smoke test — end a nonexistent session:
```bash
curl -X POST "http://localhost:8001/api/chat/end-session?session_id=00000000-0000-0000-0000-000000000000" \
  -H "Authorization: Bearer <test_jwt>"
```
Expected: `404 Session not found`

- [ ] **Step 6: Commit**

```bash
git add backend/chat/router.py
git commit -m "feat: wire end_session + aux routes to Supabase, remove in-memory dicts"
```

---

## Task 6: Backend railway.toml — Railway deployment config

**Files:**
- Create: `backend/railway.toml`

- [ ] **Step 1: Create railway.toml**

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

Note: Do NOT hardcode `PORT` — Railway injects `$PORT` dynamically.

- [ ] **Step 2: Verify the file exists and is valid TOML**

```bash
cat helios-app/backend/railway.toml
```

Expected: the three sections shown above.

- [ ] **Step 3: Commit**

```bash
git add backend/railway.toml
git commit -m "chore: add Railway deployment config"
```

---

## Task 7: Frontend useAI.ts — auth branch for authenticated users

When the user is authenticated AND `VITE_BACKEND_URL` is set, `sendMessage` routes to the FastAPI backend. Otherwise (guest), the existing direct LLM code path runs unchanged.

The function signature gains an optional `sessionId` parameter. The return type gains `sessionId?: string`.

**Files:**
- Modify: `src/composables/useAI.ts`

- [ ] **Step 1: Read the current useAI.ts**

Read `src/composables/useAI.ts` — focus on the imports (lines 1–8), the `useAI()` function signature (line 51), and the `sendMessage` signature (lines ~168–180).

- [ ] **Step 2: Add new imports at the top of useAI.ts**

Add after the existing imports (after line 8):

```typescript
import { useAuthStore } from '@/stores/auth'
import { useGeoStore }  from '@/stores/geo'
```

Note: `useGeoStore` is already used inside `sendMessage` — confirm it's in the existing imports or add it. If it's already imported, skip adding it.

- [ ] **Step 3: Update the AIResponse interface**

Add `sessionId` to the return type. Find the `AIResponse` interface (lines 12–15) and extend the return type of `sendMessage`. The cleanest approach — add a local type for the backend response:

```typescript
// After the existing AIResponse interface:
export interface BackendAIResponse extends AIResponse {
  sessionId?: string
}
```

- [ ] **Step 4: Update sendMessage signature**

Find the `sendMessage` function signature inside `useAI()` and update it to:

```typescript
async function sendMessage(
  userMessage: string,
  provider: string,
  apiKey: string,
  conversationHistory: ClaudeMessage[] = [],
  sessionId?: string,
): Promise<BackendAIResponse> {
```

- [ ] **Step 5: Add the auth branch at the top of sendMessage**

Add this block as the FIRST thing inside `sendMessage` (before any existing logic):

```typescript
// Authenticated path — route through backend
const auth = useAuthStore()
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

if (auth.isAuthenticated && auth.session && BACKEND_URL) {
  const geo = useGeoStore()
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

// Guest path — direct LLM call (existing logic below, unchanged)
```

- [ ] **Step 6: Update return statement**

The existing `return { message, visualCards }` at the end of `sendMessage` needs to match `BackendAIResponse`:

```typescript
return { message, visualCards }
// becomes:
return { message, visualCards, sessionId: undefined }
```

(The guest path doesn't produce a sessionId.)

- [ ] **Step 7: Run TypeScript check**

```bash
cd helios-app
npm run build 2>&1 | head -40
```

Expected: no TypeScript errors in `useAI.ts`. (Build may fail elsewhere if VITE_BACKEND_URL is not set yet — that's fine for this task.)

- [ ] **Step 8: Commit**

```bash
git add src/composables/useAI.ts
git commit -m "feat: useAI.ts auth branch routes authenticated users through backend"
```

---

## Task 8: Frontend ChatInterface.vue — session tracking + endSession

`ChatInterface.vue` needs:
1. A `sessionId` ref to store the session_id returned by the first backend response
2. `onMessageReceived` — called after each message to store sessionId and reset inactivity timer
3. `endSession` — POST to `/api/chat/end-session`, clears sessionId immediately to prevent double-call
4. Inactivity timer: 10-min timeout that fires `endSession`
5. `onUnmounted` hook: clears timer + calls `endSession`

**Files:**
- Modify: `src/components/ChatInterface.vue`

- [ ] **Step 1: Read ChatInterface.vue script setup**

Read `src/components/ChatInterface.vue` lines 1–120. Note the existing imports, state declarations, and the `sendMessage` function signature.

- [ ] **Step 2: Add new imports and state at the top of script setup**

After the existing imports (after line 7), add:

```typescript
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
```

(Replace the existing `vue` import line if `onUnmounted` is not already imported.)

After the existing state declarations (after the `const inputRef` line), add:

```typescript
const auth = useAuthStore()
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

const sessionId = ref<string | null>(null)
let inactivityTimer: ReturnType<typeof setTimeout> | null = null
```

- [ ] **Step 3: Add endSession function**

Add before the existing `sendMessage` function:

```typescript
async function endSession() {
  // Guard: clear immediately to prevent double-call (inactivity + unmount racing)
  if (!sessionId.value || !BACKEND_URL) return
  const id = sessionId.value
  sessionId.value = null
  if (!auth.isAuthenticated || !auth.session) return
  fetch(`${BACKEND_URL}/api/chat/end-session?session_id=${id}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${auth.session.access_token}` },
  }).catch(() => {})  // fire-and-forget, never block unmount
}
```

- [ ] **Step 4: Add onUnmounted hook**

Add after `onMounted`:

```typescript
onUnmounted(() => {
  if (inactivityTimer) clearTimeout(inactivityTimer)
  endSession()
})
```

- [ ] **Step 5: Update sendMessage to capture sessionId and reset inactivity timer**

Find the line in `sendMessage` where the AI response is applied to the chat (after `chat.finalizeMessage` or equivalent). After that line add:

```typescript
// Capture session_id from backend response (first message only for guest)
if (response.sessionId) {
  sessionId.value = response.sessionId
}
// Reset 10-min inactivity timer on every message
if (BACKEND_URL && auth.isAuthenticated) {
  if (inactivityTimer) clearTimeout(inactivityTimer)
  inactivityTimer = setTimeout(endSession, 10 * 60 * 1000)
}
```

- [ ] **Step 6: Pass sessionId into ai.sendMessage call**

Find the `ai.sendMessage(...)` call inside `sendMessage`. Add `sessionId.value ?? undefined` as the 5th argument:

```typescript
// Before:
const response = await ai.sendMessage(text, provider, apiKey, history)
// After:
const response = await ai.sendMessage(text, provider, apiKey, history, sessionId.value ?? undefined)
```

- [ ] **Step 7: TypeScript check**

```bash
npm run build 2>&1 | head -40
```

Expected: no new TypeScript errors in `ChatInterface.vue`.

- [ ] **Step 8: Commit**

```bash
git add src/components/ChatInterface.vue
git commit -m "feat: ChatInterface.vue session tracking + endSession on unmount/inactivity"
```

---

## Task 9: Frontend .env — add VITE_BACKEND_URL

**Files:**
- Modify: `.env`

- [ ] **Step 1: Add VITE_BACKEND_URL to .env**

Open `helios-app/.env` and add at the end:

```
VITE_BACKEND_URL=http://localhost:8001
```

For production deployment, this will be updated to the Railway URL (e.g., `https://helios-backend.up.railway.app`) in the Vercel dashboard env vars. Do NOT commit the production URL to the repo.

- [ ] **Step 2: Verify the dev server builds without errors**

```bash
cd helios-app
npm run dev
```

Open browser to `http://localhost:5173`. Navigate to the chat page. Open DevTools → Network tab. Log in with a test account. Send a message — verify the request goes to `http://localhost:8001/api/chat/send` (not directly to the LLM provider). Verify the response includes `session_id`.

- [ ] **Step 3: Verify guest path is unchanged**

Log out. Send a chat message as a guest user. In DevTools Network tab, verify the request goes directly to the LLM provider API (e.g., `api.deepinfra.com`), NOT to `localhost:8001`.

- [ ] **Step 4: Commit**

```bash
git add .env
git commit -m "chore: add VITE_BACKEND_URL for backend routing"
```

---

## Verification Checklist

After all tasks are complete:

1. **Backend startup**: `uvicorn main:app` starts without errors, `[helios] Supabase client initialized` in logs
2. **Health check**: `GET /api/health` → `{"status":"ok"}`
3. **Authenticated chat**: Log in → send a message → Network tab shows `POST /api/chat/send` → response includes `session_id` → `chat_sessions` row appears in Supabase table editor
4. **Message persistence**: After sending, `chat_messages` table in Supabase has 2 rows (user + assistant) for the session
5. **Memory injection**: `GET /api/chat/memory` returns the user's markdown memory (may be default template on first use)
6. **Session end**: Unmount chat (navigate away) → `POST /api/chat/end-session` fires in DevTools → `chat_sessions.ended_at` is set in Supabase
7. **Hermes trigger**: Send 2+ exchanges (≥ 4 messages) then end session → `chat_sessions.hermes_processed` becomes `true` (may take 15–30 seconds for LLM to run). Verify with: `SELECT id, hermes_processed FROM chat_sessions WHERE user_id = '<your_user_id>' ORDER BY started_at DESC LIMIT 1;`
8. **Guest path unchanged**: Logged-out user → chat goes directly to LLM provider, no backend call
9. **Rate limiting intact**: Shared key usage still in-memory (no regression)
10. **pytest**: `python -m pytest backend/memory/test_memory_service.py -v` → 3 PASSED
