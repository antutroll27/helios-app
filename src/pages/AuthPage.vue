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
