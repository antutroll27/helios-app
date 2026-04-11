import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const BASE_URL = 'https://services.swpc.noaa.gov'

interface NOAAAlert {
  issue_datetime: string
  product_id: string
  message: string
}

interface GScaleEntry {
  Scale: string
  Text: string
  DateStamp: string
  TimeStamp: string
  MinorProb?: string
  MajorProb?: string
}

export const useSpaceWeatherStore = defineStore('spaceWeather', () => {
  const kpIndex = ref<number>(0)
  const solarWindSpeed = ref<number>(0)
  const bzComponent = ref<number>(0)
  const flareClass = ref<string>('None')
  const activeAlerts = ref<NOAAAlert[]>([])
  const gScaleRaw = ref<Record<string, GScaleEntry>>({})
  const gScale = computed<number>(() => {
    try {
      // Try multiple paths the NOAA data might use
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const raw = gScaleRaw.value as any
      if (raw?.['0']?.G?.Scale !== undefined) return parseInt(raw['0'].G.Scale) || 0
      if (raw?.G?.Scale !== undefined) return parseInt(raw.G.Scale) || 0
      if (raw?.['24hr_observed']?.G?.Scale !== undefined) return parseInt(raw['24hr_observed'].G.Scale) || 0
      return 0
    } catch { return 0 }
  })
  const lastUpdated = ref<Date | null>(null)

  let pollingInterval: ReturnType<typeof setInterval> | null = null

  // ─── Disruption score ────────────────────────────────────────────────────────

  const disruptionScore = computed<number>(() => {
    const kp = kpIndex.value
    if (kp <= 1) return 0
    if (kp <= 3) return 1
    if (kp <= 4) return 2
    if (kp <= 6) return 3
    if (kp <= 8) return 4
    return 5
  })

  const disruptionLabel = computed<string>(() => {
    const labels = ['Calm', 'Quiet', 'Unsettled', 'Storm', 'Severe', 'Extreme']
    return labels[disruptionScore.value] ?? 'Unknown'
  })

  const disruptionAdvisory = computed<string>(() => {
    const score = disruptionScore.value
    if (score === 0) return 'Geomagnetic conditions are calm. Observational context only; individual relevance is uncertain.'
    if (score === 1) return 'Quiet geomagnetic activity is being observed. Individual sleep or wellbeing effects are uncertain.'
    if (score === 2) return 'Unsettled geomagnetic conditions are being observed. Treat this as context only, not a personal health prediction.'
    if (score === 3)
      return 'Geomagnetic storm conditions are being observed. Individual relevance is uncertain and causal claims should be avoided.'
    if (score === 4)
      return 'Severe geomagnetic activity is being observed. Use this as observational context only.'
    return 'Extreme geomagnetic activity is being observed. This is a space-weather reading, not a personal health forecast.'
  })

  // ─── Bz warning ──────────────────────────────────────────────────────────────

  const bzWarning = computed<'mild' | 'moderate' | 'severe' | null>(() => {
    const bz = bzComponent.value
    if (bz > -5) return null
    if (bz > -10) return 'mild'
    if (bz > -20) return 'moderate'
    return 'severe'
  })

  // ─── Fetchers ────────────────────────────────────────────────────────────────

  async function fetchKpIndex(): Promise<void> {
    const response = await fetch(`${BASE_URL}/json/planetary_k_index_1m.json`)
    if (!response.ok) throw new Error(`Kp index fetch failed: ${response.status}`)
    const data: unknown[][] = await response.json()
    if (Array.isArray(data) && data.length > 0) {
      const last = data[data.length - 1]
      const raw = parseFloat(String(last[1]))
      kpIndex.value = isNaN(raw) ? 0 : raw
    }
  }

  async function fetchSolarWindMag(): Promise<void> {
    const response = await fetch(`${BASE_URL}/products/solar-wind/mag-1-day.json`)
    if (!response.ok) throw new Error(`Solar wind mag fetch failed: ${response.status}`)
    const data: unknown[][] = await response.json()
    if (Array.isArray(data) && data.length > 1) {
      const last = data[data.length - 1]
      // Index [3] = Bz GSM
      const raw = parseFloat(String(last[3]))
      bzComponent.value = isNaN(raw) ? 0 : raw
    }
  }

  async function fetchSolarWindPlasma(): Promise<void> {
    const response = await fetch(`${BASE_URL}/products/solar-wind/plasma-1-day.json`)
    if (!response.ok) throw new Error(`Solar wind plasma fetch failed: ${response.status}`)
    const data: unknown[][] = await response.json()
    if (Array.isArray(data) && data.length > 1) {
      const last = data[data.length - 1]
      // Index [2] = speed
      const raw = parseFloat(String(last[2]))
      solarWindSpeed.value = isNaN(raw) ? 0 : raw
    }
  }

  async function fetchAlerts(): Promise<void> {
    const response = await fetch(`${BASE_URL}/products/alerts.json`)
    if (!response.ok) throw new Error(`Alerts fetch failed: ${response.status}`)
    const data: NOAAAlert[] = await response.json()
    activeAlerts.value = Array.isArray(data) ? data : []
  }

  async function fetchGScale(): Promise<void> {
    const response = await fetch(`${BASE_URL}/products/noaa-scales.json`)
    if (!response.ok) throw new Error(`G-scale fetch failed: ${response.status}`)
    const data: Record<string, GScaleEntry> = await response.json()
    gScaleRaw.value = data ?? {}
  }

  async function fetchAll(): Promise<void> {
    const results = await Promise.allSettled([
      fetchKpIndex(),
      fetchSolarWindMag(),
      fetchSolarWindPlasma(),
      fetchAlerts(),
      fetchGScale()
    ])

    for (const result of results) {
      if (result.status === 'rejected') {
        console.warn('[spaceWeather] fetch error:', result.reason)
      }
    }

    lastUpdated.value = new Date()

    // Extract flare class from active NOAA alerts.
    // NOAA flare alerts contain flare class strings (e.g. "M1.5", "X2.3") in the
    // message body text, not in product_id (which uses WMO routing codes like "ALTK07").
    const flareAlert = activeAlerts.value.find(
      (a) => a.message?.toUpperCase().includes('FLARE')
    )
    // If a flare alert is found, attempt to extract the class from the message.
    // Fall back to 'Active' if a flare message exists but class cannot be parsed.
    flareClass.value = flareAlert
      ? (flareAlert.message?.match(/\b([MXC]\d+\.?\d*)\b/)?.[1] ?? 'Active')
      : 'None'
  }

  function startPolling(intervalMs = 5 * 60 * 1000): void {
    if (pollingInterval) clearInterval(pollingInterval)
    fetchAll()
    pollingInterval = setInterval(() => {
      fetchAll()
    }, intervalMs)
  }

  function stopPolling(): void {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
    }
  }

  return {
    kpIndex,
    solarWindSpeed,
    bzComponent,
    flareClass,
    activeAlerts,
    gScale,
    lastUpdated,
    disruptionScore,
    disruptionLabel,
    disruptionAdvisory,
    bzWarning,
    fetchAll,
    startPolling,
    stopPolling
  }
})
