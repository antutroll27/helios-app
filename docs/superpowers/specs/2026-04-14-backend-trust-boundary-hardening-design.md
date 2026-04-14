# Backend Trust-Boundary Hardening

## Summary

HELIOS currently exposes third-party data-source tokens in the browser, tracks shared LLM usage in process memory, and handles chat session shutdown in a way that can queue duplicate Hermes work. This spec hardens those trust boundaries without dragging full auth/session redesign into the same pass.

The goal is to move public data fetches behind HELIOS backend routes, add durable caching and shared-key quota tracking in Supabase, and make `end-session` idempotent. The product surface should remain materially the same to users.

## Goals

- Remove browser dependence on `VITE_AQICN_TOKEN` and `VITE_NASA_API_KEY`.
- Serve AQI, DONKI, and environment data through public HELIOS backend routes.
- Add Supabase-backed cache rows so public routes can be cache-first and near-real-time.
- Replace in-memory shared-key quota tracking with durable Supabase-backed counters.
- Prevent duplicate `end-session` requests from queueing duplicate Hermes processing.
- Keep frontend store behavior close to current behavior so the UX does not regress.

## Non-Goals

- Full auth/session architecture redesign.
- Replacing Supabase Auth with cookie-backed backend sessions.
- Broad frontend redesign.
- Research/model changes.
- Full anonymous abuse-prevention perimeter beyond practical cache-first throttling.

## Desired Outcome

After this pass:

- Browsers call HELIOS backend routes for AQI, DONKI, and environment data.
- Real third-party API tokens are no longer required in client code for those flows.
- Shared AI daily limits survive backend restarts and multiple instances.
- Session shutdown becomes safe to call multiple times.
- Existing homepage/chat/environment features continue working with minimal frontend churn.

## Architecture

### 1. Public Backend Proxy Routes

Add a backend router for public data fetches. These routes remain unauthenticated so the app shell can load before sign-in, but they must be cache-first and conservatively rate-limited.

Proposed routes:

- `GET /api/public/environment?lat=<lat>&lng=<lng>`
- `GET /api/public/aqi?lat=<lat>&lng=<lng>`
- `GET /api/public/donki/summary`

These routes should return normalized JSON shaped for the existing frontend stores rather than raw upstream payloads.

### 2. Supabase-Backed Public Cache

Add a small cache table for public upstream data.

Suggested shape:

- `source TEXT`
- `cache_key TEXT`
- `payload JSONB`
- `fetched_at TIMESTAMPTZ`
- `expires_at TIMESTAMPTZ`
- unique key on `(source, cache_key)`

Cache TTLs:

- AQI: `5 minutes`
- DONKI summary: `10 minutes`
- Environment snapshot: `10 minutes`

Read path:

1. Normalize request into a stable cache key.
2. Check cache row.
3. If `expires_at > now`, return cached payload.
4. If stale or missing, fetch upstream, update row, return fresh payload.

### 3. Durable Shared LLM Quota

Replace `_shared_key_usage` in `backend/chat/router.py` with a Supabase-backed quota table.

Suggested shape:

- `user_id UUID`
- `usage_date DATE`
- `count INT`
- unique key on `(user_id, usage_date)`

Behavior:

1. Resolve current UTC date.
2. Look up or create today's row.
3. Increment count durably before the shared-key provider call.
4. Reject once `count >= SHARED_LLM_RATE_LIMIT`.

This does not need to become a global billing system. It only needs to be durable, per-user, and restart-safe.

### 4. Idempotent `end-session`

Current `end-session` behavior uses a read-then-update pattern that can race. This pass should turn session ending into a guarded state transition.

Required behavior:

- First valid request marks the session ended.
- If the session is large enough for Hermes learning, only one request may queue processing.
- Repeated requests return an already-ended or already-processing response instead of queueing more work.

Implementation guidance:

- Use `chat_sessions.ended_at`, `chat_sessions.hermes_processed`, and an additional processing marker if needed.
- Prefer one conditional update path over separate read and update steps.
- If a new column is needed, add it explicitly in schema/migration rather than inferring state from timestamps alone.

## Data Model Changes

This pass is allowed to include a small schema migration.

Add:

- `public_api_cache`
- `shared_llm_usage`

Extend if needed:

- `chat_sessions` with a processing state column such as `hermes_processing BOOLEAN DEFAULT FALSE`

The schema change should be minimal and directly tied to this trust-boundary hardening slice.

## Frontend Changes

Frontend scope stays narrow:

- `src/stores/environment.ts` stops calling AQICN directly and uses HELIOS backend routes.
- `src/stores/donki.ts` stops calling NASA DONKI directly and uses HELIOS backend routes.
- Any environment snapshot logic that currently depends on browser-exposed source tokens shifts to backend routes.

The stores should continue exposing the same reactive state shape where possible.

## Abuse Controls

Public routes should not become an uncached pass-through proxy.

This pass should include:

- cache-first behavior as the primary protection
- coarse in-memory request throttling for anonymous public routes
- bounded input validation for `lat` / `lng`
- sane timeout and error handling for upstream fetches

This is sufficient for this slice. More advanced anonymous abuse controls can be a later security pass.

## Verification

Backend verification:

- cache hit vs stale refresh tests
- shared-key durable quota tests
- `end-session` duplicate request protection tests
- public route validation tests

Frontend verification:

- targeted store tests where route behavior changes
- confirm stores still populate expected state from backend responses

Project verification:

- targeted `pytest`
- targeted `vitest`
- `npm run build`

## Success Criteria

- Browser bundles no longer need real AQI/NASA tokens for these routes.
- Public data fetches go through HELIOS backend endpoints.
- Shared-key limits survive restart and multi-instance deployment.
- Duplicate `end-session` requests do not queue duplicate Hermes work.
- Existing user-facing behavior remains materially unchanged.

## Risks and Tradeoffs

- Public routes still require careful caching and throttling because they are unauthenticated.
- Supabase-backed counters and caches introduce operational state, but that is the correct tradeoff because the current in-memory approach is not production-safe.
- This pass improves the backend perimeter substantially, but it does not solve the broader frontend token exposure problem from Supabase sessions. That remains a later auth/session hardening spec.

## Recommendation

Implement this as the next security slice before any wider auth refactor. It removes exposed data-source secrets and closes the most important backend abuse paths while keeping the scope tight enough to execute safely.
