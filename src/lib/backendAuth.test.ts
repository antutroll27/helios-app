import { afterEach, describe, expect, it, vi } from 'vitest'

import { getOAuthStartUrl, login, logout, me, signup } from '@/lib/backendAuth'

describe('backendAuth client', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('calls login with credentials included', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        user: { id: 'u1', email: 'user@example.com' },
        csrfToken: 'csrf-1',
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await login('user@example.com', 'secret123')

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/auth/login'),
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      }),
    )
  })

  it('returns null from me() on 401', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({}),
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(me()).resolves.toBeNull()
  })

  it('posts signup and logout with cookie credentials', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user: { id: 'u2', email: 'new@example.com' },
          requiresConfirmation: true,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ok: true }),
      })
    vi.stubGlobal('fetch', fetchMock)

    await signup('new@example.com', 'secret123')
    await logout()

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining('/api/auth/signup'),
      expect.objectContaining({ credentials: 'include' }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('/api/auth/logout'),
      expect.objectContaining({ method: 'POST', credentials: 'include' }),
    )
  })

  it('builds a backend-owned OAuth start URL', () => {
    vi.stubGlobal('location', { origin: 'http://localhost:5173' })

    const url = getOAuthStartUrl('google', '/lab')

    expect(url).toContain('/api/auth/oauth/start?')
    expect(url).toContain('provider=google')
    expect(url).toContain('redirect=%2Flab')
    expect(url).toContain('return_origin=http%3A%2F%2Flocalhost%3A5173')
  })
})
