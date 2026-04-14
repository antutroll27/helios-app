import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    isAuthenticated: true,
    csrfToken: 'csrf-1',
  }),
}))

vi.mock('@/stores/geo', () => ({
  useGeoStore: () => ({
    lat: 1,
    lng: 2,
    timezone: 'UTC',
    locationName: 'Test City',
  }),
}))

vi.mock('@/stores/solar', () => ({
  useSolarStore: () => ({
    solarPhase: 'day',
    elevationDeg: 25,
    sunriseTime: new Date('2026-04-14T06:00:00Z'),
    sunsetTime: new Date('2026-04-14T18:00:00Z'),
    solarNoon: new Date('2026-04-14T12:00:00Z'),
    wakeWindowEnd: new Date('2026-04-14T07:00:00Z'),
  }),
}))

vi.mock('@/stores/spaceWeather', () => ({
  useSpaceWeatherStore: () => ({
    kpIndex: 2,
    disruptionLabel: 'calm',
    bzComponent: -2,
    solarWindSpeed: 320,
    disruptionAdvisory: 'Calm',
  }),
}))

vi.mock('@/stores/environment', () => ({
  useEnvironmentStore: () => ({
    uvIndexNow: 4,
    temperatureNow: 24,
    temperatureNight: 19,
    aqiLevel: 40,
    humidity: 55,
  }),
}))

vi.mock('@/stores/protocol', () => ({
  useProtocolStore: () => ({
    dailyProtocol: {
      wakeWindow: { time: new Date('2026-04-14T06:30:00Z'), endTime: new Date('2026-04-14T07:00:00Z') },
      caffeineCutoff: { time: new Date('2026-04-14T14:00:00Z') },
      peakFocus: { time: new Date('2026-04-14T10:00:00Z') },
      windDown: { time: new Date('2026-04-14T21:00:00Z') },
      sleepWindow: { time: new Date('2026-04-14T23:00:00Z') },
    },
    peakFocusEnd: new Date('2026-04-14T12:00:00Z'),
  }),
}))

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    usualSleepTime: '23:00',
    chronotype: 'intermediate',
  }),
}))

vi.mock('@/lib/chatContext', () => ({
  buildChatContextSnapshot: (payload: unknown) => payload,
}))

vi.mock('@/lib/timezoneUtils', () => ({
  fmtTimeInZone: () => '12:00',
}))

import { useAI } from '@/composables/useAI'

describe('useAI', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        message: 'Hello',
        visual_cards: [],
        session_id: 'session-1',
      }),
    }))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('sends cookie-backed chat requests with csrf headers', async () => {
    const ai = useAI()

    await ai.sendMessage('hello', 'openai', 'key-123', [])

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/chat/send'),
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: expect.objectContaining({
          'X-HELIOS-CSRF': 'csrf-1',
        }),
      }),
    )
  })
})
