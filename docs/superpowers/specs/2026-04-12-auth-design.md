# Auth: Email/Password — Design Spec

**Date:** 2026-04-12
**Scope:** Supabase email/password authentication for HELIOS. Guest access is preserved; auth unlocks memory persistence and backend-routed chat (spec #2). Google/Apple OAuth deferred.

---

## 1. Overview

HELIOS currently works without any user identity — the chat calls LLM providers directly from the browser and all state is local. This spec adds optional Supabase authentication:

- Unauthenticated users: app works exactly as today (direct-to-provider chat, local state)
- Authenticated users: JWT available for spec #2 (backend routing + Hermes memory)
- A soft prompt banner encourages signup without blocking access

---

## 2. Architecture

### New files

| File | Role |
|---|---|
| `src/lib/supabase.ts` | Singleton Supabase client — imported everywhere auth or DB is needed |
| `src/stores/auth.ts` | Pinia auth store — reactive user/session state, auth actions |
| `src/pages/AuthPage.vue` | `/auth` route — container that owns the login/signup toggle |
| `src/components/auth/LoginForm.vue` | Email + password sign-in form |
| `src/components/auth/SignupForm.vue` | Email + password + confirm signup form |
| `src/components/AuthBanner.vue` | Soft prompt strip shown to unauthenticated users |

### Modified files

| File | Change |
|---|---|
| `src/router/index.ts` | Add `/auth` route; no hard guards — guest access preserved |
| `src/components/NavBar.vue` | Add auth state indicator (Sign in link / initials avatar) |
| `App.vue` | Call `auth.init()` on mount |
| `.env` | Add `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` |

### New package

```bash
npm install @supabase/supabase-js --legacy-peer-deps
```

---

## 3. Supabase Client

**`src/lib/supabase.ts`:**

```typescript
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)
```

Single export, imported directly by the auth store and any future composables that need Supabase.

---

## 4. Auth Store

**`src/stores/auth.ts`:**

### State

```typescript
interface AuthState {
  user:    User | null      // Supabase User object (has .id, .email)
  session: Session | null   // has .access_token (JWT for backend calls)
  loading: boolean          // true while getSession() resolves on mount
  error:   string | null    // last auth error, cleared on next action
}
```

### Getters

```typescript
isAuthenticated: (state) => state.user !== null
```

### Actions

```typescript
init()                          // getSession() + subscribe to onAuthStateChange
signUp(email, password): Promise<void>
signIn(email, password): Promise<void>
signOut(): Promise<void>
clearError(): void
```

**`init()` detail:**
- Calls `supabase.auth.getSession()` → sets `user` and `session` from result
- Subscribes to `supabase.auth.onAuthStateChange((event, session) => { ... })` — keeps state reactive across tab focus, token refresh, sign-out from another tab
- Sets `loading = false` after getSession resolves

**Error handling:** `signUp` and `signIn` catch Supabase errors, set `error` to `err.message`, and rethrow so the form component can respond. `signOut` clears user/session and navigates to `/`.

**Token refresh:** Handled automatically by `@supabase/supabase-js` — no manual refresh logic needed.

---

## 5. Auth Page & Forms

### Route

```
/auth?mode=login    (default)
/auth?mode=signup
```

Single route, one `AuthPage.vue` container. The `mode` query param controls which form is active. Switching modes updates the query param only — no navigation, no page reload.

After successful sign-in or sign-up email confirmation, redirect to the route stored in `?redirect` query param, or `/` if absent. NavBar "Sign in" link passes the current route: `/auth?mode=login&redirect=/lab`.

### AuthPage.vue

Centered card on full Onyx (`#0A171D`) background. No NavBar on this page — standalone layout. Card contains the active form component (keyed on `mode`) and nothing else.

### LoginForm.vue

Fields:
- Email (`type="email"`, autocomplete="email")
- Password (`type="password"`, autocomplete="current-password")
- Submit button: "Sign in"

Behavior:
- Calls `auth.signIn(email, password)` on submit
- Shows `auth.error` inline below the button if set, cleared when user starts typing
- Loading state: button disabled + "Signing in…" while in flight
- On success: router pushes to `redirect` param or `/`
- Link below form: "Don't have an account? Sign up →" → updates `?mode=signup`
- Placeholder comment: `// TODO: Add Google / Apple OAuth buttons here`

### SignupForm.vue

Fields:
- Email (`type="email"`, autocomplete="email")
- Password (`type="password"`, autocomplete="new-password")
- Confirm password (`type="password"`, autocomplete="new-password")
- Submit button: "Create account"

Behavior:
- Client-side validation: passwords must match before calling Supabase (inline error: "Passwords don't match")
- Calls `auth.signUp(email, password)` on submit
- On success: replaces form with a single success state — "Check your inbox to confirm your account." — no redirect (user must verify email first)
- On error: inline error below the button
- Loading state: button disabled + "Creating account…"
- Link below form: "Already have an account? Sign in →" → updates `?mode=login`

---

## 6. NavBar Changes

**Unauthenticated:**
- Small "Sign in" text button on the far right of the NavBar (same visual weight as existing nav buttons)
- Links to `/auth?mode=login&redirect=<current route>`

**Authenticated:**
- 28×28px circle with the user's email initial (uppercase, centered)
- Background: `rgba(255, 189, 118, 0.15)` (Nectarine tint), border: `1px solid rgba(255, 189, 118, 0.3)`, text: `#FFBD76`
- Clicking the avatar calls `auth.signOut()` directly (no dropdown — profile/settings dropdown deferred to Google/Apple OAuth spec)

---

## 7. Soft Prompt Banner

**`src/components/AuthBanner.vue`:**

Thin strip rendered just below the NavBar in `App.vue`, only when `!auth.isAuthenticated && !dismissed`.

```
| Save your AI memory and sync across devices — Sign up free →    ×  |
```

Styles:
- Background: `rgba(255, 246, 233, 0.04)`, border-bottom: `1px solid rgba(255, 246, 233, 0.08)`
- Text: `rgba(255, 246, 233, 0.55)`, font: Geist Mono, `var(--font-size-3xs)`
- "Sign up free →" is a router-link to `/auth?mode=signup`
- × button sets `dismissed = true` and writes `'auth-banner-dismissed': '1'` to `localStorage`
- On mount: reads `localStorage` — if already dismissed, never renders

Dismissed state is never reset automatically (persists until the user clears localStorage or signs in, at which point the banner is hidden by `isAuthenticated`).

---

## 8. App.vue Integration

```typescript
// App.vue <script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
const auth = useAuthStore()
onMounted(() => auth.init())
```

`AuthBanner` is rendered in the App layout:
```html
<!-- App.vue template -->
<NavBar />
<AuthBanner />
<RouterView />
```

---

## 9. Environment Variables

Add to `.env` (and document in `.env.example`):
```
VITE_SUPABASE_URL=<your supabase project url>
VITE_SUPABASE_ANON_KEY=<your supabase anon/public key>
```

The anon key is safe to expose client-side — it only has access to tables with appropriate RLS policies.

---

## 10. What This Spec Does NOT Include

- Password reset / forgot password flow
- Email change or profile editing
- Google / Apple OAuth (placeholder comment in LoginForm marks the location)
- `useAI.ts` backend routing for authenticated users — **spec #2 (backend wiring)**
- Hermes memory persistence — **spec #3 (Hermes wiring)**
- Any new Supabase tables — existing `users` table in `schema.sql` is sufficient; Supabase Auth manages the `auth.users` table automatically

---

## 11. File Summary

| File | Action |
|---|---|
| `src/lib/supabase.ts` | Create |
| `src/stores/auth.ts` | Create |
| `src/pages/AuthPage.vue` | Create |
| `src/components/auth/LoginForm.vue` | Create |
| `src/components/auth/SignupForm.vue` | Create |
| `src/components/AuthBanner.vue` | Create |
| `src/router/index.ts` | Modify |
| `src/components/NavBar.vue` | Modify |
| `App.vue` | Modify |
| `.env` | Modify |
