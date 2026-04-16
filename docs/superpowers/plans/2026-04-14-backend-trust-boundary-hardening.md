# Backend Trust-Boundary Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move public third-party data fetches behind HELIOS backend routes, add durable cache and shared-key quota state in Supabase, and make chat session shutdown idempotent.

**Architecture:** Add a small public backend proxy layer with Supabase-backed cache rows, then switch the frontend stores to consume those proxy routes instead of third-party APIs directly. Replace in-memory shared-key tracking and duplicate-prone session shutdown logic with Supabase-backed state transitions so behavior survives restart and multi-instance deployment.

**Tech Stack:** FastAPI, Supabase Python client, Supabase SQL schema migration, httpx, Vue 3, Pinia, Vitest, pytest

---

## File Map

**Backend**

- Modify: `backend/schema.sql`
  - Add `public_api_cache`, `shared_llm_usage`, and `chat_sessions.hermes_processing`.
- Modify: `backend/config.py`
  - Add backend-only upstream token config and TTL settings.
- Modify: `backend/main.py`
  - Register the new public router.
- Create: `backend/public/router.py`
  - Public backend endpoints for environment, AQI, and DONKI summary.
- Create: `backend/public/cache_service.py`
  - Shared cache helpers and upstream fetch normalization.
- Modify: `backend/chat/router.py`
  - Durable shared quota checks and idempotent `end-session`.
- Test: `backend/tests/test_public_routes.py`
  - Public route validation, cache hit/stale refresh behavior.
- Test: `backend/tests/test_chat_session_hardening.py`
  - Shared-key quota persistence and duplicate `end-session` protection.

**Frontend**

- Create: `src/lib/publicApi.ts`
  - Small fetch helper for public backend routes.
- Modify: `src/stores/environment.ts`
  - Replace AQICN direct fetch with backend proxy calls.
- Modify: `src/stores/donki.ts`
  - Replace NASA DONKI direct fetch with backend proxy calls.
- Test: `src/lib/publicApi.test.ts`
  - Backend route fetch helper coverage.
- Test: `src/stores/environment.test.ts`
  - Environment store uses backend route payloads correctly.
- Test: `src/stores/donki.test.ts`
  - DONKI store uses backend route payloads correctly.

## Task 1: Add Durable Schema And Config Primitives

**Files:**
- Modify: `backend/schema.sql`
- Modify: `backend/config.py`

- [ ] **Step 1: Write the failing schema/config expectations as a checklist in comments before editing**

Add this checklist near the top of `backend/schema.sql` and `backend/config.py` while editing so the scope stays explicit:

```sql
-- trust-boundary hardening checklist:
-- 1. add public_api_cache
-- 2. add shared_llm_usage
-- 3. add chat_sessions.hermes_processing
```

```python
# trust-boundary hardening checklist:
# 1. backend-only AQI/NASA tokens
# 2. public cache TTLs
# 3. anonymous public route throttles
```

- [ ] **Step 2: Add the schema changes in `backend/schema.sql`**

Append these SQL blocks after the existing `chat_sessions` definition and before RLS policies:

```sql
ALTER TABLE public.chat_sessions
  ADD COLUMN IF NOT EXISTS hermes_processing BOOLEAN DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS public.public_api_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    cache_key TEXT NOT NULL,
    payload JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, cache_key)
);

CREATE INDEX IF NOT EXISTS idx_public_api_cache_lookup
  ON public.public_api_cache(source, cache_key, expires_at);

CREATE TABLE IF NOT EXISTS public.shared_llm_usage (
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    usage_date DATE NOT NULL,
    count INT NOT NULL DEFAULT 0 CHECK (count >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, usage_date)
);
```

Also enable RLS and add direct owner access for the usage table, plus service-role-only semantics for cache rows:

```sql
ALTER TABLE public.public_api_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shared_llm_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY shared_usage_own_data ON public.shared_llm_usage
FOR ALL USING (auth.uid() = user_id);

CREATE POLICY public_api_cache_no_direct_access ON public.public_api_cache
FOR ALL USING (false);
```

- [ ] **Step 3: Add backend config values in `backend/config.py`**

Add these settings below the existing shared-key and CORS config:

```python
NASA_API_KEY = os.environ.get("NASA_API_KEY", os.environ.get("VITE_NASA_API_KEY", "DEMO_KEY"))
AQICN_TOKEN = os.environ.get("AQICN_TOKEN", os.environ.get("VITE_AQICN_TOKEN", ""))

PUBLIC_ENVIRONMENT_CACHE_TTL_SECONDS = int(os.environ.get("PUBLIC_ENVIRONMENT_CACHE_TTL_SECONDS", "600"))
PUBLIC_AQI_CACHE_TTL_SECONDS = int(os.environ.get("PUBLIC_AQI_CACHE_TTL_SECONDS", "300"))
PUBLIC_DONKI_CACHE_TTL_SECONDS = int(os.environ.get("PUBLIC_DONKI_CACHE_TTL_SECONDS", "600"))
PUBLIC_ROUTE_WINDOW_SECONDS = int(os.environ.get("PUBLIC_ROUTE_WINDOW_SECONDS", "60"))
PUBLIC_ROUTE_MAX_REQUESTS = int(os.environ.get("PUBLIC_ROUTE_MAX_REQUESTS", "60"))
```

- [ ] **Step 4: Sanity-check the edited files**

Run:

```bash
python -m py_compile backend/config.py
```

Expected: no output

- [ ] **Step 5: Commit**

```bash
git add backend/schema.sql backend/config.py
git commit -m "backend: add durable trust-boundary schema primitives"
```

## Task 2: Build Public Cache Service And Public Proxy Routes

**Files:**
- Create: `backend/public/cache_service.py`
- Create: `backend/public/router.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_public_routes.py`

- [ ] **Step 1: Write the failing backend tests**

Create `backend/tests/test_public_routes.py` with focused coverage for validation and cache behavior:

```python
from datetime import datetime, UTC, timedelta
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from backend.public.router import router as public_router


def build_app():
    app = FastAPI()
    app.include_router(public_router, prefix="/api/public")
    app.state.supabase = MagicMock()
    return app


def test_environment_rejects_invalid_lat():
    client = TestClient(build_app())
    response = client.get("/api/public/environment?lat=999&lng=88")
    assert response.status_code == 422


def test_aqi_returns_cached_payload_without_upstream_fetch(monkeypatch):
    app = build_app()
    cache_row = {
        "payload": {"aqi": 42, "label": "Good"},
        "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
    }
    app.state.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[cache_row])
    monkeypatch.setattr("backend.public.cache_service.fetch_aqi_upstream", AsyncMock())
    client = TestClient(app)

    response = client.get("/api/public/aqi?lat=22.5&lng=88.3")

    assert response.status_code == 200
    assert response.json()["aqi"] == 42
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest backend/tests/test_public_routes.py -q
```

Expected: FAIL because `backend.public.router` does not exist yet.

- [ ] **Step 3: Create `backend/public/cache_service.py`**

Create a focused service with cache lookup/save helpers and upstream normalizers:

```python
from datetime import datetime, UTC, timedelta
from typing import Any

import httpx


def cache_key_for_coords(lat: float, lng: float) -> str:
    return f"{lat:.3f}:{lng:.3f}"


async def read_cache(db, source: str, cache_key: str) -> dict[str, Any] | None:
    result = db.table("public_api_cache").select("payload, expires_at").eq("source", source).eq("cache_key", cache_key).execute()
    if not result.data:
        return None
    row = result.data[0]
    if datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) <= datetime.now(UTC):
        return None
    return row["payload"]


def write_cache(db, source: str, cache_key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
    now = datetime.now(UTC)
    db.table("public_api_cache").upsert({
        "source": source,
        "cache_key": cache_key,
        "payload": payload,
        "fetched_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat(),
    }, on_conflict="source,cache_key").execute()
```

Add upstream helpers for Open-Meteo, AQICN, and DONKI summary in the same file. Keep them normalization-only.

- [ ] **Step 4: Create `backend/public/router.py` and register it**

Create the public router with bounded query validation and cache-first flow:

```python
from fastapi import APIRouter, HTTPException, Query, Request

from backend.config import (
    PUBLIC_AQI_CACHE_TTL_SECONDS,
    PUBLIC_DONKI_CACHE_TTL_SECONDS,
    PUBLIC_ENVIRONMENT_CACHE_TTL_SECONDS,
)
from backend.public.cache_service import (
    cache_key_for_coords,
    read_cache,
    write_cache,
    fetch_environment_upstream,
    fetch_aqi_upstream,
    fetch_donki_summary_upstream,
)

router = APIRouter()


@router.get("/environment")
async def get_environment(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    request: Request = None,
):
    db = request.app.state.supabase
    key = cache_key_for_coords(lat, lng)
    cached = await read_cache(db, "environment", key)
    if cached:
        return cached
    payload = await fetch_environment_upstream(lat, lng)
    write_cache(db, "environment", key, payload, PUBLIC_ENVIRONMENT_CACHE_TTL_SECONDS)
    return payload
```

In `backend/main.py`, register the router:

```python
from backend.public.router import router as public_router
app.include_router(public_router, prefix="/api/public", tags=["public"])
```

- [ ] **Step 5: Re-run tests and commit**

Run:

```bash
python -m pytest backend/tests/test_public_routes.py -q
```

Expected: PASS

Then commit:

```bash
git add backend/public/cache_service.py backend/public/router.py backend/main.py backend/tests/test_public_routes.py
git commit -m "backend: add cached public data proxy routes"
```

## Task 3: Replace Shared-Key Memory State And Harden `end-session`

**Files:**
- Modify: `backend/chat/router.py`
- Test: `backend/tests/test_chat_session_hardening.py`

- [ ] **Step 1: Write the failing backend tests**

Create `backend/tests/test_chat_session_hardening.py`:

```python
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from backend.auth import supabase_auth
from backend.chat.router import router as chat_router


def build_app():
    app = FastAPI()
    app.include_router(chat_router, prefix="/api/chat")
    app.dependency_overrides[supabase_auth.get_current_user] = lambda: "user-123"
    app.state.supabase = MagicMock()
    app.state.memory_service = SimpleNamespace(get_memory_for_prompt=AsyncMock(return_value=""), process_session=AsyncMock())
    return app


def test_shared_usage_is_read_from_db_not_memory(monkeypatch):
    app = build_app()
    client = TestClient(app)
    app.state.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[{"count": 20}])

    response = client.post("/api/chat/send", json={
        "message": "hello",
        "context": {"lat": 1.0, "lng": 2.0, "timezone": "UTC"},
        "history": [],
    })

    assert response.status_code == 429
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest backend/tests/test_chat_session_hardening.py -q
```

Expected: FAIL because the current router still uses `_shared_key_usage`.

- [ ] **Step 3: Replace in-memory shared quota with Supabase-backed helpers**

In `backend/chat/router.py`, remove `_shared_key_usage`, `_check_shared_rate_limit`, and `_increment_shared_usage`. Replace them with durable helpers:

```python
def _shared_usage_date() -> str:
    return datetime.now(UTC).date().isoformat()


def _get_or_create_shared_usage(db, user_id: str) -> dict:
    usage_date = _shared_usage_date()
    existing = db.table("shared_llm_usage").select("count").eq("user_id", user_id).eq("usage_date", usage_date).execute()
    if existing.data:
        return existing.data[0]
    db.table("shared_llm_usage").upsert({
        "user_id": user_id,
        "usage_date": usage_date,
        "count": 0,
    }, on_conflict="user_id,usage_date").execute()
    return {"count": 0}


def _increment_shared_usage(db, user_id: str) -> int:
    usage_date = _shared_usage_date()
    current = _get_or_create_shared_usage(db, user_id)["count"]
    next_count = current + 1
    db.table("shared_llm_usage").upsert({
        "user_id": user_id,
        "usage_date": usage_date,
        "count": next_count,
        "updated_at": datetime.now(UTC).isoformat(),
    }, on_conflict="user_id,usage_date").execute()
    return next_count
```

Then gate shared-key flow with `supabase` instead of process memory.

- [ ] **Step 4: Make `end-session` idempotent**

Update the session shutdown path to use `hermes_processing`:

```python
session_result = supabase.table("chat_sessions").select("provider, encrypted_api_key, ended_at, hermes_processed, hermes_processing").eq("id", session_id).eq("user_id", user_id).execute()

if session_row.get("hermes_processed") or session_row.get("hermes_processing"):
    return {"status": "already_processing", "session_id": session_id}

update_payload = {"ended_at": datetime.now(UTC).isoformat()}
if message_count >= 4:
    update_payload["hermes_processing"] = True

supabase.table("chat_sessions").update(update_payload).eq("id", session_id).eq("user_id", user_id).is_("ended_at", "null").execute()
```

Only queue Hermes after the guarded update succeeds. If no row was updated, return `already_ended` or `already_processing`.

- [ ] **Step 5: Re-run tests and commit**

Run:

```bash
python -m pytest backend/tests/test_chat_session_hardening.py backend/tests/test_chat_security.py -q
```

Expected: PASS

Then commit:

```bash
git add backend/chat/router.py backend/tests/test_chat_session_hardening.py
git commit -m "backend: persist shared chat quota and harden session shutdown"
```

## Task 4: Switch Frontend Stores To HELIOS Public Routes

**Files:**
- Create: `src/lib/publicApi.ts`
- Modify: `src/stores/environment.ts`
- Modify: `src/stores/donki.ts`
- Test: `src/lib/publicApi.test.ts`
- Test: `src/stores/environment.test.ts`
- Test: `src/stores/donki.test.ts`

- [ ] **Step 1: Write the failing frontend tests**

Create `src/lib/publicApi.test.ts`:

```ts
import { describe, expect, it, vi } from 'vitest'
import { fetchPublicJson } from './publicApi'

describe('fetchPublicJson', () => {
  it('uses the backend public route base url', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ ok: true }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await fetchPublicJson('/environment?lat=1&lng=2')

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/public/environment?lat=1&lng=2'),
      expect.any(Object)
    )
  })
})
```

Create `src/stores/environment.test.ts` and `src/stores/donki.test.ts` with mocked backend responses and assertions on store state.

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
npm run test -- src/lib/publicApi.test.ts src/stores/environment.test.ts src/stores/donki.test.ts
```

Expected: FAIL because the helper and tests do not exist yet.

- [ ] **Step 3: Create the backend route fetch helper**

Create `src/lib/publicApi.ts`:

```ts
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL as string | undefined

export async function fetchPublicJson(path: string) {
  if (!BACKEND_URL) {
    throw new Error('Public backend URL not configured')
  }

  const response = await fetch(`${BACKEND_URL}/api/public${path}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Public backend error ${response.status}`)
  }

  return response.json()
}
```

- [ ] **Step 4: Update the stores to use HELIOS backend routes**

In `src/stores/environment.ts`, replace the third-party fetches with backend route calls:

```ts
import { fetchPublicJson } from '@/lib/publicApi'

async function fetchAll(lat: number, lng: number): Promise<void> {
  loading.value = true
  error.value = null

  try {
    const data = await fetchPublicJson(`/environment?lat=${lat}&lng=${lng}`)
    uvIndexNow.value = data.uvIndexNow ?? 0
    uvIndexMax.value = data.uvIndexMax ?? 0
    temperatureNow.value = data.temperatureNow ?? 0
    temperatureNight.value = data.temperatureNight ?? 0
    humidity.value = data.humidity ?? 0
    sunshineDurationMin.value = data.sunshineDurationMin ?? 0
    aqiLevel.value = data.aqiLevel ?? 0
    aqiLabel.value = data.aqiLabel ?? 'Unknown'
    pm25.value = data.pm25 ?? 0
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}
```

In `src/stores/donki.ts`, replace direct NASA calls with:

```ts
import { fetchPublicJson } from '@/lib/publicApi'

async function fetchAll(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const data = await fetchPublicJson('/donki/summary')
    upcomingCMEs.value = data.upcomingCMEs ?? []
    recentStorms.value = data.recentStorms ?? []
    activeFlares.value = data.activeFlares ?? []
    notifications.value = data.notifications ?? []
    nextGeostormEta.value = data.nextGeostormEta ?? null
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}
```

- [ ] **Step 5: Re-run frontend tests and commit**

Run:

```bash
npm run test -- src/lib/publicApi.test.ts src/stores/environment.test.ts src/stores/donki.test.ts
```

Expected: PASS

Then commit:

```bash
git add src/lib/publicApi.ts src/lib/publicApi.test.ts src/stores/environment.ts src/stores/environment.test.ts src/stores/donki.ts src/stores/donki.test.ts
git commit -m "frontend: route public data stores through backend proxies"
```

## Task 5: Final Verification And Integration Check

**Files:**
- Modify: none expected
- Verify: backend and frontend touched above

- [ ] **Step 1: Run backend verification**

Run:

```bash
python -m pytest backend/tests/test_public_routes.py backend/tests/test_chat_session_hardening.py backend/tests/test_chat_security.py -q
```

Expected: PASS

- [ ] **Step 2: Run frontend verification**

Run:

```bash
npm run test -- src/lib/publicApi.test.ts src/stores/environment.test.ts src/stores/donki.test.ts
```

Expected: PASS

- [ ] **Step 3: Run production build**

Run:

```bash
npm run build
```

Expected: PASS

- [ ] **Step 4: Check working tree**

Run:

```bash
git status --short
```

Expected: only intentional files from this plan, or a clean tree after commits.

- [ ] **Step 5: Final commit if needed**

If any final integration fix was required:

```bash
git add backend/schema.sql backend/config.py backend/public/router.py backend/public/cache_service.py backend/chat/router.py backend/tests/test_public_routes.py backend/tests/test_chat_session_hardening.py src/lib/publicApi.ts src/lib/publicApi.test.ts src/stores/environment.ts src/stores/environment.test.ts src/stores/donki.ts src/stores/donki.test.ts
git commit -m "security: harden backend trust boundary for public data and shared chat usage"
```

## Self-Review

Spec coverage:

- Public backend proxy routes: covered in Task 2 and Task 4.
- Supabase-backed public cache: covered in Task 1 and Task 2.
- Durable shared-key quota: covered in Task 1 and Task 3.
- Idempotent `end-session`: covered in Task 1 and Task 3.
- Verification requirements: covered in Task 5.

Placeholder scan:

- No `TODO`, `TBD`, or "handle appropriately" placeholders remain.
- All file paths are explicit.
- All code-changing steps include concrete code blocks.

Type consistency:

- Public route base path is consistently `/api/public`.
- Cache table is consistently `public_api_cache`.
- Shared quota table is consistently `shared_llm_usage`.
- Session-processing field is consistently `hermes_processing`.
