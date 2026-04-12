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
    if (_subscription) return  // already initialized — prevent duplicate listeners
    loading.value = true
    supabase.auth.getSession().then(({ data }) => {
      session.value = data.session
      user.value    = data.session?.user ?? null
      loading.value = false
    }).catch(() => {
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
    if (insertError && insertError.code !== '23505') {
      // '23505' = PostgreSQL unique_violation (duplicate key) — expected on re-signup before confirmation
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
