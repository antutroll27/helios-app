# HTTP-Only Backend Session Refactor Design

## Goal

Move HELIOS from browser-readable Supabase bearer sessions to a backend-owned `httpOnly` session model so frontend JavaScript no longer holds the main authentication secret.

This refactor is intended to be the last major security architecture step after:

- science/algo credibility hardening
- chat/input/rendering hardening
- backend trust-boundary hardening
- session exposure reduction in the auth store

The target is a materially safer production posture for a health-adjacent product.

## Positioning

HELIOS will continue to use Supabase for identity and data, but Supabase client auth will no longer be the browser-facing source of truth for the app session.

The new trust boundary is:

- browser -> HELIOS backend session cookie
- HELIOS backend -> Supabase identity/data operations

This means:

- browser JavaScript no longer reads bearer tokens for normal app auth
- backend routes authenticate from a cookie-backed server session
- XSS impact is reduced because the primary session secret is `httpOnly`

## Approaches Considered

### 1. Full backend-owned auth session

Browser signs in through HELIOS backend. Backend authenticates with Supabase, creates an app session, and sets an `httpOnly` cookie.

Pros:

- strongest security improvement
- cleanest long-term architecture
- removes browser token handling as the normal auth primitive

Cons:

- broader refactor
- requires backend auth endpoints and session storage
- requires careful cookie/CSRF handling

### 2. Hybrid transition

Keep Supabase client auth temporarily, but also issue backend sessions and gradually migrate routes.

Pros:

- smoother transition
- smaller immediate frontend disruption

Cons:

- two auth models at once
- more complexity
- easy to get wrong and leave half-migrated trust boundaries

### 3. Token wrapping only

Keep current frontend auth model and just add more backend indirection.

Pros:

- smallest change

Cons:

- does not solve the main problem
- browser still owns the main auth secret

## Recommendation

Use **Approach 1: full backend-owned auth session**.

This is the only approach that actually closes the main browser-token exposure problem instead of partially masking it.

## Target Architecture

### Session boundary

HELIOS backend becomes the application auth boundary.

Supabase remains:

- identity provider
- auth user store
- database layer

Browser becomes:

- a consumer of backend auth state
- not the holder of the primary auth secret

### Cookie model

Backend sets an opaque session cookie:

- name: `helios_session`
- value: opaque session identifier or signed reference
- flags:
  - `HttpOnly`
  - `Secure`
  - `SameSite=Lax`
  - `Path=/`

The cookie must not contain a raw Supabase access token.

### Server-side session state

Session state should live in Postgres/Supabase and include:

- `id`
- `user_id`
- `created_at`
- `expires_at`
- `rotated_at`
- `revoked_at`
- optional:
  - `ip_hash`
  - `user_agent_hash`
  - `last_seen_at`

The backend uses this record to authenticate requests and revoke sessions cleanly.

## Backend Design

### New auth endpoints

Add backend auth routes:

- `POST /api/auth/login`
  - accepts email/password
  - authenticates against Supabase
  - creates HELIOS session
  - sets cookie

- `POST /api/auth/signup`
  - creates account
  - may issue a session immediately if confirmation rules allow it
  - otherwise returns a confirmation-required state

- `POST /api/auth/logout`
  - revokes HELIOS session
  - clears cookie

- `GET /api/auth/me`
  - resolves cookie session
  - returns authenticated user/profile state

Optional later:

- `POST /api/auth/refresh`
- `POST /api/auth/change-password`

### Backend auth dependency

Protected routes should authenticate from the `helios_session` cookie by default.

Expected flow:

1. read cookie
2. resolve server session
3. verify not expired/revoked
4. load `user_id`

For migration safety, the old bearer-token path may remain temporarily, but browser code should stop relying on it once the refactor lands.

### Session service

Add a dedicated backend session service responsible for:

- issuing session ids
- hashing or signing identifiers if needed
- storing session rows
- reading current session
- revoking session
- rotating expiry or session identity when appropriate

This should be isolated from route code so the auth boundary stays understandable and testable.

## Frontend Design

### Auth store

Frontend auth state should move from:

- “hold the Supabase session and read access tokens”

to:

- “ask the backend who the current user is”

The auth store should:

- call `POST /api/auth/login`
- call `POST /api/auth/logout`
- call `GET /api/auth/me`
- use `credentials: 'include'`
- treat backend session state as the source of truth

### Protected API calls

Frontend calls to HELIOS backend should stop attaching bearer tokens from JavaScript and instead use cookie-backed requests:

- `credentials: 'include'`

This affects:

- chat send/end-session/history/memory routes
- any future user-scoped backend routes

### Supabase client usage

Direct Supabase client auth should be removed from the normal user auth flow.

If the Supabase client remains in the frontend for any reason, it must not remain the app’s main authenticated session path.

## CSRF and Cookie Security

Cookie auth requires CSRF attention.

Minimum acceptable baseline in this refactor:

- `SameSite=Lax`
- strict `CORS_ORIGINS`
- mutating auth-sensitive routes protected by CSRF token or equivalent server-side validation

This work must not rely on `httpOnly` alone and call the job done.

## Files Likely In Scope

### Backend

- `backend/main.py`
- `backend/config.py`
- `backend/schema.sql`
- `backend/auth/supabase_auth.py`
- new:
  - `backend/auth/router.py`
  - `backend/auth/session_service.py`

### Frontend

- `src/stores/auth.ts`
- `src/lib/supabase.ts`
- `src/composables/useAI.ts`
- `src/components/ChatInterface.vue`
- auth page / onboarding auth calls

### Tests

- backend auth/session tests
- frontend auth store tests
- integration checks for cookie-backed protected calls

## Rollout Strategy

1. Add backend session schema and session service.
2. Add backend auth routes: `login`, `logout`, `me`.
3. Update frontend auth store to use backend auth routes.
4. Switch protected backend calls to `credentials: 'include'`.
5. Remove normal frontend dependence on browser-readable Supabase auth session.
6. Keep any compatibility shim temporary and explicit, then remove it.

## Success Criteria

- browser JavaScript no longer needs to read auth bearer tokens for normal app auth
- backend protected routes can authenticate from `httpOnly` cookie sessions
- login/logout/me works end to end
- chat still works without frontend bearer-token injection
- tests pass
- build passes
- no broad auth UX regression

## Out of Scope

- science/model changes
- unrelated UI redesign
- broad backend refactors unrelated to auth/session boundary
- non-auth public route redesign

## Risks

- cookie + CSRF handling can be implemented incorrectly if rushed
- Supabase integration details may require a specific login/signup shape
- migration must avoid a half-client-auth / half-server-auth state becoming permanent

## Decision

Proceed with a full backend-owned `httpOnly` session refactor, using HELIOS backend as the auth boundary and Supabase as the identity/data backend.
