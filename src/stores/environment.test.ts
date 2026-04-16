import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/lib/publicApi', () => ({
  fetchPublicJson: vi.fn(),
}))

import { fetchPublicJson } from '@/lib/publicApi'
import { useEnvironmentStore } from './environment'

describe('useEnvironmentStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('hydrates environment state from the backend public route payload', async () => {
    vi.mocked(fetchPublicJson).mockResolvedValue({
      uv_index_now: 0,
      uv_index_max: 7,
      temperature_now: 25,
      temperature_night: 21,
      humidity: 82,
      sunshine_duration_min: 430,
      aqi_level: 61,
      aqi_label: 'Moderate',
      pm25: 19,
    })

    const store = useEnvironmentStore()
    await store.fetchAll(22.5, 88.3)

    expect(fetchPublicJson).toHaveBeenCalledWith('/environment?lat=22.5&lng=88.3')
    expect(store.temperatureNow).toBe(25)
    expect(store.temperatureNight).toBe(21)
    expect(store.aqiLabel).toBe('Moderate')
    expect(store.pm25).toBe(19)
    expect(store.error).toBeNull()
  })
})
