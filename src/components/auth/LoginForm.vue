<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getOAuthStartUrl } from '@/lib/backendAuth'

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

async function signInWithGoogle() {
  const redirect = (route.query.redirect as string | undefined) ?? '/'
  window.location.assign(getOAuthStartUrl('google', redirect))
}

async function submit() {
  if (!email.value || !password.value) return
  loading.value = true
  try {
    await auth.signIn(email.value, password.value)
    const raw = route.query.redirect as string | undefined
    // Validate redirect is a relative path (no protocol) to prevent open redirect
    const redirect = raw && raw.startsWith('/') && !raw.startsWith('//') ? raw : '/'
    router.push(redirect)
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

    <div class="auth-divider"><span>or</span></div>

    <button type="button" class="auth-btn-google" @click="signInWithGoogle">
      <svg class="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
      </svg>
      Continue with Google
    </button>

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

.auth-divider {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 0.1rem 0;
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(255, 246, 233, 0.1);
}

.auth-divider span {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  color: var(--text-muted);
  text-transform: uppercase;
}

.auth-btn-google {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  width: 100%;
  padding: 0.6rem 1rem;
  background: rgba(255, 246, 233, 0.04);
  border: 1px solid rgba(255, 246, 233, 0.12);
  border-radius: 6px;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.auth-btn-google:hover {
  background: rgba(255, 246, 233, 0.08);
  border-color: rgba(255, 246, 233, 0.22);
}

.google-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}
</style>
