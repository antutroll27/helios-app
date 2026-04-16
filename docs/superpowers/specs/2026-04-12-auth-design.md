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
| `src/router/index.ts` | Add `/auth` route (name: `'auth'`); no hard guards — guest access preserved |
| `src/components/NavBar.vue` | Add auth state indicator (Sign in link / initials avatar) |
| `src/components/FloatingBottomNav.vue` | Hidden on `/auth` route |
| `App.vue` | Call `auth.init()` on mount; `auth.dispose()` on unmount; render `AuthBanner`; hide shell components on `/auth` |
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

// TODO: replace `any` with generated Database type when schema types are generated
export const supabase = createClient<any>(
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
init(): void                            // getSession() + subscribe to onAuthStateChange
dispose(): void                         // unsubscribe from onAuthStateChange (call in onUnmounted)
signUp(email, password): Promise<void>
signIn(email, password): Promise<void>
signOut(): Promise<void>                // clears state only — navigation is caller's responsibility
clearError(): void
```

**`init()` detail:**
1. Sets `loading = true`
2. Calls `supabase.auth.getSession()` → sets `user` and `session` from result, sets `loading = false`
3. Stores the subscription returned by `supabase.auth.onAuthStateChange((event, session) => { ... })` in a private ref so `dispose()` can call `subscription.unsubscribe()`

**`dispose()` detail:**
- Calls `subscription.unsubscribe()` if subscription exists
- Called from `App.vue`'s `onUnmounted` (same pattern as `sw.stopPolling()`)

**`signOut()` detail:**
- Calls `supabase.auth.signOut()`
- Clears `user` and `session` to `null`
- Does **not** call `router.push()` — navigation is the caller's responsibility (see §6 NavBar)

**`signUp()` detail:**
1. Calls `supabase.auth.signUp({ email, password })`
2. On success: inserts a row into `public.users` — `supabase.from('users').insert({ id: user.id })`
   - This is required because Supabase Auth creates a row in `auth.users` automatically but does **not** populate `public.users`, which all other tables foreign-key into
3. On error: sets `error` to `err.message` and rethrows

**`signIn()` detail:**
- Calls `supabase.auth.signInWithPassword({ email, password })`
- On error: sets `error` to `err.message` and rethrows

**Token refresh:** Handled automatically by `@supabase/supabase-js` via `onAuthStateChange` — no manual refresh logic needed.

---

## 5. App.vue Integration

```typescript
// App.vue <script setup>
import { onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useSpaceWeatherStore } from './stores/spaceWeather'

const auth = useAuthStore()
const sw   = useSpaceWeatherStore()
const route = useRoute()

onMounted(() => {
  sw.startPolling()
  auth.init()
})
onUnmounted(() => {
  sw.stopPolling()
  auth.dispose()
})

const isAuthRoute = computed(() => route.name === 'auth')
```

```html
<!-- App.vue template -->
<NavBar          v-if="!isAuthRoute" />
<AuthBanner      v-if="!isAuthRoute && !auth.loading" />
<FloatingBottomNav v-if="!isAuthRoute" />
<RouterView />
```

`AuthBanner` is also gated on `!auth.loading` to prevent the banner flashing briefly for returning authenticated users while `getSession()` resolves (~100–400ms round-trip). During the loading window the banner simply does not render.

---

## 6. Auth Page & Forms

### Route

```
/auth?mode=login    (default)
/auth?mode=signup
```

Single route (`name: 'auth'`), one `AuthPage.vue` container. The `mode` query param controls which form is active. Switching modes updates the query param only — no navigation, no page reload.

After successful sign-in, redirect to the route stored in `?redirect` query param, or `/` if absent. NavBar "Sign in" link encodes the current route: `/auth?mode=login&redirect=/lab`.

### AuthPage.vue

Centered card on full Onyx (`#0A171D`) background — standalone layout with no NavBar, no AuthBanner, no FloatingBottomNav (all three are hidden via `v-if="!isAuthRoute"` in App.vue). The card contains the active form component (switched by `mode` query param) and nothing else.

### LoginForm.vue

Fields:
- Email (`type="email"`, `autocomplete="email"`)
- Password (`type="password"`, `autocomplete="current-password"`)
- Submit button: "Sign in"

Behavior:
- Calls `auth.signIn(email, password)` on submit
- On success: `router.push(redirect ?? '/')`
- Error display — check `auth.error` for known messages before showing raw Supabase text:
  - If `auth.error` contains `"Email not confirmed"` → show: `"Please confirm your email first. Check your inbox for the confirmation link."`
  - Otherwise → show `auth.error` inline below the button
- `auth.clearError()` called when user starts typing in either field
- Loading state: button disabled + "Signing in…" while in flight
- Link below form: "Don't have an account? Sign up →" → updates `?mode=signup`
- Placeholder comment: `// TODO: Add Google / Apple OAuth buttons here (see auth spec §10)`

### SignupForm.vue

Fields:
- Email (`type="email"`, `autocomplete="email"`)
- Password (`type="password"`, `autocomplete="new-password"`)
- Confirm password (`type="password"`, `autocomplete="new-password"`)
- Submit button: "Create account"

Behavior:
- Client-side validation: if passwords don't match, show "Passwords don't match" inline and do not call Supabase
- Calls `auth.signUp(email, password)` on submit
- On success: replace form with static success state — "Check your inbox to confirm your account." — no redirect (email must be confirmed before sign-in works)
- On error: show `auth.error` inline below the button
- Loading state: button disabled + "Creating account…"
- Link below form: "Already have an account? Sign in →" → updates `?mode=login`

---

## 7. NavBar Changes

**Unauthenticated (and not loading):**
- Small "Sign in" text button on the far right of the NavBar (same visual weight as existing nav buttons, Geist Mono, `var(--font-size-3xs)`)
- Links to `/auth?mode=login&redirect=<current route>`
- Not rendered while `auth.loading` is true (prevents Sign in → avatar flicker)

**Authenticated:**
- 28×28px circle with the user's email initial (uppercase, centered)
- Styles use CSS custom property tokens — no raw hex values:
  - `background: color-mix(in srgb, var(--color-nectarine) 15%, transparent)`
  - `border: 1px solid color-mix(in srgb, var(--color-nectarine) 30%, transparent)`
  - `color: var(--color-nectarine)`
  - (The `--color-nectarine` token is defined as `#FFBD76` in `src/style.css`; `color-mix()` is the correct way to apply opacity without a separate RGB-channel token)
- Clicking the avatar: calls `await auth.signOut()` then `router.push('/')` — navigation is the component's responsibility, not the store's
- No dropdown — profile/settings dropdown deferred to Google/Apple OAuth spec

---

## 8. Soft Prompt Banner

**`src/components/AuthBanner.vue`:**

Thin strip rendered just below the NavBar in `App.vue`, only when `!auth.isAuthenticated && !auth.loading && !isAuthRoute && !dismissed`.

```
| Save your AI memory and sync across devices — Sign up free →    ×  |
```

Styles:
- Background: `rgba(255, 246, 233, 0.04)`, `border-bottom: 1px solid rgba(255, 246, 233, 0.08)`
- Text: `rgba(255, 246, 233, 0.55)`, font: Geist Mono, `var(--font-size-3xs)`
- "Sign up free →" is a `<RouterLink>` to `/auth?mode=signup`
- × button sets `dismissed = true` and writes to localStorage

**localStorage key:** `helios_authBannerDismissed` — uses the `helios_` prefix matching the convention in `src/stores/user.ts` (which uses `const PREFIX = 'helios_'`).

On mount: reads `localStorage.getItem('helios_authBannerDismissed')` — if `'1'`, sets `dismissed = true` immediately so the banner never renders.

Dismissed state is never reset automatically — persists until the user clears localStorage or signs in (at which point `isAuthenticated` hides the banner regardless).

---

## 9. public.users Row Creation

Supabase Auth automatically creates a row in `auth.users` on `signUp`. It does **not** populate `public.users`, which all application tables (`chat_sessions`, `user_memories`, etc.) foreign-key into via `user_id → public.users(id)`.

The `signUp` action in the auth store creates this row immediately after a successful Supabase Auth signup:

```typescript
const { data, error } = await supabase.auth.signUp({ email, password })
if (error) throw error
// Create public.users row so FK constraints are satisfied.
// Supabase Auth creates auth.users automatically but NOT public.users.
const { error: insertError } = await supabase.from('users').insert({ id: data.user!.id })
// Swallow duplicate-key errors — row already exists from a prior signup attempt
// before email confirmation. Rethrow anything else so genuine failures surface.
if (insertError && !insertError.message.includes('duplicate')) {
  console.warn('[auth] public.users insert failed:', insertError.message)
}
```

The Supabase JS client returns `{ data, error }` rather than throwing — so unchecked errors are already silently ignored. The explicit pattern above makes the intent readable and catches genuine unexpected failures (e.g., schema mismatch) without masking them.

---

## 10. Environment Variables

Add to `.env` (and document in `.env.example`):
```
VITE_SUPABASE_URL=<your supabase project url>
VITE_SUPABASE_ANON_KEY=<your supabase anon/public key>
```

The anon key is safe to expose client-side — it only has access to tables with RLS policies applied (all tables in `schema.sql` have RLS enabled).

---

## 11. What This Spec Does NOT Include

- Password reset / forgot password flow
- Email change or profile editing
- Google / Apple OAuth (placeholder comment in LoginForm marks the location)
- `useAI.ts` backend routing for authenticated users — **spec #2 (backend wiring)**
- Hermes memory persistence — **spec #3 (Hermes wiring)**
- Supabase DB trigger for `public.users` creation — handled client-side in `signUp` action (§9)

---

## 12. File Summary

| File | Action |
|---|---|
| `src/lib/supabase.ts` | Create |
| `src/stores/auth.ts` | Create |
| `src/pages/AuthPage.vue` | Create |
| `src/components/auth/LoginForm.vue` | Create |
| `src/components/auth/SignupForm.vue` | Create |
| `src/components/AuthBanner.vue` | Create |
| `src/router/index.ts` | Modify — add `/auth` route (name: `'auth'`) |
| `src/components/NavBar.vue` | Modify — auth state indicator |
| `src/components/FloatingBottomNav.vue` | Modify — hidden on `auth` route |
| `App.vue` | Modify — `auth.init()` / `dispose()`, `AuthBanner`, `isAuthRoute` computed |
| `.env` | Modify — add Supabase env vars |
