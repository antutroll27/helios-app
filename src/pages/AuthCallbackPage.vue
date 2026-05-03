<script setup lang="ts">
import { onMounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const status = shallowRef<'loading' | 'error'>('loading')
const errorMsg = shallowRef('')

onMounted(async () => {
  try {
    await auth.init()
    router.replace(auth.isAuthenticated ? '/' : '/auth')
  } catch {
    errorMsg.value = 'Sign-in could not be completed. Please try again.'
    status.value = 'error'
  }
})
</script>

<template>
  <div class="callback-page">
    <div v-if="status === 'loading'" class="callback-card bento-card">
      <div class="callback-spinner" />
      <p class="callback-label">Finishing secure sign-in...</p>
    </div>

    <div v-else class="callback-card bento-card callback-card--error">
      <p class="callback-error">{{ errorMsg }}</p>
      <button class="callback-retry" @click="router.replace('/auth')">
        Back to sign in ->
      </button>
    </div>
  </div>
</template>

<style scoped>
.callback-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
}

.callback-card {
  width: 100%;
  max-width: 320px;
  padding: 2.5rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.callback-spinner {
  width: 28px;
  height: 28px;
  border: 2px solid rgba(255, 189, 118, 0.2);
  border-top-color: #FFBD76;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.callback-label {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  color: var(--text-muted);
  letter-spacing: var(--tracking-fine);
}

.callback-card--error {
  gap: 1.25rem;
  text-align: center;
}

.callback-error {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  color: #FF4444;
  line-height: 1.5;
}

.callback-retry {
  background: none;
  border: none;
  padding: 0;
  color: var(--color-nectarine, #FFBD76);
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  cursor: pointer;
}
</style>
