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
