import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/lib/backendAuth', () => ({
  me: vi.fn(),
  login: vi.fn(),
  signup: vi.fn(),
  logout: vi.fn(),
}))

import { login, logout, me, signup } from '@/lib/backendAuth'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts logged out with no csrf token', () => {
    const auth = useAuthStore()

    expect(auth.user).toBeNull()
    expect(auth.csrfToken).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('init hydrates user and csrf token from backend me()', async () => {
    vi.mocked(me).mockResolvedValueOnce({
      user: { id: 'u1', email: 'user@example.com' },
      csrfToken: 'csrf-1',
    })
    const auth = useAuthStore()

    await auth.init()

    expect(auth.loading).toBe(false)
    expect(auth.user?.email).toBe('user@example.com')
    expect(auth.csrfToken).toBe('csrf-1')
    expect(auth.isAuthenticated).toBe(true)
  })

  it('init clears state cleanly on backend 401', async () => {
    vi.mocked(me).mockResolvedValueOnce(null)
    const auth = useAuthStore()

    await auth.init()

    expect(auth.isAuthenticated).toBe(false)
    expect(auth.csrfToken).toBeNull()
  })

  it('signIn stores backend user and csrf token', async () => {
    vi.mocked(login).mockResolvedValueOnce({
      user: { id: 'u1', email: 'user@example.com' },
      csrfToken: 'csrf-2',
    })
    const auth = useAuthStore()

    await auth.signIn('user@example.com', 'secret123')

    expect(auth.user?.email).toBe('user@example.com')
    expect(auth.csrfToken).toBe('csrf-2')
  })

  it('signIn sets error and rethrows on failure', async () => {
    vi.mocked(login).mockRejectedValueOnce(new Error('Invalid login credentials'))
    const auth = useAuthStore()

    await expect(auth.signIn('bad@example.com', 'wrong-pass')).rejects.toThrow('Invalid login credentials')
    expect(auth.error).toBe('Invalid login credentials')
  })

  it('signUp preserves logged-out state when confirmation is required', async () => {
    vi.mocked(signup).mockResolvedValueOnce({
      user: { id: 'u2', email: 'new@example.com' },
      requiresConfirmation: true,
    })
    const auth = useAuthStore()

    const result = await auth.signUp('new@example.com', 'secret123')

    expect(result.requiresConfirmation).toBe(true)
    expect(auth.user).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('signOut clears auth state and sensitive user data', async () => {
    vi.mocked(logout).mockResolvedValueOnce()
    const auth = useAuthStore()
    const userStore = useUserStore()
    userStore.apiKey = 'top-secret'
    auth.user = { id: 'u1', email: 'user@example.com' }
    auth.csrfToken = 'csrf-1'

    await auth.signOut()

    expect(auth.user).toBeNull()
    expect(auth.csrfToken).toBeNull()
    expect(userStore.apiKey).toBe('')
  })
})
