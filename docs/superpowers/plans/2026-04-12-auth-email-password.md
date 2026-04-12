# Auth: Email/Password Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional Supabase email/password auth to HELIOS — guest access preserved, auth unlocks JWT for spec #2 (backend wiring).

**Architecture:** Supabase JS client singleton → Pinia auth store → `/auth` route with `AuthPage.vue` container switching between `LoginForm`/`SignupForm`. App.vue hides NavBar/FloatingBottomNav on the auth route via `isAuthRoute` computed. Unauthenticated users see a dismissible soft-prompt banner.

**Tech Stack:** `@supabase/supabase-js`, Vue 3 `<script setup lang="ts">`, Pinia, Vue Router, Vitest

---

## File Map

| File | Action |
|---|---|
| `src/lib/supabase.ts` | Create — singleton Supabase client |
| `src/stores/auth.ts` | Create — Pinia auth store |
| `src/stores/auth.test.ts` | Create — unit tests for auth store |
| `src/pages/AuthPage.vue` | Create — `/auth` route container |
| `src/components/auth/LoginForm.vue` | Create — sign-in form |
| `src/components/auth/SignupForm.vue` | Create — sign-up form |
| `src/components/AuthBanner.vue` | Create — soft-prompt strip |
| `src/router/index.ts` | Modify — add `/auth` route |
| `src/components/NavBar.vue` | Modify — sign-in link / user avatar |
| `src/components/FloatingBottomNav.vue` | No change — hidden via `v-if` in App.vue |
| `src/App.vue` | Modify — `auth.init()`, `auth.dispose()`, `isAuthRoute`, `AuthBanner` |
| `.env` | Modify — add Supabase env vars |

---

## Context for implementers

**Existing patterns to follow:**
- All stores live in `src/stores/` and use `defineStore` from Pinia
- `src/stores/user.ts` uses `const PREFIX = 'helios_'` for all localStorage keys — follow this convention
- `src/App.vue` already does `onMounted(async () => { ... sw.startPolling() })` and `onUnmounted(() => { sw.stopPolling() })` — `auth.init()` / `auth.dispose()` follow the same pattern
- No Tailwind arbitrary bracket values (e.g., `text-[0.55rem]`) — use `@theme` token classes (`text-3xs`, `tracking-fine`) or scoped CSS
- The CSS custom property `--color-nectarine` is defined in `src/style.css` as `#FFBD76`
- `NavBar.vue` right section currently has two icon buttons: reload and theme toggle. The auth indicator goes after those.
- `FloatingBottomNav.vue` uses `useRoute` and `useRouter` already imported

**Spec:** `docs/superpowers/specs/2026-04-12-auth-design.md`

---

## Task 1: Install package + Supabase client + env vars

**Files:**
- Create: `src/lib/supabase.ts`
- Modify: `.env`

- [ ] **Step 1: Install `@supabase/supabase-js`**

```bash
cd helios-app
npm install @supabase/supabase-js --legacy-peer-deps
```

Expected: package added to `node_modules` and `package.json` without errors.

- [ ] **Step 2: Add env vars to `.env` and `.env.example`**

Add these two lines to `.env` (fill in real values from your Supabase project dashboard → Settings → API):

```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

If `.env.example` exists in the repo root, add the same two keys with placeholder values. If it does not exist, create it with:

```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

- [ ] **Step 3: Create `src/lib/supabase.ts`**

```typescript
import { createClient } from '@supabase/supabase-js'

// TODO: replace `any` with generated Database type when schema types are generated
export const supabase = createClient<any>(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)
```

- [ ] **Step 4: Verify the import works**

Run dev server and confirm no import errors:

```bash
npm run dev
```

Expected: dev server starts, no console errors about missing env vars (if Supabase URL/key are filled in).

- [ ] **Step 5: Commit**

```bash
git add src/lib/supabase.ts .env package.json package-lock.json
git commit -m "feat(auth): install supabase-js, create client singleton, add env vars"
```

---

## Task 2: Auth store + tests

**Files:**
- Create: `src/stores/auth.ts`
- Create: `src/stores/auth.test.ts`

- [ ] **Step 1: Write the failing tests first**

Create `src/stores/auth.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock the supabase module before importing the store
vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } },
      }),
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn().mockResolvedValue({ error: null }),
    },
    from: vi.fn().mockReturnValue({
      insert: vi.fn().mockResolvedValue({ error: null }),
    }),
  },
}))

import { useAuthStore } from './auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()  // reset call history between tests
  })

  it('starts unauthenticated with user null', () => {
    const auth = useAuthStore()
    expect(auth.user).toBeNull()
    expect(auth.session).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('init() sets loading=false and hydrates user/session from getSession', async () => {
    const { supabase } = await import('@/lib/supabase')
    vi.mocked(supabase.auth.getSession).mockResolvedValueOnce({
      data: { session: { user: { id: 'u1', email: 'a@b.com' }, access_token: 'tok' } as any },
      error: null,
    })
    const auth = useAuthStore()
    auth.init()
    await new Promise(r => setTimeout(r, 0))
    expect(auth.loading).toBe(false)
    expect(auth.user).not.toBeNull()
    expect(auth.session).not.toBeNull()
  })

  it('signIn() sets error and rethrows on failure', async () => {
    const { supabase } = await import('@/lib/supabase')
    vi.mocked(supabase.auth.signInWithPassword).mockResolvedValueOnce({
      data: { user: null, session: null },
      error: { message: 'Invalid login credentials', name: 'AuthApiError', status: 400 } as any,
    })
    const auth = useAuthStore()
    await expect(auth.signIn('bad@example.com', 'wrong')).rejects.toThrow('Invalid login credentials')
    expect(auth.error).toBe('Invalid login credentials')
  })

  it('clearError() resets error to null', () => {
    const auth = useAuthStore()
    auth.error = 'some error'
    auth.clearError()
    expect(auth.error).toBeNull()
  })

  it('signOut() clears user and session', async () => {
    const auth = useAuthStore()
    // Manually set state as if logged in
    auth.user = { id: 'abc', email: 'test@test.com' } as any
    auth.session = { access_token: 'tok' } as any
    await auth.signOut()
    expect(auth.user).toBeNull()
    expect(auth.session).toBeNull()
  })

  it('signUp() calls public.users insert with the new user id', async () => {
    const { supabase } = await import('@/lib/supabase')
    vi.mocked(supabase.auth.signUp).mockResolvedValueOnce({
      data: { user: { id: 'new-id', email: 'x@y.com' } as any, session: null },
      error: null,
    })
    const auth = useAuthStore()
    await auth.signUp('x@y.com', 'pass123')
    expect(supabase.from).toHaveBeenCalledWith('users')
  })
})
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
npx vitest run src/stores/auth.test.ts
```

Expected: FAIL — `useAuthStore` is not defined (module doesn't exist yet).

- [ ] **Step 3: Create `src/stores/auth.ts`**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

export const useAuthStore = defineStore('auth', () => {
  const user    = ref<User | null>(null)
  const session = ref<Session | null>(null)
  const loading = ref(true)
  const error   = ref<string | null>(null)

  // Private — holds the onAuthStateChange subscription for cleanup
  // Use structural type — `Subscription` is not reliably exported from supabase-js top-level
  let _subscription: { unsubscribe: () => void } | null = null

  const isAuthenticated = computed(() => user.value !== null)

  function init() {
    loading.value = true
    supabase.auth.getSession().then(({ data }) => {
      session.value = data.session
      user.value    = data.session?.user ?? null
      loading.value = false
    })

    const { data } = supabase.auth.onAuthStateChange((_event, newSession) => {
      session.value = newSession
      user.value    = newSession?.user ?? null
    })
    _subscription = data.subscription
  }

  function dispose() {
    _subscription?.unsubscribe()
    _subscription = null
  }

  async function signIn(email: string, password: string) {
    error.value = null
    const { error: err } = await supabase.auth.signInWithPassword({ email, password })
    if (err) {
      error.value = err.message
      throw new Error(err.message)
    }
  }

  async function signUp(email: string, password: string) {
    error.value = null
    const { data, error: err } = await supabase.auth.signUp({ email, password })
    if (err) {
      error.value = err.message
      throw new Error(err.message)
    }
    // Create public.users row — Supabase Auth only creates auth.users automatically
    const { error: insertError } = await supabase.from('users').insert({ id: data.user!.id })
    // Swallow duplicate-key errors (prior signup attempt before email confirmation)
    if (insertError && !insertError.message.includes('duplicate')) {
      console.warn('[auth] public.users insert failed:', insertError.message)
    }
  }

  async function signOut() {
    await supabase.auth.signOut()
    user.value    = null
    session.value = null
  }

  function clearError() {
    error.value = null
  }

  return {
    user, session, loading, error,
    isAuthenticated,
    init, dispose, signIn, signUp, signOut, clearError,
  }
})
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
npx vitest run src/stores/auth.test.ts
```

Expected: 5/5 PASS.

- [ ] **Step 5: Run full test suite — confirm no regressions**

```bash
npx vitest run
```

Expected: all previous tests still pass.

- [ ] **Step 6: Commit**

```bash
git add src/stores/auth.ts src/stores/auth.test.ts
git commit -m "feat(auth): add auth Pinia store with init/dispose/signIn/signUp/signOut"
```

---

## Task 3: Router + AuthPage container

**Files:**
- Modify: `src/router/index.ts`
- Create: `src/pages/AuthPage.vue`

- [ ] **Step 1: Add `/auth` route to the router**

Edit `src/router/index.ts` — add the auth route (name `'auth'` is required for `isAuthRoute` computed in App.vue):

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',           component: () => import('@/pages/HomePage.vue') },
    { path: '/settings',   component: () => import('@/pages/SettingsPage.vue') },
    { path: '/biometrics', component: () => import('@/pages/BiometricsPage.vue') },
    { path: '/lab',        component: () => import('@/pages/LabPage.vue') },
    { path: '/auth',       name: 'auth', component: () => import('@/pages/AuthPage.vue') },
  ]
})

export default router
```

- [ ] **Step 2: Create `src/pages/AuthPage.vue`**

`AuthPage.vue` is a full-screen centered card. It reads `?mode` from the query string and renders either `LoginForm` or `SignupForm`. Switching modes updates the query param only (no navigation).

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LoginForm from '@/components/auth/LoginForm.vue'
import SignupForm from '@/components/auth/SignupForm.vue'

const route  = useRoute()
const router = useRouter()

const mode = computed(() => route.query.mode === 'signup' ? 'signup' : 'login')

function switchMode(to: 'login' | 'signup') {
  router.replace({ query: { ...route.query, mode: to } })
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card bento-card">
      <!-- Brand mark -->
      <div class="auth-brand">HELIOS</div>
      <p class="auth-subtitle">Circadian Intelligence</p>

      <!-- Active form -->
      <LoginForm
        v-if="mode === 'login'"
        @switch-mode="switchMode('signup')"
      />
      <SignupForm
        v-else
        @switch-mode="switchMode('login')"
      />
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  padding: 1.5rem;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 2rem 2rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.auth-brand {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs5);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  color: var(--color-nectarine, #FFBD76);
  text-transform: uppercase;
}

.auth-subtitle {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  color: var(--text-muted);
  margin-bottom: 1.25rem;
}
</style>
```

- [ ] **Step 3: Verify route works**

Navigate to `http://localhost:5173/auth` in the browser. Expected: centered card visible (forms not wired yet — component import errors are expected until Task 4/5).

- [ ] **Step 4: Commit**

```bash
git add src/router/index.ts src/pages/AuthPage.vue
git commit -m "feat(auth): add /auth route and AuthPage container"
```

---

## Task 4: LoginForm

**Files:**
- Create: `src/components/auth/LoginForm.vue`

- [ ] **Step 1: Create `src/components/auth/LoginForm.vue`**

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits<{ (e: 'switch-mode'): void }>()

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()

const email    = ref('')
const password = ref('')
const loading  = ref(false)

// Map known Supabase error strings to friendlier copy
function friendlyError(msg: string | null): string | null {
  if (!msg) return null
  if (msg.includes('Email not confirmed'))
    return 'Please confirm your email first. Check your inbox for the confirmation link.'
  return msg
}

// Clear error as user types
watch([email, password], () => auth.clearError())

async function submit() {
  if (!email.value || !password.value) return
  loading.value = true
  try {
    await auth.signIn(email.value, password.value)
    const redirect = route.query.redirect as string | undefined
    router.push(redirect ?? '/')
  } catch {
    // error is set on auth store — displayed below
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form class="auth-form" @submit.prevent="submit" novalidate>
    <h2 class="auth-form-title">Sign in</h2>

    <div class="auth-field">
      <label class="auth-label" for="lf-email">Email</label>
      <input
        id="lf-email"
        v-model="email"
        type="email"
        autocomplete="email"
        class="auth-input"
        placeholder="you@example.com"
        :disabled="loading"
        required
      />
    </div>

    <div class="auth-field">
      <label class="auth-label" for="lf-password">Password</label>
      <input
        id="lf-password"
        v-model="password"
        type="password"
        autocomplete="current-password"
        class="auth-input"
        placeholder="••••••••"
        :disabled="loading"
        required
      />
    </div>

    <p v-if="auth.error" class="auth-error">{{ friendlyError(auth.error) }}</p>

    <button type="submit" class="auth-btn" :disabled="loading || !email || !password">
      {{ loading ? 'Signing in…' : 'Sign in' }}
    </button>

    <!-- TODO: Add Google / Apple OAuth buttons here (see auth spec §10) -->

    <p class="auth-switch">
      Don't have an account?
      <button type="button" class="auth-link" @click="emit('switch-mode')">Sign up →</button>
    </p>
  </form>
</template>

<style scoped>
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.auth-form-title {
  font-size: var(--font-size-md2);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.auth-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.auth-label {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  color: var(--text-muted);
  text-transform: uppercase;
}

.auth-input {
  background: rgba(255, 246, 233, 0.05);
  border: 1px solid rgba(255, 246, 233, 0.12);
  border-radius: 6px;
  padding: 0.6rem 0.75rem;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
  box-sizing: border-box;
}

.auth-input:focus {
  border-color: rgba(255, 189, 118, 0.45);
}

.auth-input:disabled {
  opacity: 0.5;
}

.auth-error {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  color: #FF4444;
  background: rgba(255, 68, 68, 0.07);
  border-left: 2px solid rgba(255, 68, 68, 0.4);
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  line-height: 1.4;
}

.auth-btn {
  background: var(--color-nectarine, #FFBD76);
  color: #0A171D;
  border: none;
  border-radius: 6px;
  padding: 0.65rem 1rem;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs5);
  font-weight: 700;
  letter-spacing: var(--tracking-fine);
  cursor: pointer;
  transition: opacity 0.15s;
  width: 100%;
  margin-top: 0.25rem;
}

.auth-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.auth-switch {
  font-size: var(--font-size-xs3);
  color: var(--text-muted);
  text-align: center;
  margin-top: 0.25rem;
}

.auth-link {
  background: none;
  border: none;
  padding: 0;
  color: var(--color-nectarine, #FFBD76);
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  cursor: pointer;
}
</style>
```

- [ ] **Step 2: Verify in browser**

Navigate to `http://localhost:5173/auth?mode=login`. Expected: sign-in form with email/password fields and "Sign in" button.

- [ ] **Step 3: Commit**

```bash
git add src/components/auth/LoginForm.vue
git commit -m "feat(auth): add LoginForm with error handling and mode switch"
```

---

## Task 5: SignupForm

**Files:**
- Create: `src/components/auth/SignupForm.vue`

- [ ] **Step 1: Create `src/components/auth/SignupForm.vue`**

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits<{ (e: 'switch-mode'): void }>()

const auth = useAuthStore()

const email           = ref('')
const password        = ref('')
const confirmPassword = ref('')
const loading         = ref(false)
const success         = ref(false)
const matchError      = ref<string | null>(null)

watch([email, password, confirmPassword], () => {
  auth.clearError()
  matchError.value = null
})

async function submit() {
  if (!email.value || !password.value || !confirmPassword.value) return
  if (password.value !== confirmPassword.value) {
    matchError.value = "Passwords don't match"
    return
  }
  loading.value = true
  try {
    await auth.signUp(email.value, password.value)
    success.value = true
  } catch {
    // error is set on auth store — displayed below
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <!-- Success state — shown after signUp -->
  <div v-if="success" class="auth-success">
    <div class="auth-success-icon">✓</div>
    <h2 class="auth-form-title">Check your inbox</h2>
    <p class="auth-success-body">
      We sent a confirmation link to <strong>{{ email }}</strong>.
      Click it to activate your account, then sign in.
    </p>
    <button type="button" class="auth-link-standalone" @click="emit('switch-mode')">
      Back to sign in →
    </button>
  </div>

  <!-- Sign-up form -->
  <form v-else class="auth-form" @submit.prevent="submit" novalidate>
    <h2 class="auth-form-title">Create account</h2>

    <div class="auth-field">
      <label class="auth-label" for="sf-email">Email</label>
      <input
        id="sf-email"
        v-model="email"
        type="email"
        autocomplete="email"
        class="auth-input"
        placeholder="you@example.com"
        :disabled="loading"
        required
      />
    </div>

    <div class="auth-field">
      <label class="auth-label" for="sf-password">Password</label>
      <input
        id="sf-password"
        v-model="password"
        type="password"
        autocomplete="new-password"
        class="auth-input"
        placeholder="••••••••"
        :disabled="loading"
        required
      />
    </div>

    <div class="auth-field">
      <label class="auth-label" for="sf-confirm">Confirm password</label>
      <input
        id="sf-confirm"
        v-model="confirmPassword"
        type="password"
        autocomplete="new-password"
        class="auth-input"
        placeholder="••••••••"
        :disabled="loading"
        required
      />
    </div>

    <p v-if="matchError" class="auth-error">{{ matchError }}</p>
    <p v-else-if="auth.error" class="auth-error">{{ auth.error }}</p>

    <button
      type="submit"
      class="auth-btn"
      :disabled="loading || !email || !password || !confirmPassword"
    >
      {{ loading ? 'Creating account…' : 'Create account' }}
    </button>

    <p class="auth-switch">
      Already have an account?
      <button type="button" class="auth-link" @click="emit('switch-mode')">Sign in →</button>
    </p>
  </form>
</template>

<style scoped>
/* Shared form styles — duplicated from LoginForm intentionally (no shared CSS file for two components) */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.auth-form-title {
  font-size: var(--font-size-md2);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.auth-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.auth-label {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  color: var(--text-muted);
  text-transform: uppercase;
}

.auth-input {
  background: rgba(255, 246, 233, 0.05);
  border: 1px solid rgba(255, 246, 233, 0.12);
  border-radius: 6px;
  padding: 0.6rem 0.75rem;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
  box-sizing: border-box;
}

.auth-input:focus {
  border-color: rgba(255, 189, 118, 0.45);
}

.auth-input:disabled {
  opacity: 0.5;
}

.auth-error {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  color: #FF4444;
  background: rgba(255, 68, 68, 0.07);
  border-left: 2px solid rgba(255, 68, 68, 0.4);
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  line-height: 1.4;
}

.auth-btn {
  background: var(--color-nectarine, #FFBD76);
  color: #0A171D;
  border: none;
  border-radius: 6px;
  padding: 0.65rem 1rem;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs5);
  font-weight: 700;
  letter-spacing: var(--tracking-fine);
  cursor: pointer;
  transition: opacity 0.15s;
  width: 100%;
  margin-top: 0.25rem;
}

.auth-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.auth-switch {
  font-size: var(--font-size-xs3);
  color: var(--text-muted);
  text-align: center;
  margin-top: 0.25rem;
}

.auth-link {
  background: none;
  border: none;
  padding: 0;
  color: var(--color-nectarine, #FFBD76);
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  cursor: pointer;
}

/* Success state */
.auth-success {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
  text-align: center;
  padding: 1rem 0;
}

.auth-success-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(0, 212, 170, 0.12);
  border: 1px solid rgba(0, 212, 170, 0.3);
  color: #00D4AA;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-success-body {
  font-size: var(--font-size-xs3);
  color: var(--text-muted);
  line-height: 1.5;
}

.auth-success-body strong {
  color: var(--text-primary);
}

.auth-link-standalone {
  background: none;
  border: none;
  padding: 0;
  color: var(--color-nectarine, #FFBD76);
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  cursor: pointer;
  margin-top: 0.5rem;
}
</style>
```

- [ ] **Step 2: Verify mode switching works**

Navigate to `http://localhost:5173/auth`. Click "Sign up →" — URL should update to `?mode=signup` and the signup form should appear. Click "Sign in →" — should switch back. No full navigation.

- [ ] **Step 3: Commit**

```bash
git add src/components/auth/SignupForm.vue
git commit -m "feat(auth): add SignupForm with password validation and success state"
```

---

## Task 6: App.vue integration + FloatingBottomNav

**Files:**
- Modify: `src/App.vue`
- Modify: `src/components/FloatingBottomNav.vue`

- [ ] **Step 1: Update `src/App.vue`**

Replace the full file content with the updated version that adds `auth.init()` / `auth.dispose()`, `isAuthRoute`, and conditional rendering:

```vue
<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useGeoStore } from '@/stores/geo'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'
import { useDonkiStore } from '@/stores/donki'
import { useEnvironmentStore } from '@/stores/environment'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'
import NavBar from '@/components/NavBar.vue'
import FloatingBottomNav from '@/components/FloatingBottomNav.vue'
import AuthBanner from '@/components/AuthBanner.vue'

const geo   = useGeoStore()
const sw    = useSpaceWeatherStore()
const donki = useDonkiStore()
const env   = useEnvironmentStore()
const auth  = useAuthStore()
const route = useRoute()
const { isDark } = useTheme()

const isAuthRoute = computed(() => route.name === 'auth')

onMounted(async () => {
  auth.init()  // non-blocking — resolves auth state in background
  await geo.requestLocation()
  await Promise.allSettled([
    sw.fetchAll(),
    donki.fetchAll(),
    env.fetchAll(geo.lat, geo.lng)
  ])
  sw.startPolling()
})

onUnmounted(() => {
  sw.stopPolling()
  auth.dispose()
})
</script>

<template>
  <div
    class="min-h-screen transition-colors duration-300"
    :style="{
      backgroundColor: 'var(--bg-primary)',
      color: 'var(--text-primary)'
    }"
  >
    <NavBar            v-if="!isAuthRoute" />
    <AuthBanner        v-if="!isAuthRoute && !auth.loading" />
    <main class="main-content">
      <RouterView />
    </main>
    <FloatingBottomNav v-if="!isAuthRoute" />
  </div>
</template>

<style>
.main-content {
  padding-bottom: calc(5rem + env(safe-area-inset-bottom, 0px));
}
</style>
```

- [ ] **Step 2: Hide FloatingBottomNav on `/auth` route**

`FloatingBottomNav.vue` already uses `useRoute` — it already knows the current route. But the hide is handled at the App.vue level via `v-if="!isAuthRoute"`. No changes needed to `FloatingBottomNav.vue` itself. Verify this: open `src/components/FloatingBottomNav.vue` and confirm it renders inside App.vue's template (not self-contained) — if so, the `v-if` at App.vue level is sufficient.

- [ ] **Step 3: Verify**

Navigate to `http://localhost:5173/auth`. Confirm: no NavBar, no FloatingBottomNav. Navigate to `http://localhost:5173/` — confirm NavBar and FloatingBottomNav reappear.

- [ ] **Step 4: Commit**

```bash
git add src/App.vue
git commit -m "feat(auth): wire auth store into App.vue, hide shell on /auth route"
```

---

## Task 7: NavBar auth indicator

**Files:**
- Modify: `src/components/NavBar.vue`

The NavBar currently has a right section with two icon buttons (reload, theme toggle). Add the auth indicator after those.

- [ ] **Step 1: Add auth imports to NavBar**

In `src/components/NavBar.vue`, make two import changes:

1. Change the existing Vue import from `import { ref } from 'vue'` to `import { ref, computed } from 'vue'`
2. Add a new import for vue-router (not currently imported in NavBar): `import { useRouter, useRoute } from 'vue-router'`

Then add to `<script setup>`:

```typescript
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route  = useRoute()
const auth   = useAuthStore()

const userInitial = computed(() =>
  auth.user?.email ? auth.user.email[0].toUpperCase() : ''
)

async function handleSignOut() {
  await auth.signOut()
  router.push('/')
}
```

- [ ] **Step 2: Add auth indicator to NavBar template**

In `NavBar.vue`'s template, inside `.nav-right` div, add after the theme toggle button:

```html
<!-- Auth indicator — hidden while auth is resolving to prevent flicker -->
<template v-if="!auth.loading">
  <!-- Unauthenticated: Sign in link -->
  <RouterLink
    v-if="!auth.isAuthenticated"
    :to="`/auth?mode=login&redirect=${encodeURIComponent(route.path)}`"
    class="nav-sign-in"
  >
    Sign in
  </RouterLink>

  <!-- Authenticated: initial avatar -->
  <button
    v-else
    class="nav-avatar"
    :title="`Signed in as ${auth.user?.email} — click to sign out`"
    @click="handleSignOut"
  >
    {{ userInitial }}
  </button>
</template>
```

- [ ] **Step 3: Add scoped CSS for auth indicator**

In the `<style scoped>` block of `NavBar.vue`, add:

```css
.nav-sign-in {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.15s;
}

.nav-sign-in:hover {
  color: var(--color-nectarine, #FFBD76);
}

.nav-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--color-nectarine, #FFBD76) 15%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-nectarine, #FFBD76) 30%, transparent);
  color: var(--color-nectarine, #FFBD76);
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.15s;
}

.nav-avatar:hover {
  opacity: 0.8;
}
```

- [ ] **Step 4: Verify**

- Guest: NavBar shows "Sign in" text link. Clicking goes to `/auth?mode=login&redirect=/`.
- After signing in: NavBar shows the user's initial in a Nectarine circle. Clicking signs out and redirects to `/`.
- While auth is loading on cold visit: neither shows (no flicker).

- [ ] **Step 5: Commit**

```bash
git add src/components/NavBar.vue
git commit -m "feat(auth): add sign-in link and user avatar to NavBar"
```

---

## Task 8: AuthBanner (soft prompt)

**Files:**
- Create: `src/components/AuthBanner.vue`

- [ ] **Step 1: Create `src/components/AuthBanner.vue`**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth      = useAuthStore()
const dismissed = ref(false)

const STORAGE_KEY = 'helios_authBannerDismissed'

onMounted(() => {
  if (localStorage.getItem(STORAGE_KEY) === '1') {
    dismissed.value = true
  }
})

function dismiss() {
  dismissed.value = true
  localStorage.setItem(STORAGE_KEY, '1')
}
</script>

<template>
  <div
    v-if="!auth.isAuthenticated && !dismissed"
    class="auth-banner"
    role="banner"
  >
    <span class="auth-banner-text">
      Save your AI memory and sync across devices —
      <RouterLink to="/auth?mode=signup" class="auth-banner-link">Sign up free →</RouterLink>
    </span>
    <button
      type="button"
      class="auth-banner-dismiss"
      aria-label="Dismiss"
      @click="dismiss"
    >
      ×
    </button>
  </div>
</template>

<style scoped>
.auth-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.45rem 1rem;
  background: rgba(255, 246, 233, 0.04);
  border-bottom: 1px solid rgba(255, 246, 233, 0.08);
  /* Sits below the fixed NavBar.
     Use a CSS variable so future NavBar height changes stay in one place.
     Measure the actual NavBar height in the browser and set accordingly.
     The NavBar is approximately 50px tall (padding 0.42rem + 30px SVG logo). */
  margin-top: var(--navbar-height, 50px);
}

.auth-banner-text {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  color: rgba(255, 246, 233, 0.55);
}

.auth-banner-link {
  color: var(--color-nectarine, #FFBD76);
  text-decoration: none;
}

.auth-banner-link:hover {
  text-decoration: underline;
}

.auth-banner-dismiss {
  background: none;
  border: none;
  color: rgba(255, 246, 233, 0.35);
  font-size: 1rem;
  line-height: 1;
  cursor: pointer;
  padding: 0 0.25rem;
  flex-shrink: 0;
  transition: color 0.15s;
}

.auth-banner-dismiss:hover {
  color: rgba(255, 246, 233, 0.7);
}
</style>
```

**Note on `margin-top`:** The NavBar is `position: fixed` so it doesn't push down page content. The AuthBanner uses `var(--navbar-height, 50px)` to clear it. To wire this properly, add `--navbar-height: <measured value>px` to the `:root` block in `src/style.css` (or wherever global CSS variables live) after measuring the rendered NavBar height in the browser. The default fallback of 50px is approximate.

- [ ] **Step 2: Verify**

- Guest user: AuthBanner appears below NavBar with the copy and dismiss button.
- Click ×: banner disappears and stays gone after page reload.
- Sign in: banner disappears because `auth.isAuthenticated` becomes true.
- Navigate to `/auth`: banner does not appear (gated by `!isAuthRoute && !auth.loading` in App.vue).

- [ ] **Step 3: Run full test suite**

```bash
npx vitest run
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/components/AuthBanner.vue
git commit -m "feat(auth): add AuthBanner soft prompt with localStorage dismiss"
```

---

## Verification Checklist

After all tasks are complete, verify end-to-end:

1. **Guest flow:** Visit `/` → see AuthBanner → click "Sign up free →" → land on `/auth?mode=signup` → no NavBar or FloatingBottomNav visible
2. **Mode switching:** On `/auth?mode=signup`, click "Sign in →" → URL updates to `?mode=login`, form switches without page reload
3. **Sign up:** Enter email + password + confirm → click "Create account" → success state shows "Check your inbox"
4. **Sign in:** After confirming email in inbox → sign in → redirected to `/` → NavBar shows user initial → banner gone
5. **Sign out:** Click user avatar → signs out → redirected to `/` → NavBar shows "Sign in" link → banner reappears
6. **Banner dismiss:** Guest user → click × → banner gone → reload page → still gone
7. **Auth loading guard:** Reload page as authenticated user → no "Sign in" flash before avatar appears
8. **Test suite:** `npx vitest run` — all tests pass
