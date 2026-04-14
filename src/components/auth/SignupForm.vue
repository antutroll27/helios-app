<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits<{ (e: 'switch-mode'): void }>()

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

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
    const result = await auth.signUp(email.value, password.value)
    if (result.requiresConfirmation) {
      success.value = true
      return
    }

    const raw = route.query.redirect as string | undefined
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
