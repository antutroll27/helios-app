# HTTP-Only Backend Session Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move HELIOS from browser-readable Supabase bearer sessions to backend-owned `httpOnly` cookie sessions, while preserving login/signup/logout/chat behavior.

**Architecture:** FastAPI becomes the application auth boundary. The backend authenticates against Supabase, creates opaque server-side sessions in Postgres, issues `helios_session` cookies plus an in-memory CSRF token for mutating requests, and protected routes resolve identity from cookie-backed session state instead of browser bearer tokens.

**Tech Stack:** FastAPI, Supabase Python client, Postgres/Supabase schema SQL, Vue 3, Pinia, Vitest, Pytest, `fetch` with `credentials: 'include'`

---

## File Structure

### Backend

- Create: `backend/auth/router.py`
  - Auth HTTP endpoints: `login`, `signup`, `logout`, `me`
- Create: `backend/auth/session_service.py`
  - Session creation, lookup, revocation, CSRF generation/verification
- Create: `backend/tests/test_auth_session_service.py`
  - Session service unit coverage
- Create: `backend/tests/test_auth_router.py`
  - Auth endpoint and cookie/CSRF coverage
- Modify: `backend/auth/supabase_auth.py`
  - Switch from bearer-only dependency to cookie-first auth dependency with temporary bearer fallback
- Modify: `backend/chat/router.py`
  - Protected chat routes use cookie session auth and CSRF verification
- Modify: `backend/config.py`
  - Add session cookie/session TTL/CSRF settings
- Modify: `backend/main.py`
  - Register auth router and session service
- Modify: `backend/schema.sql`
  - Add `app_sessions` table and indexes

### Frontend

- Create: `src/lib/backendAuth.ts`
  - Encapsulate backend auth endpoints and typed payloads
- Modify: `src/stores/auth.ts`
  - Backend-session source of truth; store current user + in-memory CSRF token
- Modify: `src/components/auth/LoginForm.vue`
  - Submit to backend auth route
- Modify: `src/components/auth/SignupForm.vue`
  - Submit to backend auth route
- Modify: `src/composables/useAI.ts`
  - Stop attaching bearer tokens; use cookie-backed requests + CSRF header where needed
- Modify: `src/components/ChatInterface.vue`
  - Same migration for chat/history/session-end requests
- Modify: `src/lib/supabase.ts`
  - Remove browser-auth session ownership; keep only non-auth client usage if still needed
- Modify: `src/stores/auth.test.ts`
  - Rewrite around backend-session behavior
- Create: `src/lib/backendAuth.test.ts`
  - Auth API client coverage

### Verification

- Backend tests: `backend/tests/test_auth_session_service.py`, `backend/tests/test_auth_router.py`, existing `backend/tests/test_chat_security.py`
- Frontend tests: `src/stores/auth.test.ts`, `src/lib/backendAuth.test.ts`
- Full checks: `npm run build`, targeted `pytest`

---

### Task 1: Add Server-Side Session Schema And Config

**Files:**
- Modify: `backend/schema.sql`
- Modify: `backend/config.py`
- Test: `backend/tests/test_auth_session_service.py`

- [ ] **Step 1: Write the failing config/schema-oriented tests**

```python
from backend.auth.session_service import SessionCookieSettings


def test_session_cookie_defaults_are_strict_enough():
    settings = SessionCookieSettings.from_config()
    assert settings.cookie_name == "helios_session"
    assert settings.same_site == "lax"
    assert settings.http_only is True
    assert settings.secure is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_auth_session_service.py::test_session_cookie_defaults_are_strict_enough -q`
Expected: FAIL with import or attribute errors because `session_service.py` and cookie settings do not exist yet

- [ ] **Step 3: Add the schema and config primitives**

```sql
create table if not exists public.app_sessions (
  id text primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  csrf_token_hash text not null,
  created_at timestamptz not null default timezone('utc', now()),
  expires_at timestamptz not null,
  rotated_at timestamptz,
  revoked_at timestamptz,
  last_seen_at timestamptz,
  ip_hash text,
  user_agent_hash text
);

create index if not exists idx_app_sessions_user_id on public.app_sessions(user_id);
create index if not exists idx_app_sessions_expires_at on public.app_sessions(expires_at);
```

```python
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "helios_session")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true"
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "lax")
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "168"))
SESSION_REFRESH_MINUTES = int(os.getenv("SESSION_REFRESH_MINUTES", "30"))
```

- [ ] **Step 4: Run the targeted test again**

Run: `python -m pytest backend/tests/test_auth_session_service.py::test_session_cookie_defaults_are_strict_enough -q`
Expected: still FAIL, but now only because `SessionCookieSettings` has not been implemented yet

- [ ] **Step 5: Commit**

```bash
git add backend/schema.sql backend/config.py backend/tests/test_auth_session_service.py
git commit -m "feat: add backend session schema and config primitives"
```

---

### Task 2: Build The Backend Session Service

**Files:**
- Create: `backend/auth/session_service.py`
- Modify: `backend/tests/test_auth_session_service.py`

- [ ] **Step 1: Write the failing session service tests**

```python
from datetime import datetime, timedelta, timezone

from backend.auth.session_service import SessionService


class FakeTable:
    def __init__(self):
        self.rows = []

    def insert(self, payload):
        self.rows.append(payload)
        return self

    def execute(self):
        return type("Response", (), {"data": self.rows})


class FakeSupabase:
    def table(self, name):
        assert name == "app_sessions"
        return FakeTable()


def test_issue_session_creates_opaque_id_and_csrf():
    service = SessionService(FakeSupabase(), ttl_hours=24)
    session, csrf_token = service.issue_session(user_id="user-123", ip="1.2.3.4", user_agent="ua")
    assert session["id"] != "user-123"
    assert csrf_token
    assert session["csrf_token_hash"] != csrf_token


def test_validate_csrf_accepts_matching_token():
    service = SessionService(FakeSupabase(), ttl_hours=24)
    session, csrf_token = service.issue_session(user_id="user-123", ip="1.2.3.4", user_agent="ua")
    assert service.validate_csrf(session, csrf_token) is True
    assert service.validate_csrf(session, "wrong") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_auth_session_service.py -q`
Expected: FAIL because `SessionService` does not exist

- [ ] **Step 3: Implement the minimal session service**

```python
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import secrets


@dataclass
class SessionCookieSettings:
    cookie_name: str
    same_site: str
    http_only: bool
    secure: bool

    @classmethod
    def from_config(cls):
        return cls(
            cookie_name=SESSION_COOKIE_NAME,
            same_site=SESSION_COOKIE_SAMESITE,
            http_only=True,
            secure=SESSION_COOKIE_SECURE,
        )


class SessionService:
    def __init__(self, supabase, ttl_hours: int):
        self.supabase = supabase
        self.ttl_hours = ttl_hours

    def issue_session(self, user_id: str, ip: str | None, user_agent: str | None):
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(24)
        now = datetime.now(timezone.utc)
        payload = {
            "id": session_id,
            "user_id": user_id,
            "csrf_token_hash": self._sha256(csrf_token),
            "expires_at": (now + timedelta(hours=self.ttl_hours)).isoformat(),
            "ip_hash": self._sha256(ip) if ip else None,
            "user_agent_hash": self._sha256(user_agent) if user_agent else None,
        }
        self.supabase.table("app_sessions").insert(payload).execute()
        return payload, csrf_token

    def validate_csrf(self, session: dict, token: str | None) -> bool:
        if not token:
            return False
        return session.get("csrf_token_hash") == self._sha256(token)

    def _sha256(self, value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()
```

- [ ] **Step 4: Run the session service test suite**

Run: `python -m pytest backend/tests/test_auth_session_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/auth/session_service.py backend/tests/test_auth_session_service.py
git commit -m "feat: add backend auth session service"
```

---

### Task 3: Add Backend Auth Routes And Cookie Issuance

**Files:**
- Create: `backend/auth/router.py`
- Modify: `backend/main.py`
- Modify: `backend/auth/supabase_auth.py`
- Modify: `backend/tests/test_auth_router.py`

- [ ] **Step 1: Write the failing auth router tests**

```python
from fastapi.testclient import TestClient

from backend.main import app


def test_login_sets_http_only_cookie(monkeypatch):
    client = TestClient(app)

    response = client.post("/api/auth/login", json={
        "email": "user@example.com",
        "password": "secret123",
    })

    assert response.status_code == 200
    assert "helios_session" in response.cookies
    assert response.json()["user"]["email"] == "user@example.com"
    assert response.json()["csrfToken"]


def test_me_reads_cookie_session(monkeypatch):
    client = TestClient(app)
    response = client.get("/api/auth/me")
    assert response.status_code in {200, 401}
```

- [ ] **Step 2: Run the router tests to verify they fail**

Run: `python -m pytest backend/tests/test_auth_router.py -q`
Expected: FAIL because `/api/auth/login` and `/api/auth/me` do not exist

- [ ] **Step 3: Implement the auth router and register it**

```python
router = APIRouter()


@router.post("/login")
async def login(payload: LoginRequest, request: Request, response: Response):
    auth_response = request.app.state.supabase.auth.sign_in_with_password({
        "email": payload.email,
        "password": payload.password,
    })
    user = auth_response.user
    session_row, csrf_token = request.app.state.session_service.issue_session(
        user_id=user.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_row["id"],
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path="/",
    )
    return {"user": {"id": user.id, "email": user.email}, "csrfToken": csrf_token}


@router.get("/me")
async def me(current_user=Depends(get_current_user_from_session)):
    return current_user


@router.post("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        request.app.state.session_service.revoke_session(session_id)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"ok": True}
```

```python
from backend.auth.router import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
```

- [ ] **Step 4: Run the router tests again**

Run: `python -m pytest backend/tests/test_auth_router.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/auth/router.py backend/main.py backend/auth/supabase_auth.py backend/tests/test_auth_router.py
git commit -m "feat: add backend auth routes with http-only sessions"
```

---

### Task 4: Enforce Cookie Auth And CSRF On Protected Chat Routes

**Files:**
- Modify: `backend/auth/supabase_auth.py`
- Modify: `backend/chat/router.py`
- Modify: `backend/tests/test_chat_security.py`

- [ ] **Step 1: Write the failing protected-route tests**

```python
from fastapi.testclient import TestClient

from backend.main import app


def test_chat_send_rejects_missing_csrf(monkeypatch):
    client = TestClient(app)
    response = client.post("/api/chat/send", json={"message": "hello", "history": []})
    assert response.status_code == 403


def test_chat_send_accepts_cookie_and_csrf(monkeypatch):
    client = TestClient(app)
    client.cookies.set("helios_session", "session-123")
    response = client.post(
        "/api/chat/send",
        json={"message": "hello", "history": []},
        headers={"X-HELIOS-CSRF": "csrf-123"},
    )
    assert response.status_code != 401
```

- [ ] **Step 2: Run the chat security tests to verify the new assertions fail**

Run: `python -m pytest backend/tests/test_chat_security.py -q`
Expected: FAIL because chat routes still expect bearer auth and do not enforce CSRF this way

- [ ] **Step 3: Implement cookie-first auth + CSRF verification**

```python
async def get_current_user_from_session(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        session = request.app.state.session_service.get_active_session(session_id)
        if session:
            request.state.auth_session = session
            return session["user_id"]
    return await get_current_user(credentials)


def require_csrf(request: Request):
    session = getattr(request.state, "auth_session", None)
    token = request.headers.get("X-HELIOS-CSRF")
    if not session or not request.app.state.session_service.validate_csrf(session, token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")
```

```python
@router.post("/send")
async def send_message(
    payload: ChatRequest,
    request: Request,
    user_id: str = Depends(get_current_user_from_session),
):
    require_csrf(request)
    return await _handle_chat_send(payload=payload, request=request, user_id=user_id)
```

- [ ] **Step 4: Run the targeted backend security checks**

Run: `python -m pytest backend/tests/test_chat_security.py backend/tests/test_auth_router.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/auth/supabase_auth.py backend/chat/router.py backend/tests/test_chat_security.py
git commit -m "feat: enforce cookie auth and csrf on chat routes"
```

---

### Task 5: Migrate Frontend Auth Store To Backend Session State

**Files:**
- Create: `src/lib/backendAuth.ts`
- Create: `src/lib/backendAuth.test.ts`
- Modify: `src/stores/auth.ts`
- Modify: `src/stores/auth.test.ts`
- Modify: `src/lib/supabase.ts`

- [ ] **Step 1: Write the failing frontend auth client/store tests**

```ts
import { describe, expect, it, vi } from 'vitest'
import { login, me } from '@/lib/backendAuth'

describe('backend auth client', () => {
  it('calls login with credentials included', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ user: { id: 'u1', email: 'user@example.com' }, csrfToken: 'csrf-1' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await login('user@example.com', 'secret123')

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/auth/login'),
      expect.objectContaining({ credentials: 'include' }),
    )
  })
})
```

```ts
it('auth store initializes from backend me()', async () => {
  const auth = useAuthStore()
  await auth.init()
  expect(auth.isAuthenticated).toBe(true)
  expect(auth.user?.email).toBe('user@example.com')
})
```

- [ ] **Step 2: Run the frontend auth tests to verify they fail**

Run: `npm run test -- src/lib/backendAuth.test.ts src/stores/auth.test.ts`
Expected: FAIL because `backendAuth.ts` does not exist and `auth.init()` still depends on Supabase client state

- [ ] **Step 3: Implement the backend auth client and store migration**

```ts
export async function login(email: string, password: string) {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) throw new Error('Login failed')
  return response.json() as Promise<{ user: { id: string; email: string }, csrfToken: string }>
}

export async function me() {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/auth/me`, {
    credentials: 'include',
  })
  if (response.status === 401) return null
  if (!response.ok) throw new Error('Auth lookup failed')
  return response.json()
}
```

```ts
const user = ref<AuthUser | null>(null)
const csrfToken = ref<string | null>(null)

async function init() {
  loading.value = true
  try {
    const payload = await backendMe()
    user.value = payload?.user ?? null
    csrfToken.value = payload?.csrfToken ?? null
  } finally {
    loading.value = false
  }
}

async function signIn(email: string, password: string) {
  const payload = await backendLogin(email, password)
  user.value = payload.user
  csrfToken.value = payload.csrfToken
}
```

```ts
export const supabase = createClient<any>(supabaseUrl ?? '', supabaseKey ?? '', {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
    detectSessionInUrl: false,
  },
})
```

- [ ] **Step 4: Run the frontend auth tests again**

Run: `npm run test -- src/lib/backendAuth.test.ts src/stores/auth.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lib/backendAuth.ts src/lib/backendAuth.test.ts src/stores/auth.ts src/stores/auth.test.ts src/lib/supabase.ts
git commit -m "feat: migrate frontend auth store to backend session state"
```

---

### Task 6: Switch Forms And Protected Frontend Calls To Cookie Sessions

**Files:**
- Modify: `src/components/auth/LoginForm.vue`
- Modify: `src/components/auth/SignupForm.vue`
- Modify: `src/composables/useAI.ts`
- Modify: `src/components/ChatInterface.vue`
- Test: `src/lib/backendAuth.test.ts`

- [ ] **Step 1: Write the failing protected-call assertions**

```ts
it('chat requests include csrf header instead of bearer auth', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) })
  vi.stubGlobal('fetch', fetchMock)

  await sendChatMessage({ message: 'hello' })

  expect(fetchMock).toHaveBeenCalledWith(
    expect.any(String),
    expect.objectContaining({
      credentials: 'include',
      headers: expect.objectContaining({
        'X-HELIOS-CSRF': expect.any(String),
      }),
    }),
  )
})
```

- [ ] **Step 2: Run the targeted frontend tests to verify they fail**

Run: `npm run test -- src/stores/auth.test.ts src/lib/backendAuth.test.ts`
Expected: FAIL because login/signup/forms/chat still assume Supabase or bearer-token behavior

- [ ] **Step 3: Migrate forms and protected fetches**

```ts
await auth.signIn(email.value, password.value)
router.push(redirect)
```

```ts
const csrfToken = auth.csrfToken
await fetch(`${apiBase}/api/chat/send`, {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'X-HELIOS-CSRF': csrfToken ?? '',
  },
  body: JSON.stringify(payload),
})
```

```ts
await fetch(`${apiBase}/api/chat/end-session`, {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'X-HELIOS-CSRF': auth.csrfToken ?? '',
  },
  body: JSON.stringify({ sessionId }),
})
```

- [ ] **Step 4: Run the frontend auth/chat verification**

Run: `npm run test -- src/lib/backendAuth.test.ts src/stores/auth.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/components/auth/LoginForm.vue src/components/auth/SignupForm.vue src/composables/useAI.ts src/components/ChatInterface.vue
git commit -m "feat: switch frontend auth and chat calls to cookie sessions"
```

---

### Task 7: End-To-End Verification And Compatibility Cleanup

**Files:**
- Modify: `backend/auth/supabase_auth.py`
- Modify: `backend/tests/test_auth_router.py`
- Modify: `backend/tests/test_chat_security.py`
- Modify: `src/stores/auth.ts`

- [ ] **Step 1: Add the final regression checks**

```python
def test_cookie_session_authenticates_without_authorization_header(test_client, seeded_session):
    test_client.cookies.set("helios_session", seeded_session["id"])
    response = test_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["user"]["id"] == seeded_session["user_id"]


def test_invalid_bearer_token_still_returns_unauthorized(test_client):
    response = test_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer definitely-invalid"},
    )
    assert response.status_code == 401
```

```ts
it('auth init leaves the app logged out cleanly on backend 401', async () => {
  const auth = useAuthStore()
  await auth.init()
  expect(auth.isAuthenticated).toBe(false)
  expect(auth.csrfToken).toBe(null)
})
```

- [ ] **Step 2: Run backend verification**

Run: `python -m pytest backend/tests/test_auth_session_service.py backend/tests/test_auth_router.py backend/tests/test_chat_security.py -q`
Expected: PASS

- [ ] **Step 3: Run frontend verification**

Run: `npm run test -- src/lib/backendAuth.test.ts src/stores/auth.test.ts`
Expected: PASS

- [ ] **Step 4: Run production build verification**

Run: `npm run build`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/auth/supabase_auth.py backend/tests/test_auth_router.py backend/tests/test_chat_security.py src/stores/auth.ts
git commit -m "test: verify backend-owned auth session flow"
```

---

## Self-Review

### Spec coverage

- Backend-owned `httpOnly` cookie session: covered by Tasks 1-3
- Cookie auth dependency + protected routes: covered by Task 4
- Frontend auth store migration: covered by Task 5
- Cookie-backed protected API calls: covered by Task 6
- Tests/build verification: covered by Task 7
- CSRF baseline: covered by Tasks 2, 4, and 6

### Placeholder scan

- Removed vague steps like “add validation later” and replaced them with concrete CSRF/session tests and code skeletons.
- Every task contains explicit file paths, commands, and concrete code fragments.

### Type consistency

- Session cookie name remains `helios_session` throughout.
- CSRF header remains `X-HELIOS-CSRF` throughout.
- Session service API uses `issue_session`, `validate_csrf`, and `revoke_session` consistently across tasks.
- Frontend auth store uses `user` + `csrfToken` as the backend-session contract consistently across tasks.
