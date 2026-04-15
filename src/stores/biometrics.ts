import { defineStore } from 'pinia'
import { ref, computed, onScopeDispose } from 'vue'
import { useSolarStore } from './solar'

export interface SleepLog {
  date: string              // "YYYY-MM-DD"
  sleep_onset: string       // ISO datetime string
  wake_time: string         // ISO datetime string
  total_sleep_min: number
  deep_sleep_min?: number
  rem_sleep_min?: number
  hrv_avg?: number          // rMSSD in ms
  skin_temp_delta?: number  // °C from baseline
  resting_hr?: number       // bpm
  sleep_score?: number      // 0-100
  source: 'oura' | 'fitbit' | 'manual' | 'mock'
}

export interface CircadianInsight {
  id: string
  type: 'correlation' | 'trend' | 'adherence' | 'anomaly'
  title: string
  body: string
  accent: string            // hex color
  metric: string
  confidence: 'low' | 'medium' | 'high'
}

export interface ProtocolAdherenceDay {
  date: string
  sleep_delta_min: number   // positive = slept later than target
  wake_delta_min: number    // positive = woke later than target
  adherence_pct: number     // 0-100
}

export type DateRange = 7 | 30
export type UploadStatus = 'idle' | 'parsing' | 'success' | 'error'

// ---------------------------------------------------------------------------
// MOCK_KP_HISTORY — Record<dateString, kpValue>
// 30 nights ending 2026-04-15 (today). 4 high-Kp nights (kp > 3) match the
// 4 low-HRV nights in MOCK_SLEEP_LOGS (nights 5, 12, 19, 26 = Mar 20, Mar 27,
// Apr 3, Apr 10).
// ---------------------------------------------------------------------------

const MOCK_KP_HISTORY: Record<string, number> = {
  '2026-03-16': 1.3,
  '2026-03-17': 0.9,
  '2026-03-18': 2.1,
  '2026-03-19': 1.7,
  '2026-03-20': 4.5, // HIGH — night 5, hrv ~50ms (8ms below mean ~58ms)
  '2026-03-21': 1.4,
  '2026-03-22': 2.6,
  '2026-03-23': 1.1,
  '2026-03-24': 2.9,
  '2026-03-25': 1.8,
  '2026-03-26': 2.2,
  '2026-03-27': 5.1, // HIGH — night 12, hrv ~50ms
  '2026-03-28': 1.2,
  '2026-03-29': 1.6,
  '2026-03-30': 2.4,
  '2026-03-31': 1.0,
  '2026-04-01': 2.7,
  '2026-04-02': 1.5,
  '2026-04-03': 4.8, // HIGH — night 19, hrv ~50ms
  '2026-04-04': 0.9,
  '2026-04-05': 1.3,
  '2026-04-06': 2.0,
  '2026-04-07': 1.9,
  '2026-04-08': 0.8,
  '2026-04-09': 2.3,
  '2026-04-10': 5.3, // HIGH — night 26, hrv ~50ms
  '2026-04-11': 1.4,
  '2026-04-12': 0.8,
  '2026-04-13': 1.6,
  '2026-04-14': 2.1,
}

// ---------------------------------------------------------------------------
// MOCK_SLEEP_LOGS — 30 contiguous nights ending 2026-04-14
// Dates run from 2026-03-16 to 2026-04-14.
//
// Night numbering (1-indexed):
//   Night 1  = 2026-03-16
//   Night 5  = 2026-03-20 — hrv_avg ~50ms (8ms below mean ~58ms), HIGH Kp
//   Night 8  = 2026-03-23 — hrv_avg: undefined (device not worn)
//   Night 10 = 2026-03-25 — late sleep (≥60 min after 23:00), sleep_score < 65
//   Night 12 = 2026-03-27 — hrv_avg ~50ms (8ms below mean), HIGH Kp
//   Night 15 = 2026-03-30 — outlier: total_sleep_min=310, sleep_score=48
//   Night 19 = 2026-04-03 — hrv_avg ~50ms (8ms below mean), HIGH Kp
//   Night 22 = 2026-04-06 — hrv_avg: undefined (device not worn)
//   Night 24 = 2026-04-08 — late sleep (≥60 min after 23:00), sleep_score < 65
//   Night 26 = 2026-04-10 — hrv_avg ~50ms (8ms below mean), HIGH Kp
//   All others: realistic variation
// ---------------------------------------------------------------------------

const MOCK_SLEEP_LOGS: SleepLog[] = [
  // Night 1 — 2026-03-16, normal
  {
    date: '2026-03-16',
    sleep_onset: '2026-03-16T23:08:00.000Z',
    wake_time: '2026-03-17T06:52:00.000Z',
    total_sleep_min: 464,
    deep_sleep_min: 88,
    rem_sleep_min: 112,
    hrv_avg: 59,
    skin_temp_delta: 0.1,
    resting_hr: 55,
    sleep_score: 82,
    source: 'mock',
  },
  // Night 2 — 2026-03-17, normal
  {
    date: '2026-03-17',
    sleep_onset: '2026-03-17T22:54:00.000Z',
    wake_time: '2026-03-18T07:06:00.000Z',
    total_sleep_min: 492,
    deep_sleep_min: 86,
    rem_sleep_min: 118,
    hrv_avg: 61,
    skin_temp_delta: 0.0,
    resting_hr: 53,
    sleep_score: 85,
    source: 'mock',
  },
  // Night 3 — 2026-03-18, normal
  {
    date: '2026-03-18',
    sleep_onset: '2026-03-18T23:12:00.000Z',
    wake_time: '2026-03-19T07:04:00.000Z',
    total_sleep_min: 472,
    deep_sleep_min: 82,
    rem_sleep_min: 109,
    hrv_avg: 57,
    skin_temp_delta: -0.1,
    resting_hr: 57,
    sleep_score: 79,
    source: 'mock',
  },
  // Night 4 — 2026-03-19, normal
  {
    date: '2026-03-19',
    sleep_onset: '2026-03-19T23:05:00.000Z',
    wake_time: '2026-03-20T07:10:00.000Z',
    total_sleep_min: 485,
    deep_sleep_min: 90,
    rem_sleep_min: 115,
    hrv_avg: 60,
    skin_temp_delta: 0.0,
    resting_hr: 54,
    sleep_score: 84,
    source: 'mock',
  },
  // Night 5 — 2026-03-20, HIGH Kp (4.5) → low HRV (~50ms, ~8ms below mean)
  {
    date: '2026-03-20',
    sleep_onset: '2026-03-20T23:18:00.000Z',
    wake_time: '2026-03-21T07:02:00.000Z',
    total_sleep_min: 464,
    deep_sleep_min: 70,
    rem_sleep_min: 96,
    hrv_avg: 50,
    skin_temp_delta: 0.2,
    resting_hr: 61,
    sleep_score: 72,
    source: 'mock',
  },
  // Night 6 — 2026-03-21, normal
  {
    date: '2026-03-21',
    sleep_onset: '2026-03-21T23:05:00.000Z',
    wake_time: '2026-03-22T07:08:00.000Z',
    total_sleep_min: 483,
    deep_sleep_min: 85,
    rem_sleep_min: 115,
    hrv_avg: 59,
    skin_temp_delta: 0.0,
    resting_hr: 55,
    sleep_score: 83,
    source: 'mock',
  },
  // Night 7 — 2026-03-22, normal
  {
    date: '2026-03-22',
    sleep_onset: '2026-03-22T23:16:00.000Z',
    wake_time: '2026-03-23T07:22:00.000Z',
    total_sleep_min: 486,
    deep_sleep_min: 84,
    rem_sleep_min: 114,
    hrv_avg: 62,
    skin_temp_delta: 0.1,
    resting_hr: 56,
    sleep_score: 80,
    source: 'mock',
  },
  // Night 8 — 2026-03-23, no device (hrv_avg undefined)
  {
    date: '2026-03-23',
    sleep_onset: '2026-03-23T23:04:00.000Z',
    wake_time: '2026-03-24T07:02:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 80,
    rem_sleep_min: 108,
    hrv_avg: undefined,
    skin_temp_delta: undefined,
    resting_hr: undefined,
    sleep_score: undefined,
    source: 'mock',
  },
  // Night 9 — 2026-03-24, normal
  {
    date: '2026-03-24',
    sleep_onset: '2026-03-24T22:58:00.000Z',
    wake_time: '2026-03-25T07:08:00.000Z',
    total_sleep_min: 490,
    deep_sleep_min: 88,
    rem_sleep_min: 122,
    hrv_avg: 63,
    skin_temp_delta: -0.2,
    resting_hr: 52,
    sleep_score: 87,
    source: 'mock',
  },
  // Night 10 — 2026-03-25, LATE SLEEP (00:15 → 75 min past 23:00), sleep_score < 65
  {
    date: '2026-03-25',
    sleep_onset: '2026-03-26T00:15:00.000Z',
    wake_time: '2026-03-26T07:45:00.000Z',
    total_sleep_min: 450,
    deep_sleep_min: 70,
    rem_sleep_min: 100,
    hrv_avg: 53,
    skin_temp_delta: 0.3,
    resting_hr: 60,
    sleep_score: 62,
    source: 'mock',
  },
  // Night 11 — 2026-03-26, normal
  {
    date: '2026-03-26',
    sleep_onset: '2026-03-26T23:10:00.000Z',
    wake_time: '2026-03-27T07:00:00.000Z',
    total_sleep_min: 470,
    deep_sleep_min: 83,
    rem_sleep_min: 110,
    hrv_avg: 58,
    skin_temp_delta: 0.0,
    resting_hr: 55,
    sleep_score: 81,
    source: 'mock',
  },
  // Night 12 — 2026-03-27, HIGH Kp (5.1) → low HRV (~50ms)
  {
    date: '2026-03-27',
    sleep_onset: '2026-03-27T23:28:00.000Z',
    wake_time: '2026-03-28T07:14:00.000Z',
    total_sleep_min: 466,
    deep_sleep_min: 68,
    rem_sleep_min: 94,
    hrv_avg: 50,
    skin_temp_delta: 0.3,
    resting_hr: 62,
    sleep_score: 70,
    source: 'mock',
  },
  // Night 13 — 2026-03-28, normal
  {
    date: '2026-03-28',
    sleep_onset: '2026-03-28T23:10:00.000Z',
    wake_time: '2026-03-29T07:00:00.000Z',
    total_sleep_min: 470,
    deep_sleep_min: 80,
    rem_sleep_min: 110,
    hrv_avg: 56,
    skin_temp_delta: 0.0,
    resting_hr: 55,
    sleep_score: 81,
    source: 'mock',
  },
  // Night 14 — 2026-03-29, normal
  {
    date: '2026-03-29',
    sleep_onset: '2026-03-29T22:56:00.000Z',
    wake_time: '2026-03-30T07:04:00.000Z',
    total_sleep_min: 488,
    deep_sleep_min: 89,
    rem_sleep_min: 124,
    hrv_avg: 64,
    skin_temp_delta: -0.2,
    resting_hr: 52,
    sleep_score: 88,
    source: 'mock',
  },
  // Night 15 — 2026-03-30, OUTLIER (short sleep, poor score)
  {
    date: '2026-03-30',
    sleep_onset: '2026-03-31T01:05:00.000Z',
    wake_time: '2026-03-31T06:17:00.000Z',
    total_sleep_min: 310,
    deep_sleep_min: 50,
    rem_sleep_min: 70,
    hrv_avg: 44,
    skin_temp_delta: 0.4,
    resting_hr: 64,
    sleep_score: 48,
    source: 'mock',
  },
  // Night 16 — 2026-03-31, normal
  {
    date: '2026-03-31',
    sleep_onset: '2026-03-31T23:02:00.000Z',
    wake_time: '2026-04-01T07:00:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 83,
    rem_sleep_min: 115,
    hrv_avg: 60,
    skin_temp_delta: -0.1,
    resting_hr: 55,
    sleep_score: 84,
    source: 'mock',
  },
  // Night 17 — 2026-04-01, normal
  {
    date: '2026-04-01',
    sleep_onset: '2026-04-01T23:08:00.000Z',
    wake_time: '2026-04-02T07:10:00.000Z',
    total_sleep_min: 482,
    deep_sleep_min: 85,
    rem_sleep_min: 114,
    hrv_avg: 58,
    skin_temp_delta: 0.0,
    resting_hr: 56,
    sleep_score: 82,
    source: 'mock',
  },
  // Night 18 — 2026-04-02, normal
  {
    date: '2026-04-02',
    sleep_onset: '2026-04-02T23:14:00.000Z',
    wake_time: '2026-04-03T07:12:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 81,
    rem_sleep_min: 110,
    hrv_avg: 61,
    skin_temp_delta: 0.1,
    resting_hr: 54,
    sleep_score: 80,
    source: 'mock',
  },
  // Night 19 — 2026-04-03, HIGH Kp (4.8) → low HRV (~50ms)
  {
    date: '2026-04-03',
    sleep_onset: '2026-04-03T23:30:00.000Z',
    wake_time: '2026-04-04T07:18:00.000Z',
    total_sleep_min: 468,
    deep_sleep_min: 66,
    rem_sleep_min: 92,
    hrv_avg: 50,
    skin_temp_delta: 0.3,
    resting_hr: 63,
    sleep_score: 71,
    source: 'mock',
  },
  // Night 20 — 2026-04-04, normal
  {
    date: '2026-04-04',
    sleep_onset: '2026-04-04T23:04:00.000Z',
    wake_time: '2026-04-05T07:06:00.000Z',
    total_sleep_min: 482,
    deep_sleep_min: 86,
    rem_sleep_min: 116,
    hrv_avg: 59,
    skin_temp_delta: -0.1,
    resting_hr: 54,
    sleep_score: 83,
    source: 'mock',
  },
  // Night 21 — 2026-04-05, normal
  {
    date: '2026-04-05',
    sleep_onset: '2026-04-05T23:16:00.000Z',
    wake_time: '2026-04-06T07:14:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 84,
    rem_sleep_min: 113,
    hrv_avg: 57,
    skin_temp_delta: 0.2,
    resting_hr: 56,
    sleep_score: 79,
    source: 'mock',
  },
  // Night 22 — 2026-04-06, no device (hrv_avg undefined)
  {
    date: '2026-04-06',
    sleep_onset: '2026-04-06T23:00:00.000Z',
    wake_time: '2026-04-07T07:05:00.000Z',
    total_sleep_min: 485,
    deep_sleep_min: 82,
    rem_sleep_min: 110,
    hrv_avg: undefined,
    skin_temp_delta: undefined,
    resting_hr: undefined,
    sleep_score: undefined,
    source: 'mock',
  },
  // Night 23 — 2026-04-07, normal
  {
    date: '2026-04-07',
    sleep_onset: '2026-04-07T23:12:00.000Z',
    wake_time: '2026-04-08T07:02:00.000Z',
    total_sleep_min: 470,
    deep_sleep_min: 80,
    rem_sleep_min: 110,
    hrv_avg: 62,
    skin_temp_delta: 0.1,
    resting_hr: 57,
    sleep_score: 79,
    source: 'mock',
  },
  // Night 24 — 2026-04-08, LATE SLEEP (00:30 → 90 min past 23:00), sleep_score < 65
  {
    date: '2026-04-08',
    sleep_onset: '2026-04-09T00:30:00.000Z',
    wake_time: '2026-04-09T07:52:00.000Z',
    total_sleep_min: 442,
    deep_sleep_min: 68,
    rem_sleep_min: 95,
    hrv_avg: 54,
    skin_temp_delta: 0.3,
    resting_hr: 61,
    sleep_score: 60,
    source: 'mock',
  },
  // Night 25 — 2026-04-09, normal
  {
    date: '2026-04-09',
    sleep_onset: '2026-04-09T23:06:00.000Z',
    wake_time: '2026-04-10T07:04:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 83,
    rem_sleep_min: 113,
    hrv_avg: 59,
    skin_temp_delta: 0.0,
    resting_hr: 55,
    sleep_score: 83,
    source: 'mock',
  },
  // Night 26 — 2026-04-10, HIGH Kp (5.3) → low HRV (~50ms)
  {
    date: '2026-04-10',
    sleep_onset: '2026-04-10T23:22:00.000Z',
    wake_time: '2026-04-11T07:08:00.000Z',
    total_sleep_min: 466,
    deep_sleep_min: 67,
    rem_sleep_min: 95,
    hrv_avg: 50,
    skin_temp_delta: 0.3,
    resting_hr: 62,
    sleep_score: 70,
    source: 'mock',
  },
  // Night 27 — 2026-04-11, normal
  {
    date: '2026-04-11',
    sleep_onset: '2026-04-11T22:58:00.000Z',
    wake_time: '2026-04-12T07:06:00.000Z',
    total_sleep_min: 488,
    deep_sleep_min: 87,
    rem_sleep_min: 121,
    hrv_avg: 63,
    skin_temp_delta: -0.2,
    resting_hr: 53,
    sleep_score: 86,
    source: 'mock',
  },
  // Night 28 — 2026-04-12, normal
  {
    date: '2026-04-12',
    sleep_onset: '2026-04-12T23:10:00.000Z',
    wake_time: '2026-04-13T07:08:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 82,
    rem_sleep_min: 112,
    hrv_avg: 60,
    skin_temp_delta: 0.1,
    resting_hr: 56,
    sleep_score: 82,
    source: 'mock',
  },
  // Night 29 — 2026-04-13, normal
  {
    date: '2026-04-13',
    sleep_onset: '2026-04-13T23:04:00.000Z',
    wake_time: '2026-04-14T07:02:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 85,
    rem_sleep_min: 114,
    hrv_avg: 61,
    skin_temp_delta: -0.1,
    resting_hr: 54,
    sleep_score: 83,
    source: 'mock',
  },
  // Night 30 — 2026-04-14, normal (last night before today 2026-04-15)
  {
    date: '2026-04-14',
    sleep_onset: '2026-04-14T23:18:00.000Z',
    wake_time: '2026-04-15T07:10:00.000Z',
    total_sleep_min: 472,
    deep_sleep_min: 83,
    rem_sleep_min: 111,
    hrv_avg: 57,
    skin_temp_delta: 0.0,
    resting_hr: 56,
    sleep_score: 80,
    source: 'mock',
  },
]

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useBiometricsStore = defineStore('biometrics', () => {
  const logs = ref<SleepLog[]>([])
  const dateRange = ref<DateRange>(7)
  const uploadStatus = ref<UploadStatus>('idle')
  const uploadError = ref<string | null>(null)
  const dataSource = ref<'mock' | 'uploaded'>('mock')

  // ---------------------------------------------------------------------------
  // Helpers (store-scoped, not exported)
  // ---------------------------------------------------------------------------

  // Parses ISO datetime ("2026-03-14T23:10:00.000Z") → minutes since midnight
  // Reads raw UTC digits at index 11–15 so mock data "intended local time" is
  // not shifted by the browser's local timezone offset.
  function isoToMin(iso: string): number {
    const h = parseInt(iso.slice(11, 13), 10)
    const m = parseInt(iso.slice(14, 16), 10)
    return h * 60 + m
  }

  // Parses "HH:MM" or ISO datetime → minutes since midnight
  // WARNING: do NOT use timeToMinutes inside protocolAdherence — use isoToMin
  // instead. timeToMinutes applies the browser's local timezone offset on full
  // ISO strings, which produces incorrect deltas for the post-midnight shift logic.
  function timeToMinutes(s: string): number {
    const hhmm = s.length > 5 ? s.slice(11, 16) : s
    const [h, m] = hhmm.split(':').map(Number)
    return h * 60 + m
  }

  // Minutes since midnight → "HH:MM", wraps at 1440
  function minutesToTime(min: number): string {
    const wrapped = ((min % 1440) + 1440) % 1440
    const h = Math.floor(wrapped / 60).toString().padStart(2, '0')
    const m = Math.floor(wrapped % 60).toString().padStart(2, '0')
    return `${h}:${m}`
  }

  function helperAvg(nums: number[]): number {
    if (nums.length === 0) return 0
    return nums.reduce((a, b) => a + b, 0) / nums.length
  }

  // ---------------------------------------------------------------------------
  // Live now-angle (updates every 60s for the body clock dial needle)
  // ---------------------------------------------------------------------------
  const nowAngle = ref<number>(
    ((new Date().getHours() * 60 + new Date().getMinutes()) / 1440) * 360
  )
  // Keep the handle so Vitest tests can call clearInterval(_nowTimer) to avoid leaks
  const _nowTimer = setInterval(() => {
    nowAngle.value = ((new Date().getHours() * 60 + new Date().getMinutes()) / 1440) * 360
  }, 60_000)
  onScopeDispose(() => clearInterval(_nowTimer))

  // Instantiate solar store at setup level (not inside computed) for testability
  const solarStore = useSolarStore()

  // ---------------------------------------------------------------------------
  // Phase A — scalar circadian timing computeds
  // ---------------------------------------------------------------------------

  // DLMO estimate: avg sleep onset − 2h (Czeisler & Gooley 2007)
  const dlmoEstimate = computed<string>(() => {
    const valid = logs.value.filter(l => l.sleep_onset)
    if (valid.length < 3) return '--:--'
    const avgOnsetMin = helperAvg(valid.map(l => timeToMinutes(l.sleep_onset)))
    return minutesToTime(avgOnsetMin - 120)
  })

  // Caffeine cutoff: avg sleep onset − 6h (Drake et al. 2013)
  const caffeineCutoff = computed<string>(() => {
    const valid = logs.value.filter(l => l.sleep_onset)
    if (valid.length < 3) return '--:--'
    const avgOnsetMin = helperAvg(valid.map(l => timeToMinutes(l.sleep_onset)))
    return minutesToTime(avgOnsetMin - 360)
  })

  // Nap window: avg wake time + 7h (Dinges 1992 post-lunch dip)
  const napWindow = computed<string>(() => {
    const valid = logs.value.filter(l => l.wake_time)
    if (valid.length < 3) return '--:--'
    const avgWakeMin = helperAvg(valid.map(l => timeToMinutes(l.wake_time)))
    return minutesToTime(avgWakeMin + 420)
  })

  // ---------------------------------------------------------------------------
  // Phase B — Sleep Regularity Index (adapted from Windred et al. 2024)
  // ---------------------------------------------------------------------------

  // SRI scalar: 0–100. Null if fewer than 7 nights.
  const sri = computed<number | null>(() => {
    const valid = logs.value.filter(l => l.sleep_onset && l.wake_time)
    if (valid.length < 7) return null
    const midpoints = valid.map(l => (timeToMinutes(l.sleep_onset) + timeToMinutes(l.wake_time)) / 2)
    const meanMid = helperAvg(midpoints)
    const mad = helperAvg(midpoints.map(m => Math.abs(m - meanMid)))
    return Math.max(0, Math.round(100 - (mad / 120) * 100))
  })

  // SRI 30-day series — sliding 7-night window, one value per day
  const sriSeries = computed<{ date: string; value: number | null }[]>(() => {
    const all = logs.value.filter(l => l.sleep_onset && l.wake_time)
    const startIdx = Math.max(0, all.length - 30)
    const last30 = all.slice(startIdx)
    return last30.map((entry, i) => {
      const absIdx = startIdx + i
      const window = all.slice(Math.max(0, absIdx - 6), absIdx + 1)
      if (window.length < 7) return { date: entry.date, value: null }
      const midpoints = window.map(l => (timeToMinutes(l.sleep_onset) + timeToMinutes(l.wake_time)) / 2)
      const meanMid = helperAvg(midpoints)
      const mad = helperAvg(midpoints.map(m => Math.abs(m - meanMid)))
      return { date: entry.date, value: Math.max(0, Math.round(100 - (mad / 120) * 100)) }
    })
  })

  // ---------------------------------------------------------------------------
  // Phase B — Sleep Debt (rolling 14-day, always uses raw logs not windowedLogs)
  // ---------------------------------------------------------------------------

  const SLEEP_TARGET_MIN = 480  // 8 hours
  const TARGET_SLEEP_MIN = 23 * 60  // 23:00 = 1380 (protocol target sleep onset)

  // Total accumulated debt over the last 14 nights (positive = surplus, negative = deficit)
  const sleepDebtMin = computed<number>(() => {
    return logs.value.slice(-14).reduce((acc, l) => acc + (l.total_sleep_min - SLEEP_TARGET_MIN), 0)
  })

  // Per-night deviation series for sparkline
  const sleepDebtSeries = computed<{ date: string; value: number }[]>(() => {
    return logs.value.slice(-14).map(l => ({
      date: l.date,
      value: l.total_sleep_min - SLEEP_TARGET_MIN
    }))
  })

  // ---------------------------------------------------------------------------
  // Phase B — Body Clock Dial data
  // ---------------------------------------------------------------------------

  interface DialData {
    sleepWindowStart: number
    sleepWindowEnd:   number
    peakAlertStart:   number
    peakAlertEnd:     number
    dlmoAngle:        number
    solarNoonAngle:   number
  }

  const dialData = computed<DialData | null>(() => {
    if (dlmoEstimate.value === '--:--') return null
    const validOnset = logs.value.filter(l => l.sleep_onset)
    const validWake  = logs.value.filter(l => l.wake_time)
    if (validOnset.length < 3 || validWake.length < 3) return null

    const toAngle = (min: number) => (min / 1440) * 360
    const avgOnsetMin = helperAvg(validOnset.map(l => timeToMinutes(l.sleep_onset)))
    const avgWakeMin  = helperAvg(validWake.map(l => timeToMinutes(l.wake_time)))

    const solarNoonDate = solarStore.solarNoon
    const solarNoonMin  = solarNoonDate instanceof Date
      ? solarNoonDate.getUTCHours() * 60 + solarNoonDate.getUTCMinutes()
      : 720  // fallback: noon

    return {
      sleepWindowStart: toAngle(avgOnsetMin),
      sleepWindowEnd:   toAngle(avgWakeMin),
      peakAlertStart:   toAngle(avgWakeMin + 120),
      peakAlertEnd:     toAngle(avgWakeMin + 600),
      dlmoAngle:        toAngle(timeToMinutes(dlmoEstimate.value)),
      solarNoonAngle:   toAngle(solarNoonMin),
    }
  })

  // ---------------------------------------------------------------------------
  // Windowed logs — last N nights based on dateRange
  // ---------------------------------------------------------------------------

  const windowedLogs = computed<SleepLog[]>(() => {
    return logs.value.slice(-dateRange.value)
  })

  // ---------------------------------------------------------------------------
  // Chart series — all use null (not undefined) for missing values
  // ---------------------------------------------------------------------------

  // HRV series: null where hrv_avg is undefined
  const hrvSeries = computed(() => ({
    dates: windowedLogs.value.map(l => l.date.slice(5)),  // "MM-DD"
    values: windowedLogs.value.map(l => l.hrv_avg ?? null)
  }))

  // Kp overlay matching same dates as windowedLogs — Record<string, number> lookup
  const kpOverlaySeries = computed(() => {
    const wDates = windowedLogs.value.map(l => l.date)
    return {
      dates: wDates.map(d => d.slice(5)),
      kp: wDates.map(d => MOCK_KP_HISTORY[d] ?? 0.0)
    }
  })

  // Sleep architecture: deep / rem / light (clamped ≥ 0)
  const sleepArchitectureSeries = computed(() => {
    const w = windowedLogs.value
    return {
      dates: w.map(l => l.date.slice(5)),
      deep: w.map(l => l.deep_sleep_min ?? 0),
      rem: w.map(l => l.rem_sleep_min ?? 0),
      light: w.map(l => Math.max(0, l.total_sleep_min - (l.deep_sleep_min ?? 0) - (l.rem_sleep_min ?? 0)))
    }
  })

  // Sleep score series: null for gaps
  const sleepScoreSeries = computed(() => ({
    dates: windowedLogs.value.map(l => l.date.slice(5)),
    values: windowedLogs.value.map(l => l.sleep_score ?? null)
  }))

  // Resting HR series: null for gaps
  const restingHRSeries = computed(() => ({
    dates: windowedLogs.value.map(l => l.date.slice(5)),
    values: windowedLogs.value.map(l => l.resting_hr ?? null)
  }))

  // Skin temp delta series: null for gaps
  const skinTempSeries = computed(() => ({
    dates: windowedLogs.value.map(l => l.date.slice(5)),
    values: windowedLogs.value.map(l => l.skin_temp_delta ?? null)
  }))

  // ---------------------------------------------------------------------------
  // Summary KPIs (mean of non-null values in window)
  // ---------------------------------------------------------------------------

  const avgHRV = computed<number | null>(() => {
    const vals = windowedLogs.value.map(l => l.hrv_avg).filter((v): v is number => v != null)
    return vals.length ? +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : null
  })

  const avgSleepScore = computed<number | null>(() => {
    const vals = windowedLogs.value.map(l => l.sleep_score).filter((v): v is number => v != null)
    return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : null
  })

  const avgRestingHR = computed<number | null>(() => {
    const vals = windowedLogs.value.map(l => l.resting_hr).filter((v): v is number => v != null)
    return vals.length ? +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : null
  })

  const avgTotalSleepH = computed<number | null>(() => {
    const vals = windowedLogs.value.map(l => l.total_sleep_min)
    return vals.length ? +(vals.reduce((a, b) => a + b, 0) / vals.length / 60).toFixed(1) : null
  })

  // ---------------------------------------------------------------------------
  // Protocol adherence
  // Target sleep = 23:00; target wake = sleep onset + 8h (hardcoded for now).
  // Per spec: sleep_delta_min = actual_sleep_min_from_midnight − target_sleep_min
  //           wake_delta_min  = actual_wake_min_from_midnight  − target_wake_min
  //           adherence_pct   = round((1 − clamp(avg|delta|, 0, 120) / 120) × 100)
  //
  // Post-midnight times (< 12:00) are shifted +1440 so they compare correctly
  // against the 23:00 target (e.g. 00:15 → 1455, delta = +75).
  // ---------------------------------------------------------------------------

  const protocolAdherence = computed<ProtocolAdherenceDay[]>(() => {
    return windowedLogs.value.map(l => {
      let actualSleepMin = isoToMin(l.sleep_onset)
      // Post-midnight times (< noon) shift to next-day scale so delta is correct
      if (actualSleepMin < 12 * 60) actualSleepMin += 24 * 60

      const sleepDelta = actualSleepMin - TARGET_SLEEP_MIN

      // Target wake = 07:00 = 420 min from midnight
      const targetWakeMin = 7 * 60  // 07:00
      const actualWakeMin = isoToMin(l.wake_time)
      const wakeDelta = actualWakeMin - targetWakeMin

      const avgAbsDelta = (Math.abs(sleepDelta) + Math.abs(wakeDelta)) / 2
      const adherence = Math.round((1 - Math.min(avgAbsDelta, 120) / 120) * 100)

      return {
        date: l.date,
        sleep_delta_min: sleepDelta,
        wake_delta_min: wakeDelta,
        adherence_pct: Math.max(0, adherence),
      }
    })
  })

  const avgAdherencePct = computed<number>(() => {
    const vals = protocolAdherence.value.map(d => d.adherence_pct)
    return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 100
  })

  // ---------------------------------------------------------------------------
  // Insight computation — at most 4, sorted by confidence desc
  // ---------------------------------------------------------------------------

  const insights = computed<CircadianInsight[]>(() => {
    const result: CircadianInsight[] = []
    const w = windowedLogs.value

    // 1. HRV vs Kp correlation
    const paired = w
      .filter(l => l.hrv_avg != null)
      .map(l => ({
        hrv: l.hrv_avg!,
        kp: MOCK_KP_HISTORY[l.date] ?? 0,
      }))
    const highKp = paired.filter(p => p.kp > 3)
    const lowKp  = paired.filter(p => p.kp <= 3)
    if (highKp.length >= 3 && lowKp.length >= 2) {
      const avgHRVHigh = highKp.reduce((a, b) => a + b.hrv, 0) / highKp.length
      const avgHRVLow  = lowKp.reduce((a, b) => a + b.hrv, 0)  / lowKp.length
      const delta = avgHRVLow - avgHRVHigh
      if (delta >= 3) {
        result.push({
          id: 'hrv-kp-correlation',
          type: 'correlation',
          title: `HRV drops ${Math.abs(delta).toFixed(0)} ms on high-Kp nights`,
          body: `On ${highKp.length} nights with Kp > 3, your average HRV was ${avgHRVHigh.toFixed(1)} ms vs ${avgHRVLow.toFixed(1)} ms on calm nights. Geomagnetic activity may affect autonomic nervous system tone. This is an observational pattern, not a clinical finding.`,
          accent: '#FF4444',
          metric: 'hrv',
          confidence: highKp.length >= 5 ? 'medium' : 'low',
        })
      }
    }

    // 2. HRV trend (first half vs second half of window)
    const validHRV = w.filter(l => l.hrv_avg != null)
    if (validHRV.length >= 6) {
      const half = Math.floor(validHRV.length / 2)
      const firstHalf  = validHRV.slice(0, half)
      const secondHalf = validHRV.slice(half)
      const avgFirst  = firstHalf.reduce((a, b)  => a + b.hrv_avg!, 0) / firstHalf.length
      const avgSecond = secondHalf.reduce((a, b) => a + b.hrv_avg!, 0) / secondHalf.length
      const trend = avgSecond - avgFirst
      if (trend < -4) {
        result.push({
          id: 'hrv-trend-declining',
          type: 'trend',
          title: `HRV declining ${Math.abs(trend).toFixed(0)} ms over ${dateRange.value} days`,
          body: `Your HRV averaged ${avgFirst.toFixed(1)} ms in the first half of this period and ${avgSecond.toFixed(1)} ms in the second half. A sustained HRV decline often signals accumulated recovery debt. Prioritise sleep consistency and consider reducing training load.`,
          accent: '#FF4444',
          metric: 'hrv',
          confidence: 'low',
        })
      }
    }

    // 3. Protocol adherence
    if (avgAdherencePct.value < 70) {
      const meanDelta = protocolAdherence.value.reduce((a, b) => a + b.sleep_delta_min, 0) / protocolAdherence.value.length
      result.push({
        id: 'protocol-adherence-low',
        type: 'adherence',
        title: `${avgAdherencePct.value}% protocol adherence`,
        body: `Your sleep timing is averaging ${Math.abs(Math.round(meanDelta))} min ${meanDelta > 0 ? 'later' : 'earlier'} than your HELIOS target. Consistent timing is the single most powerful lever for circadian entrainment (Roenneberg 2012).`,
        accent: '#FFBD76',
        metric: 'adherence',
        // 'high' would sort this first but adherence is most actionable; keeping
        // 'medium' because it fires only when adherence is already poor — the
        // insight is corrective, not a leading indicator. Upgrade to 'high' if
        // product decides adherence always tops the card stack.
        confidence: 'high',
      })
    }

    // 4. Late sleep → low score correlation
    const lateSleepNights = protocolAdherence.value.filter(d => Math.abs(d.sleep_delta_min) > 45)
    if (lateSleepNights.length >= 2) {
      const lateDates = new Set(lateSleepNights.map(d => d.date))
      const lateScores = w
        .filter(l => lateDates.has(l.date) && l.sleep_score != null)
        .map(l => l.sleep_score!)
      if (lateScores.length >= 2) {
        const avgLateScore = lateScores.reduce((a, b) => a + b, 0) / lateScores.length
        if (avgLateScore < 65) {
          result.push({
            id: 'late-sleep-low-score',
            type: 'anomaly',
            title: 'Sleep quality drops when you sleep 45+ min late',
            body: `On ${lateSleepNights.length} nights when you slept significantly later than your 23:00 target, your average sleep score was ${avgLateScore.toFixed(0)} — below your typical range. Late sleep onset compresses slow-wave sleep in the first half of the night.`,
            accent: '#9B8BFA',
            metric: 'sleep_score',
            confidence: 'low',
          })
        }
      }
    }

    // Sort: high → medium → low; take first 4
    const order: Record<'high' | 'medium' | 'low', number> = { high: 0, medium: 1, low: 2 }
    return result.sort((a, b) => order[a.confidence] - order[b.confidence]).slice(0, 4)
  })

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  function setDateRange(range: DateRange) {
    dateRange.value = range
  }

  function loadMockData() {
    logs.value = MOCK_SLEEP_LOGS
    dataSource.value = 'mock'
  }

  function ingestParsedLogs(newLogs: SleepLog[]) {
    logs.value = [...newLogs].sort((a, b) => a.date.localeCompare(b.date))
    dataSource.value = 'uploaded'
    uploadStatus.value = 'success'
  }

  function setUploadStatus(status: UploadStatus, err?: string) {
    uploadStatus.value = status
    uploadError.value = err ?? null
  }

  // Auto-load mock data on store creation
  loadMockData()

  return {
    // State
    logs,
    dateRange,
    uploadStatus,
    uploadError,
    dataSource,
    // Windowed
    windowedLogs,
    // Chart series
    hrvSeries,
    kpOverlaySeries,
    sleepArchitectureSeries,
    sleepScoreSeries,
    restingHRSeries,
    skinTempSeries,
    // KPIs
    avgHRV,
    avgSleepScore,
    avgRestingHR,
    avgTotalSleepH,
    // Adherence + insights
    protocolAdherence,
    avgAdherencePct,
    insights,
    // Phase A
    dlmoEstimate,
    caffeineCutoff,
    napWindow,
    // Phase B
    sri,
    sriSeries,
    sleepDebtMin,
    sleepDebtSeries,
    dialData,
    nowAngle,
    // Actions
    setDateRange,
    loadMockData,
    ingestParsedLogs,
    setUploadStatus,
  }
})
