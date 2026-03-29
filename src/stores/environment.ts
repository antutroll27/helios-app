import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const AQICN_TOKEN = () => import.meta.env.VITE_AQICN_TOKEN as string

// ─── Types ────────────────────────────────────────────────────────────────────

interface OpenMeteoResponse {
  hourly: {
    time: string[]
    uv_index: number[]
    temperature_2m: number[]
    relative_humidity_2m: number[]
  }
  daily: {
    time: string[]
    uv_index_max: number[]
    temperature_2m_max: number[]
    temperature_2m_min: number[]
    sunrise: string[]
    sunset: string[]
    sunshine_duration: number[] // seconds
  }
}

interface AQICNResponse {
  status: string
  data: {
    aqi: number
    iaqi?: {
      pm25?: { v: number }
    }
    city?: { name: string }
  }
}

// ─── AQI label helper ─────────────────────────────────────────────────────────

function aqiToLabel(aqi: number): string {
  if (aqi <= 50) return 'Good'
  if (aqi <= 100) return 'Moderate'
  if (aqi <= 150) return 'Unhealthy for Sensitive Groups'
  if (aqi <= 200) return 'Unhealthy'
  if (aqi <= 300) return 'Very Unhealthy'
  return 'Hazardous'
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useEnvironmentStore = defineStore('environment', () => {
  const uvIndexNow = ref<number>(0)
  const uvIndexMax = ref<number>(0)
  const temperatureNow = ref<number>(0)
  const temperatureNight = ref<number>(0) // avg 22:00–06:00
  const humidity = ref<number>(0)
  const sunshineDurationMin = ref<number>(0)
  const aqiLevel = ref<number>(0)
  const aqiLabel = ref<string>('Unknown')
  const pm25 = ref<number>(0)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // ─── Computed risk flags ────────────────────────────────────────────────────

  const heatRisk = computed<boolean>(() => temperatureNight.value > 28)
  const lowSunshineDay = computed<boolean>(() => sunshineDurationMin.value < 120)
  const airQualityRisk = computed<boolean>(() => aqiLevel.value > 100)

  // ─── Fetchers ────────────────────────────────────────────────────────────────

  async function fetchOpenMeteo(lat: number, lng: number): Promise<void> {
    const url =
      `https://api.open-meteo.com/v1/forecast` +
      `?latitude=${lat}&longitude=${lng}` +
      `&hourly=uv_index,temperature_2m,relative_humidity_2m` +
      `&daily=uv_index_max,temperature_2m_max,temperature_2m_min,sunrise,sunset,sunshine_duration` +
      `&timezone=auto&forecast_days=3`

    const response = await fetch(url)
    if (!response.ok) throw new Error(`Open-Meteo fetch failed: ${response.status}`)
    const data: OpenMeteoResponse = await response.json()

    const now = new Date()
    const hourlyTimes = data.hourly.time

    // Find current hour index.
    // Open-Meteo returns times in LOCAL timezone format ("YYYY-MM-DDTHH:00"), NOT UTC.
    // Using now.toISOString() (UTC) would cause a mismatch for any UTC+ timezone.
    // Instead, format the current local wall-clock hour as "YYYY-MM-DDTHH" by
    // reading the local date/time parts directly.
    const localYear = now.getFullYear()
    const localMonth = String(now.getMonth() + 1).padStart(2, '0')
    const localDay = String(now.getDate()).padStart(2, '0')
    const localHour = String(now.getHours()).padStart(2, '0')
    const currentHourStr = `${localYear}-${localMonth}-${localDay}T${localHour}` // "YYYY-MM-DDTHH"
    let currentIndex = hourlyTimes.findIndex((t) => t.startsWith(currentHourStr))
    if (currentIndex === -1) currentIndex = 0

    uvIndexNow.value = data.hourly.uv_index[currentIndex] ?? 0
    temperatureNow.value = data.hourly.temperature_2m[currentIndex] ?? 0
    humidity.value = data.hourly.relative_humidity_2m[currentIndex] ?? 0

    // Today's max UV
    uvIndexMax.value = data.daily.uv_index_max[0] ?? 0

    // Today's sunshine duration: convert seconds → minutes
    const sunshineSec = data.daily.sunshine_duration[0] ?? 0
    sunshineDurationMin.value = parseFloat((sunshineSec / 60).toFixed(1))

    // Night temperature average: collect readings between 22:00–06:00 (today + next day)
    const nightTemps: number[] = []
    for (let i = 0; i < hourlyTimes.length; i++) {
      const t = new Date(hourlyTimes[i])
      const h = t.getHours()
      if (h >= 22 || h < 6) {
        const temp = data.hourly.temperature_2m[i]
        if (temp !== undefined && temp !== null) {
          nightTemps.push(temp)
        }
      }
    }
    if (nightTemps.length > 0) {
      temperatureNight.value = parseFloat(
        (nightTemps.reduce((a, b) => a + b, 0) / nightTemps.length).toFixed(1)
      )
    } else {
      // Fallback: average of min/max
      temperatureNight.value = parseFloat(
        (((data.daily.temperature_2m_min[0] ?? 0) + (data.daily.temperature_2m_max[0] ?? 0)) / 2).toFixed(1)
      )
    }
  }

  async function fetchAQICN(lat: number, lng: number): Promise<void> {
    const token = AQICN_TOKEN()
    if (!token) throw new Error('AQICN token not configured')
    const url = `https://api.waqi.info/feed/geo:${lat};${lng}/?token=${token}`
    const response = await fetch(url)
    if (!response.ok) throw new Error(`AQICN fetch failed: ${response.status}`)
    const data: AQICNResponse = await response.json()
    if (data.status !== 'ok') throw new Error(`AQICN error: ${data.status}`)
    aqiLevel.value = data.data.aqi ?? 0
    aqiLabel.value = aqiToLabel(aqiLevel.value)
    pm25.value = data.data.iaqi?.pm25?.v ?? 0
  }

  async function fetchAll(lat: number, lng: number): Promise<void> {
    loading.value = true
    error.value = null

    const results = await Promise.allSettled([fetchOpenMeteo(lat, lng), fetchAQICN(lat, lng)])

    const errors: string[] = []
    for (const result of results) {
      if (result.status === 'rejected') {
        const msg = result.reason instanceof Error ? result.reason.message : String(result.reason)
        errors.push(msg)
        console.warn('[environment] fetch error:', msg)
      }
    }

    if (errors.length > 0) {
      error.value = errors.join('; ')
    }

    loading.value = false
  }

  return {
    uvIndexNow,
    uvIndexMax,
    temperatureNow,
    temperatureNight,
    humidity,
    sunshineDurationMin,
    aqiLevel,
    aqiLabel,
    pm25,
    loading,
    error,
    heatRisk,
    lowSunshineDay,
    airQualityRisk,
    fetchAll
  }
})
