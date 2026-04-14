import { afterEach, describe, expect, it, vi } from 'vitest'

describe('fetchPublicJson', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  it('uses the backend public route base url', async () => {
    vi.stubEnv('VITE_BACKEND_URL', 'https://backend.example')
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ ok: true }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const { fetchPublicJson } = await import('./publicApi')
    await fetchPublicJson('/environment?lat=1&lng=2')

    expect(fetchMock).toHaveBeenCalledWith(
      'https://backend.example/api/public/environment?lat=1&lng=2',
      expect.objectContaining({ method: 'GET' })
    )
  })
})
