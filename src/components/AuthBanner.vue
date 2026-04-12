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
     Use a CSS variable so future NavBar height changes stay in one place. */
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
