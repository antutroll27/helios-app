import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/lib/publicApi', () => ({
  fetchPublicJson: vi.fn(),
}))

import { fetchPublicJson } from '@/lib/publicApi'
import { useDonkiStore } from './donki'

describe('useDonkiStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('hydrates DONKI state from the backend public route payload', async () => {
    vi.mocked(fetchPublicJson).mockResolvedValue({
      upcoming_cmes: [{ time21_5: '2026-04-14T00:00:00Z' }],
      recent_storms: [{ gstID: 'gst-1' }],
      active_flares: [{ flrID: 'flr-1' }],
      notifications: [{ messageID: 'note-1', messageType: 'GST' }],
      next_geostorm_eta_hours: 18.5,
    })

    const store = useDonkiStore()
    await store.fetchAll()

    expect(fetchPublicJson).toHaveBeenCalledWith('/donki/summary')
    expect(store.upcomingCMEs).toHaveLength(1)
    expect(store.recentStorms).toHaveLength(1)
    expect(store.activeFlares).toHaveLength(1)
    expect(store.notifications).toHaveLength(1)
    expect(store.nextGeostormEta).toBe(18.5)
    expect(store.error).toBeNull()
  })
})
