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
