import { beforeEach, describe, expect, it, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBiometricsStore } from './biometrics'

// Mock the solar store — it requires geolocation/SunCalc which don't work in Vitest
vi.mock('./solar', () => ({
  useSolarStore: () => ({ solarNoon: new Date('2026-04-12T12:00:00.000Z') })
}))

function makeLogs(overrides: Partial<{
  sleep_onset: string
  wake_time: string
  total_sleep_min: number
}>[] = []) {
  const defaults = {
    sleep_onset: '2026-03-14T23:00:00.000Z',  // 23:00
    wake_time:   '2026-03-15T07:00:00.000Z',  // 07:00
    total_sleep_min: 480,
    source: 'mock' as const,
  }
  return overrides.map((o, i) => ({
    ...defaults,
    ...o,
    date: `2026-03-${String(14 + i).padStart(2, '0')}`,
    deep_sleep_min: 90,
    rem_sleep_min: 110,
  }))
}

describe('Phase A computeds', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns "--:--" for dlmoEstimate when fewer than 3 nights', () => {
    store.logs = makeLogs([{}, {}])
    expect(store.dlmoEstimate).toBe('--:--')
  })

  it('computes dlmoEstimate as avg sleep onset minus 2 hours', () => {
    // avg sleep onset = 23:00 → DLMO = 21:00
    store.logs = makeLogs([{}, {}, {}])
    expect(store.dlmoEstimate).toBe('21:00')
  })

  it('computes caffeineCutoff as avg sleep onset minus 6 hours', () => {
    // avg sleep onset = 23:00 → cutoff = 17:00
    store.logs = makeLogs([{}, {}, {}])
    expect(store.caffeineCutoff).toBe('17:00')
  })

  it('computes napWindow as avg wake time plus 7 hours', () => {
    // avg wake = 07:00 → nap = 14:00
    store.logs = makeLogs([{}, {}, {}])
    expect(store.napWindow).toBe('14:00')
  })

  it('wraps napWindow correctly for late chronotypes', () => {
    // avg wake = 10:00 → nap = 17:00
    const logs = makeLogs([
      { wake_time: '2026-03-15T10:00:00.000Z' },
      { wake_time: '2026-03-16T10:00:00.000Z' },
      { wake_time: '2026-03-17T10:00:00.000Z' },
    ])
    store.logs = logs
    expect(store.napWindow).toBe('17:00')
  })
})

describe('Phase B — sri', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns null when fewer than 7 nights', () => {
    store.logs = makeLogs(Array(6).fill({}))
    expect(store.sri).toBeNull()
  })

  it('returns 100 for perfectly regular sleep (zero deviation)', () => {
    // All nights identical onset/wake → MAD = 0
    store.logs = makeLogs(Array(7).fill({}))
    expect(store.sri).toBe(100)
  })

  it('returns lower SRI when midpoints vary significantly', () => {
    // Mix of early and late midpoints
    const logs = makeLogs([
      { sleep_onset: '2026-03-14T22:00:00.000Z', wake_time: '2026-03-15T06:00:00.000Z' },
      { sleep_onset: '2026-03-15T00:00:00.000Z', wake_time: '2026-03-16T08:00:00.000Z' },
      { sleep_onset: '2026-03-16T22:00:00.000Z', wake_time: '2026-03-17T06:00:00.000Z' },
      { sleep_onset: '2026-03-17T00:00:00.000Z', wake_time: '2026-03-18T08:00:00.000Z' },
      { sleep_onset: '2026-03-18T22:00:00.000Z', wake_time: '2026-03-19T06:00:00.000Z' },
      { sleep_onset: '2026-03-19T00:00:00.000Z', wake_time: '2026-03-20T08:00:00.000Z' },
      { sleep_onset: '2026-03-20T22:00:00.000Z', wake_time: '2026-03-21T06:00:00.000Z' },
    ])
    store.logs = logs
    expect(store.sri).toBeLessThan(100)
    expect(store.sri).toBeGreaterThanOrEqual(0)
  })
})

describe('Phase B — sleepDebtMin', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns negative debt when sleeping less than 480 min/night', () => {
    // 14 nights × (400 - 480) = -1120 min
    store.logs = makeLogs(Array(14).fill({ total_sleep_min: 400 }))
    expect(store.sleepDebtMin).toBe(-1120)
  })

  it('returns positive surplus when sleeping more than 480 min/night', () => {
    store.logs = makeLogs(Array(14).fill({ total_sleep_min: 500 }))
    expect(store.sleepDebtMin).toBe(280)
  })

  it('uses raw logs (last 14), not windowedLogs — unaffected by dateRange toggle', () => {
    // 20 logs total. dateRange is 7 by default.
    // Debt should use last 14 logs, not last 7.
    store.logs = makeLogs([
      ...Array(6).fill({ total_sleep_min: 600 }),  // surplus nights (not in last 14)
      ...Array(14).fill({ total_sleep_min: 400 }),  // deficit nights (in last 14)
    ])
    // 14 × (400 - 480) = -1120
    expect(store.sleepDebtMin).toBe(-1120)
  })
})

describe('Phase B — sleepDebtSeries', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns per-night deviation from 480 min target', () => {
    store.logs = makeLogs([
      { total_sleep_min: 480 },  // 0 deviation
      { total_sleep_min: 420 },  // -60
      { total_sleep_min: 510 },  // +30
    ])
    const vals = store.sleepDebtSeries.map(s => s.value)
    expect(vals).toEqual([0, -60, 30])
  })
})

describe('Phase B — sriSeries', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns null for entries where fewer than 7 nights are in the window', () => {
    store.logs = makeLogs(Array(10).fill({}))
    const series = store.sriSeries
    // First 6 entries (indices 0-5) have windows of size 1-6 → null
    expect(series[0].value).toBeNull()
    expect(series[5].value).toBeNull()
    // Entry at index 6 has a 7-night window → should have a value
    expect(series[6].value).not.toBeNull()
  })

  it('returns 100 for perfectly regular sleep', () => {
    // All identical → MAD = 0 → SRI = 100
    store.logs = makeLogs(Array(10).fill({}))
    const series = store.sriSeries
    const withValues = series.filter(s => s.value !== null)
    withValues.forEach(s => expect(s.value).toBe(100))
  })
})

describe('Phase B — dialData', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns null when fewer than 3 nights', () => {
    store.logs = makeLogs([{}, {}])
    expect(store.dialData).toBeNull()
  })

  it('returns non-null dial data with 3+ nights', () => {
    store.logs = makeLogs([{}, {}, {}])
    expect(store.dialData).not.toBeNull()
  })

  it('sleep window start angle = (avgOnsetMinutes / 1440) * 360', () => {
    // avg onset = 23:00 = 1380 min → angle = (1380/1440)*360 = 345°
    store.logs = makeLogs([{}, {}, {}])
    expect(store.dialData!.sleepWindowStart).toBeCloseTo(345, 0)
  })

  it('uses solar noon fallback (720 min = 180°) when solarNoon unavailable', () => {
    // The mock returns solarNoon = 12:00 UTC = 720 min → angle = 180°
    store.logs = makeLogs([{}, {}, {}])
    expect(store.dialData!.solarNoonAngle).toBeCloseTo(180, 0)
  })
})
