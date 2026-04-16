import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { fetchPublicJson } from '@/lib/publicApi'

interface EnvironmentRouteResponse {
  uv_index_now?: number
  uv_index_max?: number
  temperature_now?: number
  temperature_night?: number
  humidity?: number
  sunshine_duration_min?: number
  aqi_level?: number
  aqi_label?: string
  pm25?: number
}

function aqiToLabel(aqi: number): string {
  if (aqi <= 50) return 'Good'
  if (aqi <= 100) return 'Moderate'
  if (aqi <= 150) return 'Unhealthy for Sensitive Groups'
  if (aqi <= 200) return 'Unhealthy'
  if (aqi <= 300) return 'Very Unhealthy'
  return 'Hazardous'
}

export const useEnvironmentStore = defineStore('environment', () => {
  const uvIndexNow = ref<number>(0)
  const uvIndexMax = ref<number>(0)
  const temperatureNow = ref<number>(0)
  const temperatureNight = ref<number>(0)
  const humidity = ref<number>(0)
  const sunshineDurationMin = ref<number>(0)
  const aqiLevel = ref<number>(0)
  const aqiLabel = ref<string>('Unknown')
  const pm25 = ref<number>(0)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  const heatRisk = computed<boolean>(() => temperatureNight.value > 28)
  const lowSunshineDay = computed<boolean>(() => sunshineDurationMin.value < 120)
  const airQualityRisk = computed<boolean>(() => aqiLevel.value > 100)

  async function fetchAll(lat: number, lng: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const data = await fetchPublicJson(`/environment?lat=${lat}&lng=${lng}`) as EnvironmentRouteResponse
      uvIndexNow.value = data.uv_index_now ?? 0
      uvIndexMax.value = data.uv_index_max ?? 0
      temperatureNow.value = data.temperature_now ?? 0
      temperatureNight.value = data.temperature_night ?? 0
      humidity.value = data.humidity ?? 0
      sunshineDurationMin.value = data.sunshine_duration_min ?? 0
      aqiLevel.value = data.aqi_level ?? 0
      aqiLabel.value = data.aqi_label ?? aqiToLabel(aqiLevel.value)
      pm25.value = data.pm25 ?? 0
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      console.warn('[environment] fetch error:', message)
      error.value = message
    } finally {
      loading.value = false
    }
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
