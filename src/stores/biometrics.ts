import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
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

export interface KpDayEntry {
  date: string
  kp_max: number
}

export interface ProtocolAdherenceDay {
  date: string
  target_sleep_hhmm: string   // "23:00"
  actual_sleep_hhmm: string   // "23:42"
  target_wake_hhmm: string    // "07:00"
  actual_wake_hhmm: string    // "07:18"
  delta_sleep_min: number     // positive = slept later than target
  delta_wake_min: number
  adherence_pct: number       // 0-100
}

export interface CircadianInsight {
  id: string
  type: 'correlation' | 'trend' | 'adherence' | 'anomaly'
  title: string
  body: string
  accent: string
  metric: string
  confidence: 'low' | 'medium' | 'high'
}

export type DateRange = 7 | 30
export type UploadStatus = 'idle' | 'parsing' | 'success' | 'error'

// ---------------------------------------------------------------------------
// Mock data — 30 nights: 2026-03-14 through 2026-04-12
// Deliberate patterns:
//   • 4 high-Kp nights (2026-03-17, 2026-03-24, 2026-04-01, 2026-04-08)
//     → hrv_avg ~8 ms below mean (36-38 ms vs general 44-50 ms)
//   • 2 late-sleep nights (2026-03-21, 2026-04-03) → sleep_onset ~01:15-01:30
//   • 2 no-device nights (2026-03-19, 2026-04-05) → hrv_avg: undefined
//   • 1 outlier night (2026-03-26) → total_sleep_min: 312, sleep_score: 46, hrv_avg: 31
//   • All other nights realistic (total 420-490 min, deep 70-110, rem 85-130, etc.)
// ---------------------------------------------------------------------------

const MOCK_SLEEP_LOGS: SleepLog[] = [
  // 2026-03-14 — normal
  {
    date: '2026-03-14',
    sleep_onset: '2026-03-14T23:08:00.000Z',
    wake_time: '2026-03-15T06:52:00.000Z',
    total_sleep_min: 464,
    deep_sleep_min: 95,
    rem_sleep_min: 112,
    hrv_avg: 48,
    skin_temp_delta: 0.1,
    resting_hr: 55,
    sleep_score: 82,
    source: 'mock'
  },
  // 2026-03-15 — normal
  {
    date: '2026-03-15',
    sleep_onset: '2026-03-15T22:54:00.000Z',
    wake_time: '2026-03-16T07:06:00.000Z',
    total_sleep_min: 492,
    deep_sleep_min: 104,
    rem_sleep_min: 118,
    hrv_avg: 51,
    skin_temp_delta: 0.0,
    resting_hr: 53,
    sleep_score: 85,
    source: 'mock'
  },
  // 2026-03-16 — normal
  {
    date: '2026-03-16',
    sleep_onset: '2026-03-16T23:12:00.000Z',
    wake_time: '2026-03-17T07:04:00.000Z',
    total_sleep_min: 472,
    deep_sleep_min: 88,
    rem_sleep_min: 109,
    hrv_avg: 46,
    skin_temp_delta: -0.1,
    resting_hr: 57,
    sleep_score: 79,
    source: 'mock'
  },
  // 2026-03-17 — HIGH Kp (5.3) → low HRV
  {
    date: '2026-03-17',
    sleep_onset: '2026-03-17T23:18:00.000Z',
    wake_time: '2026-03-18T07:02:00.000Z',
    total_sleep_min: 464,
    deep_sleep_min: 78,
    rem_sleep_min: 96,
    hrv_avg: 37,
    skin_temp_delta: 0.2,
    resting_hr: 61,
    sleep_score: 71,
    source: 'mock'
  },
  // 2026-03-18 — normal
  {
    date: '2026-03-18',
    sleep_onset: '2026-03-18T23:05:00.000Z',
    wake_time: '2026-03-19T07:10:00.000Z',
    total_sleep_min: 485,
    deep_sleep_min: 101,
    rem_sleep_min: 115,
    hrv_avg: 50,
    skin_temp_delta: 0.0,
    resting_hr: 54,
    sleep_score: 84,
    source: 'mock'
  },
  // 2026-03-19 — no device (hrv_avg undefined)
  {
    date: '2026-03-19',
    sleep_onset: '2026-03-19T23:22:00.000Z',
    wake_time: '2026-03-20T07:15:00.000Z',
    total_sleep_min: 473,
    deep_sleep_min: 90,
    rem_sleep_min: 105,
    hrv_avg: undefined,
    skin_temp_delta: undefined,
    resting_hr: undefined,
    sleep_score: undefined,
    source: 'mock'
  },
  // 2026-03-20 — normal
  {
    date: '2026-03-20',
    sleep_onset: '2026-03-20T22:58:00.000Z',
    wake_time: '2026-03-21T07:08:00.000Z',
    total_sleep_min: 490,
    deep_sleep_min: 108,
    rem_sleep_min: 122,
    hrv_avg: 53,
    skin_temp_delta: -0.2,
    resting_hr: 52,
    sleep_score: 87,
    source: 'mock'
  },
  // 2026-03-21 — LATE SLEEP (~01:15)
  {
    date: '2026-03-21',
    sleep_onset: '2026-03-22T01:18:00.000Z',
    wake_time: '2026-03-22T07:45:00.000Z',
    total_sleep_min: 387,
    deep_sleep_min: 67,
    rem_sleep_min: 88,
    hrv_avg: 41,
    skin_temp_delta: 0.3,
    resting_hr: 60,
    sleep_score: 63,
    source: 'mock'
  },
  // 2026-03-22 — normal
  {
    date: '2026-03-22',
    sleep_onset: '2026-03-22T23:16:00.000Z',
    wake_time: '2026-03-23T07:22:00.000Z',
    total_sleep_min: 486,
    deep_sleep_min: 97,
    rem_sleep_min: 114,
    hrv_avg: 47,
    skin_temp_delta: 0.1,
    resting_hr: 56,
    sleep_score: 80,
    source: 'mock'
  },
  // 2026-03-23 — normal
  {
    date: '2026-03-23',
    sleep_onset: '2026-03-23T23:04:00.000Z',
    wake_time: '2026-03-24T07:02:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 102,
    rem_sleep_min: 119,
    hrv_avg: 52,
    skin_temp_delta: -0.1,
    resting_hr: 54,
    sleep_score: 83,
    source: 'mock'
  },
  // 2026-03-24 — HIGH Kp (4.8) → low HRV
  {
    date: '2026-03-24',
    sleep_onset: '2026-03-24T23:28:00.000Z',
    wake_time: '2026-03-25T07:14:00.000Z',
    total_sleep_min: 466,
    deep_sleep_min: 76,
    rem_sleep_min: 94,
    hrv_avg: 36,
    skin_temp_delta: 0.3,
    resting_hr: 62,
    sleep_score: 68,
    source: 'mock'
  },
  // 2026-03-25 — normal
  {
    date: '2026-03-25',
    sleep_onset: '2026-03-25T23:10:00.000Z',
    wake_time: '2026-03-26T07:00:00.000Z',
    total_sleep_min: 470,
    deep_sleep_min: 93,
    rem_sleep_min: 110,
    hrv_avg: 49,
    skin_temp_delta: 0.0,
    resting_hr: 55,
    sleep_score: 81,
    source: 'mock'
  },
  // 2026-03-26 — OUTLIER (short sleep, poor score)
  {
    date: '2026-03-26',
    sleep_onset: '2026-03-27T01:02:00.000Z',
    wake_time: '2026-03-27T06:14:00.000Z',
    total_sleep_min: 312,
    deep_sleep_min: 52,
    rem_sleep_min: 74,
    hrv_avg: 31,
    skin_temp_delta: 0.4,
    resting_hr: 64,
    sleep_score: 46,
    source: 'mock'
  },
  // 2026-03-27 — normal
  {
    date: '2026-03-27',
    sleep_onset: '2026-03-27T23:14:00.000Z',
    wake_time: '2026-03-28T07:08:00.000Z',
    total_sleep_min: 474,
    deep_sleep_min: 99,
    rem_sleep_min: 116,
    hrv_avg: 50,
    skin_temp_delta: -0.1,
    resting_hr: 55,
    sleep_score: 83,
    source: 'mock'
  },
  // 2026-03-28 — normal
  {
    date: '2026-03-28',
    sleep_onset: '2026-03-28T22:56:00.000Z',
    wake_time: '2026-03-29T07:04:00.000Z',
    total_sleep_min: 488,
    deep_sleep_min: 106,
    rem_sleep_min: 124,
    hrv_avg: 55,
    skin_temp_delta: -0.2,
    resting_hr: 52,
    sleep_score: 88,
    source: 'mock'
  },
  // 2026-03-29 — normal
  {
    date: '2026-03-29',
    sleep_onset: '2026-03-29T23:06:00.000Z',
    wake_time: '2026-03-30T07:12:00.000Z',
    total_sleep_min: 486,
    deep_sleep_min: 100,
    rem_sleep_min: 118,
    hrv_avg: 54,
    skin_temp_delta: 0.1,
    resting_hr: 53,
    sleep_score: 86,
    source: 'mock'
  },
  // 2026-03-30 — normal
  {
    date: '2026-03-30',
    sleep_onset: '2026-03-30T23:20:00.000Z',
    wake_time: '2026-03-31T07:06:00.000Z',
    total_sleep_min: 466,
    deep_sleep_min: 86,
    rem_sleep_min: 108,
    hrv_avg: 44,
    skin_temp_delta: 0.2,
    resting_hr: 58,
    sleep_score: 77,
    source: 'mock'
  },
  // 2026-03-31 — normal
  {
    date: '2026-03-31',
    sleep_onset: '2026-03-31T23:02:00.000Z',
    wake_time: '2026-04-01T07:00:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 98,
    rem_sleep_min: 115,
    hrv_avg: 51,
    skin_temp_delta: -0.1,
    resting_hr: 55,
    sleep_score: 84,
    source: 'mock'
  },
  // 2026-04-01 — HIGH Kp (6.1) → low HRV
  {
    date: '2026-04-01',
    sleep_onset: '2026-04-01T23:30:00.000Z',
    wake_time: '2026-04-02T07:18:00.000Z',
    total_sleep_min: 468,
    deep_sleep_min: 74,
    rem_sleep_min: 92,
    hrv_avg: 38,
    skin_temp_delta: 0.3,
    resting_hr: 63,
    sleep_score: 69,
    source: 'mock'
  },
  // 2026-04-02 — normal
  {
    date: '2026-04-02',
    sleep_onset: '2026-04-02T23:08:00.000Z',
    wake_time: '2026-04-03T07:10:00.000Z',
    total_sleep_min: 482,
    deep_sleep_min: 97,
    rem_sleep_min: 114,
    hrv_avg: 49,
    skin_temp_delta: 0.0,
    resting_hr: 56,
    sleep_score: 82,
    source: 'mock'
  },
  // 2026-04-03 — LATE SLEEP (~01:30)
  {
    date: '2026-04-03',
    sleep_onset: '2026-04-04T01:27:00.000Z',
    wake_time: '2026-04-04T07:52:00.000Z',
    total_sleep_min: 385,
    deep_sleep_min: 65,
    rem_sleep_min: 85,
    hrv_avg: 40,
    skin_temp_delta: 0.4,
    resting_hr: 61,
    sleep_score: 61,
    source: 'mock'
  },
  // 2026-04-04 — normal
  {
    date: '2026-04-04',
    sleep_onset: '2026-04-04T23:18:00.000Z',
    wake_time: '2026-04-05T07:14:00.000Z',
    total_sleep_min: 476,
    deep_sleep_min: 94,
    rem_sleep_min: 111,
    hrv_avg: 48,
    skin_temp_delta: -0.1,
    resting_hr: 57,
    sleep_score: 80,
    source: 'mock'
  },
  // 2026-04-05 — no device (hrv_avg undefined)
  {
    date: '2026-04-05',
    sleep_onset: '2026-04-05T23:25:00.000Z',
    wake_time: '2026-04-06T07:20:00.000Z',
    total_sleep_min: 475,
    deep_sleep_min: 91,
    rem_sleep_min: 107,
    hrv_avg: undefined,
    skin_temp_delta: undefined,
    resting_hr: undefined,
    sleep_score: undefined,
    source: 'mock'
  },
  // 2026-04-06 — normal
  {
    date: '2026-04-06',
    sleep_onset: '2026-04-06T23:00:00.000Z',
    wake_time: '2026-04-07T07:05:00.000Z',
    total_sleep_min: 485,
    deep_sleep_min: 103,
    rem_sleep_min: 121,
    hrv_avg: 53,
    skin_temp_delta: -0.2,
    resting_hr: 53,
    sleep_score: 86,
    source: 'mock'
  },
  // 2026-04-07 — normal
  {
    date: '2026-04-07',
    sleep_onset: '2026-04-07T23:12:00.000Z',
    wake_time: '2026-04-08T07:02:00.000Z',
    total_sleep_min: 470,
    deep_sleep_min: 89,
    rem_sleep_min: 110,
    hrv_avg: 47,
    skin_temp_delta: 0.1,
    resting_hr: 57,
    sleep_score: 79,
    source: 'mock'
  },
  // 2026-04-08 — HIGH Kp (4.7) → low HRV
  {
    date: '2026-04-08',
    sleep_onset: '2026-04-08T23:22:00.000Z',
    wake_time: '2026-04-09T07:08:00.000Z',
    total_sleep_min: 466,
    deep_sleep_min: 77,
    rem_sleep_min: 95,
    hrv_avg: 37,
    skin_temp_delta: 0.3,
    resting_hr: 62,
    sleep_score: 70,
    source: 'mock'
  },
  // 2026-04-09 — normal
  {
    date: '2026-04-09',
    sleep_onset: '2026-04-09T23:06:00.000Z',
    wake_time: '2026-04-10T07:04:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 96,
    rem_sleep_min: 113,
    hrv_avg: 50,
    skin_temp_delta: 0.0,
    resting_hr: 55,
    sleep_score: 83,
    source: 'mock'
  },
  // 2026-04-10 — normal
  {
    date: '2026-04-10',
    sleep_onset: '2026-04-10T23:14:00.000Z',
    wake_time: '2026-04-11T07:10:00.000Z',
    total_sleep_min: 476,
    deep_sleep_min: 99,
    rem_sleep_min: 117,
    hrv_avg: 52,
    skin_temp_delta: -0.1,
    resting_hr: 54,
    sleep_score: 85,
    source: 'mock'
  },
  // 2026-04-11 — normal
  {
    date: '2026-04-11',
    sleep_onset: '2026-04-11T22:58:00.000Z',
    wake_time: '2026-04-12T07:06:00.000Z',
    total_sleep_min: 488,
    deep_sleep_min: 107,
    rem_sleep_min: 126,
    hrv_avg: 56,
    skin_temp_delta: -0.3,
    resting_hr: 51,
    sleep_score: 89,
    source: 'mock'
  },
  // 2026-04-12 — normal (today)
  {
    date: '2026-04-12',
    sleep_onset: '2026-04-12T23:10:00.000Z',
    wake_time: '2026-04-13T07:08:00.000Z',
    total_sleep_min: 478,
    deep_sleep_min: 93,
    rem_sleep_min: 112,
    hrv_avg: 49,
    skin_temp_delta: 0.1,
    resting_hr: 56,
    sleep_score: 82,
    source: 'mock'
  }
]

const MOCK_KP_HISTORY: KpDayEntry[] = [
  { date: '2026-03-14', kp_max: 1.3 },
  { date: '2026-03-15', kp_max: 0.9 },
  { date: '2026-03-16', kp_max: 2.1 },
  { date: '2026-03-17', kp_max: 5.3 }, // HIGH
  { date: '2026-03-18', kp_max: 1.7 },
  { date: '2026-03-19', kp_max: 0.7 },
  { date: '2026-03-20', kp_max: 1.4 },
  { date: '2026-03-21', kp_max: 2.6 },
  { date: '2026-03-22', kp_max: 1.1 },
  { date: '2026-03-23', kp_max: 2.9 },
  { date: '2026-03-24', kp_max: 4.8 }, // HIGH
  { date: '2026-03-25', kp_max: 1.8 },
  { date: '2026-03-26', kp_max: 2.2 },
  { date: '2026-03-27', kp_max: 0.8 },
  { date: '2026-03-28', kp_max: 1.2 },
  { date: '2026-03-29', kp_max: 1.6 },
  { date: '2026-03-30', kp_max: 2.4 },
  { date: '2026-03-31', kp_max: 1.0 },
  { date: '2026-04-01', kp_max: 6.1 }, // HIGH
  { date: '2026-04-02', kp_max: 2.7 },
  { date: '2026-04-03', kp_max: 1.5 },
  { date: '2026-04-04', kp_max: 0.9 },
  { date: '2026-04-05', kp_max: 1.3 },
  { date: '2026-04-06', kp_max: 2.0 },
  { date: '2026-04-07', kp_max: 1.9 },
  { date: '2026-04-08', kp_max: 4.7 }, // HIGH
  { date: '2026-04-09', kp_max: 2.3 },
  { date: '2026-04-10', kp_max: 1.4 },
  { date: '2026-04-11', kp_max: 0.8 },
  { date: '2026-04-12', kp_max: 1.6 }
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

  // Parses "HH:MM" or ISO datetime ("2026-03-14T23:10:00.000Z") → minutes since midnight
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

  // Last N calendar days
  const windowedLogs = computed<SleepLog[]>(() => {
    return logs.value.slice(-dateRange.value)
  })

  // Series for HRV chart: null for missing values (gaps in chart)
  const hrvSeries = computed(() => {
    return {
      dates: windowedLogs.value.map(l => l.date.slice(5)),  // "MM-DD"
      values: windowedLogs.value.map(l => l.hrv_avg ?? null)
    }
  })

  // Kp overlay matching same dates as windowedLogs
  const kpOverlaySeries = computed(() => {
    const dates = windowedLogs.value.map(l => l.date)
    return {
      dates: dates.map(d => d.slice(5)),
      kp: dates.map(d => MOCK_KP_HISTORY.find(k => k.date === d)?.kp_max ?? 0)
    }
  })

  // Sleep architecture: deep / rem / light (total - deep - rem)
  const sleepArchitectureSeries = computed(() => {
    const w = windowedLogs.value
    return {
      dates: w.map(l => l.date.slice(5)),
      deep: w.map(l => l.deep_sleep_min ?? 0),
      rem: w.map(l => l.rem_sleep_min ?? 0),
      light: w.map(l => Math.max(0, l.total_sleep_min - (l.deep_sleep_min ?? 0) - (l.rem_sleep_min ?? 0)))
    }
  })

  const sleepScoreSeries = computed(() => ({
    dates: windowedLogs.value.map(l => l.date.slice(5)),
    scores: windowedLogs.value.map(l => l.sleep_score ?? null)
  }))

  const restingHRSeries = computed(() => ({
    dates: windowedLogs.value.map(l => l.date.slice(5)),
    values: windowedLogs.value.map(l => l.resting_hr ?? null)
  }))

  const skinTempSeries = computed(() => ({
    dates: windowedLogs.value.map(l => l.date.slice(5)),
    deltas: windowedLogs.value.map(l => l.skin_temp_delta ?? null)
  }))

  // Summary KPIs (mean of non-null values in window)
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

  // Protocol adherence — compare sleep_onset/wake_time to fixed 23:00/07:00 targets
  const protocolAdherence = computed<ProtocolAdherenceDay[]>(() => {
    // Parse HH:MM directly from ISO string (index 11–15) to avoid local timezone conversion.
    // Mock data stores "intended local time" with a Z suffix — Date.getHours() would apply
    // the user's local offset and produce wildly wrong deltas.
    function isoToMin(iso: string): number {
      const h = parseInt(iso.slice(11, 13), 10)
      const m = parseInt(iso.slice(14, 16), 10)
      return h * 60 + m
    }
    function isoToHHMM(iso: string): string {
      return iso.slice(11, 16)
    }

    return windowedLogs.value.map(l => {
      const targetSleepMin = 23 * 60   // 23:00
      const targetWakeMin  =  7 * 60   // 07:00

      let actualSleepMin = isoToMin(l.sleep_onset)
      // Times before noon are post-midnight (e.g. 01:15 → 1515 on 0–1680 scale)
      // Evening times stay as-is (23:00 = 1380). Target 23:00 = 1380 — no shift needed.
      if (actualSleepMin < 12 * 60) actualSleepMin += 24 * 60
      const deltaSleep = actualSleepMin - targetSleepMin

      const actualWakeMin = isoToMin(l.wake_time)
      const deltaWake = actualWakeMin - targetWakeMin

      const avgAbsDelta = (Math.abs(deltaSleep) + Math.abs(deltaWake)) / 2
      const adherence = Math.round((1 - Math.min(avgAbsDelta, 120) / 120) * 100)

      return {
        date: l.date,
        target_sleep_hhmm: '23:00',
        actual_sleep_hhmm: isoToHHMM(l.sleep_onset),
        target_wake_hhmm: '07:00',
        actual_wake_hhmm: isoToHHMM(l.wake_time),
        delta_sleep_min: deltaSleep,
        delta_wake_min: deltaWake,
        adherence_pct: Math.max(0, adherence)
      }
    })
  })

  const avgAdherencePct = computed(() => {
    const vals = protocolAdherence.value.map(d => d.adherence_pct)
    return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 100
  })

  // Insight computation
  const insights = computed<CircadianInsight[]>(() => {
    const result: CircadianInsight[] = []
    const w = windowedLogs.value

    // 1. HRV vs Kp correlation
    const paired = w
      .filter(l => l.hrv_avg != null)
      .map(l => ({
        hrv: l.hrv_avg!,
        kp: MOCK_KP_HISTORY.find(k => k.date === l.date)?.kp_max ?? 0
      }))
    const highKp = paired.filter(p => p.kp > 3)
    const lowKp = paired.filter(p => p.kp <= 3)
    if (highKp.length >= 2 && lowKp.length >= 2) {
      const avgHigh = highKp.reduce((a, b) => a + b.hrv, 0) / highKp.length
      const avgLow = lowKp.reduce((a, b) => a + b.hrv, 0) / lowKp.length
      const delta = avgLow - avgHigh
      if (Math.abs(delta) >= 3) {
        result.push({
          id: 'hrv-kp-correlation',
          type: 'correlation',
          title: `HRV drops ${Math.abs(delta).toFixed(0)} ms on high-Kp nights`,
          body: `On ${highKp.length} nights with Kp > 3, your average HRV was ${avgHigh.toFixed(1)} ms vs ${avgLow.toFixed(1)} ms on calm nights. Geomagnetic activity may affect autonomic nervous system tone. This is an observational pattern, not a clinical finding.`,
          accent: '#00D4AA',
          metric: 'hrv',
          confidence: highKp.length >= 3 ? 'medium' : 'low'
        })
      }
    }

    // 2. Protocol adherence
    if (avgAdherencePct.value < 75) {
      const meanDelta = protocolAdherence.value.reduce((a, b) => a + b.delta_sleep_min, 0) / protocolAdherence.value.length
      result.push({
        id: 'protocol-adherence-low',
        type: 'adherence',
        title: `${avgAdherencePct.value}% protocol adherence`,
        body: `Your sleep timing is averaging ${Math.abs(Math.round(meanDelta))} min ${meanDelta > 0 ? 'later' : 'earlier'} than your HELIOS target. Consistent timing is the single most powerful lever for circadian entrainment (Roenneberg 2012).`,
        accent: '#FFBD76',
        metric: 'sleep_score',
        confidence: 'high'
      })
    }

    // 3. HRV trend (first half vs second half of window)
    const validHRV = w.filter(l => l.hrv_avg != null)
    if (validHRV.length >= 6) {
      const half = Math.floor(validHRV.length / 2)
      const firstHalf = validHRV.slice(0, half)
      const secondHalf = validHRV.slice(half)
      const avgFirst = firstHalf.reduce((a, b) => a + b.hrv_avg!, 0) / firstHalf.length
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
          confidence: 'medium'
        })
      }
    }

    // 4. Late sleep → low score correlation
    const lateSleepNights = protocolAdherence.value.filter(d => d.delta_sleep_min > 45)
    if (lateSleepNights.length >= 2) {
      const lateDates = new Set(lateSleepNights.map(d => d.date))
      const lateScores = w.filter(l => lateDates.has(l.date) && l.sleep_score != null).map(l => l.sleep_score!)
      if (lateScores.length >= 2) {
        const avgLateScore = lateScores.reduce((a, b) => a + b, 0) / lateScores.length
        if (avgLateScore < 70) {
          result.push({
            id: 'late-sleep-low-score',
            type: 'anomaly',
            title: `Sleep quality drops when you sleep 45+ min late`,
            body: `On ${lateSleepNights.length} nights when you slept significantly later than your 23:00 target, your average sleep score was ${avgLateScore.toFixed(0)} — below your typical range. Late sleep onset compresses slow-wave sleep in the first half of the night.`,
            accent: '#9B8BFA',
            metric: 'sleep_score',
            confidence: 'medium'
          })
        }
      }
    }

    // Return max 4, sorted by confidence
    const order: Record<'high' | 'medium' | 'low', number> = { high: 0, medium: 1, low: 2 }
    return result.sort((a, b) => order[a.confidence] - order[b.confidence]).slice(0, 4)
  })

  // Actions
  function setDateRange(range: DateRange) { dateRange.value = range }

  function loadMockData() {
    logs.value = MOCK_SLEEP_LOGS
    dataSource.value = 'mock'
  }

  function ingestParsedLogs(parsed: SleepLog[]) {
    logs.value = [...parsed].sort((a, b) => a.date.localeCompare(b.date))
    dataSource.value = 'uploaded'
    uploadStatus.value = 'success'
  }

  function setUploadStatus(status: UploadStatus, error?: string) {
    uploadStatus.value = status
    uploadError.value = error ?? null
  }

  return {
    logs, dateRange, uploadStatus, uploadError, dataSource,
    windowedLogs, hrvSeries, kpOverlaySeries, sleepArchitectureSeries,
    sleepScoreSeries, restingHRSeries, skinTempSeries,
    avgHRV, avgSleepScore, avgRestingHR, avgTotalSleepH,
    protocolAdherence, avgAdherencePct, insights,
    nowAngle, dlmoEstimate, caffeineCutoff, napWindow,
    setDateRange, loadMockData, ingestParsedLogs, setUploadStatus
  }
})
