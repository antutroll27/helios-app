import { defineStore } from 'pinia'
import { ref } from 'vue'

const DA_NANG_LAT = 16.0544
const DA_NANG_LNG = 108.2022

export const useGeoStore = defineStore('geo', () => {
  const lat = ref<number>(DA_NANG_LAT)
  const lng = ref<number>(DA_NANG_LNG)
  const timezone = ref<string>('Asia/Bangkok')
  const locationName = ref<string>('Da Nang, Vietnam')
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  async function reverseGeocode(latitude: number, longitude: number): Promise<void> {
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&timezone=auto&forecast_days=1&daily=temperature_2m_max`
      const response = await fetch(url)
      if (!response.ok) throw new Error(`Open-Meteo geocode failed: ${response.status}`)
      const data = await response.json()
      if (data.timezone) {
        timezone.value = data.timezone
      }
      // Attempt reverse geocode via nominatim for location name
      try {
        const nominatimUrl = `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`
        const nominatimResponse = await fetch(nominatimUrl, {
          headers: { 'Accept-Language': 'en', 'User-Agent': 'HeliosApp/1.0' }
        })
        if (nominatimResponse.ok) {
          const nominatimData = await nominatimResponse.json()
          const city =
            nominatimData.address?.city ||
            nominatimData.address?.town ||
            nominatimData.address?.village ||
            nominatimData.address?.county ||
            ''
          const country = nominatimData.address?.country || ''
          if (city || country) {
            locationName.value = [city, country].filter(Boolean).join(', ')
          }
        }
      } catch {
        // Nominatim failed — keep default or previously set name
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Reverse geocode failed'
      error.value = message
    }
  }

  async function requestLocation(): Promise<void> {
    loading.value = true
    error.value = null

    if (!navigator.geolocation) {
      error.value = 'Geolocation is not supported by this browser. Using default location.'
      lat.value = DA_NANG_LAT
      lng.value = DA_NANG_LNG
      await reverseGeocode(DA_NANG_LAT, DA_NANG_LNG)
      loading.value = false
      return
    }

    await new Promise<void>((resolve) => {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          lat.value = position.coords.latitude
          lng.value = position.coords.longitude
          await reverseGeocode(lat.value, lng.value)
          resolve()
        },
        async (positionError) => {
          error.value = `Location access denied (${positionError.message}). Using default location: Da Nang.`
          lat.value = DA_NANG_LAT
          lng.value = DA_NANG_LNG
          await reverseGeocode(DA_NANG_LAT, DA_NANG_LNG)
          resolve()
        },
        { timeout: 10000, maximumAge: 300000 }
      )
    })

    loading.value = false
  }

  return {
    lat,
    lng,
    timezone,
    locationName,
    loading,
    error,
    requestLocation,
    reverseGeocode
  }
})
