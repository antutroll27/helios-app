import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import {
  login as backendLogin,
  logout as backendLogout,
  me as backendMe,
  signup as backendSignup,
  type BackendAuthPayload,
  type BackendAuthUser,
} from '@/lib/backendAuth'
import { useUserStore } from '@/stores/user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<BackendAuthUser | null>(null)
  const csrfToken = ref<string | null>(null)
  const loading = ref(true)
  const error = ref<string | null>(null)
  const userStore = useUserStore()

  let initPromise: Promise<void> | null = null

  const isAuthenticated = computed(() => user.value !== null)

  function applyPayload(payload: BackendAuthPayload | null) {
    user.value = payload?.user ?? null
    csrfToken.value = payload?.csrfToken ?? null
  }

  function clearAuthState() {
    user.value = null
    csrfToken.value = null
  }

  async function init() {
    if (initPromise) return initPromise

    loading.value = true
    initPromise = (async () => {
      try {
        const payload = await backendMe()
        applyPayload(payload)
      } catch {
        clearAuthState()
      } finally {
        loading.value = false
        initPromise = null
      }
    })()

    return initPromise
  }

  function dispose() {
    initPromise = null
  }

  async function signIn(email: string, password: string) {
    error.value = null
    try {
      const payload = await backendLogin(email, password)
      applyPayload(payload)
      return payload
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Sign-in failed'
      error.value = message
      throw new Error(message)
    }
  }

  async function signUp(email: string, password: string) {
    error.value = null
    try {
      const payload = await backendSignup(email, password)
      if (payload.requiresConfirmation) {
        clearAuthState()
      } else {
        applyPayload(payload)
      }
      return payload
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Sign-up failed'
      error.value = message
      throw new Error(message)
    }
  }

  async function signOut() {
    try {
      await backendLogout()
    } finally {
      userStore.clearSensitiveData()
      clearAuthState()
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    user,
    csrfToken,
    loading,
    error,
    isAuthenticated,
    applyPayload,
    init,
    dispose,
    signIn,
    signUp,
    signOut,
    clearError,
  }
})
