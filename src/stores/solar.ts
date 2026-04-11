import { defineStore } from 'pinia'
import { computed, ref, onScopeDispose } from 'vue'
import SunCalc from 'suncalc'
import { useGeoStore } from './geo'

export const useSolarStore = defineStore('solar', () => {
  const geo = useGeoStore()

  // Reactive now tick — updated every minute
  const now = ref<Date>(new Date())

  function refreshNow() {
    now.value = new Date()
  }

  // Auto-refresh every 60 seconds; cleared when the store is disposed
  const _nowInterval = setInterval(refreshNow, 60_000)
  onScopeDispose(() => clearInterval(_nowInterval))

  // ─── SunCalc raw data ────────────────────────────────────────────────────────

  const times = computed(() =>
    SunCalc.getTimes(now.value, geo.lat, geo.lng)
  )

  const position = computed(() =>
    SunCalc.getPosition(now.value, geo.lat, geo.lng)
  )

  // ─── Derived angles ──────────────────────────────────────────────────────────

  const elevationDeg = computed<number>(() =>
    parseFloat(((position.value.altitude * 180) / Math.PI).toFixed(2))
  )

  // ─── Key time windows ────────────────────────────────────────────────────────

  const sunriseTime = computed<Date>(() => times.value.sunrise)
  const sunsetTime = computed<Date>(() => times.value.sunset)
  const solarNoon = computed<Date>(() => times.value.solarNoon)
  const nadir = computed<Date>(() => times.value.nadir)
  const goldenHour = computed<Date>(() => times.value.goldenHour)
  const dawn = computed<Date>(() => times.value.dawn)
  const dusk = computed<Date>(() => times.value.dusk)
  const night = computed<Date>(() => times.value.night)

  /** Optimal wake window: sunrise to sunrise + 30 min */
  const wakeWindowStart = computed<Date>(() => sunriseTime.value)
  const wakeWindowEnd = computed<Date>(() => {
    const t = new Date(sunriseTime.value)
    t.setMinutes(t.getMinutes() + 30)
    return t
  })

  // ─── Boolean helpers ─────────────────────────────────────────────────────────

  const isDaytime = computed<boolean>(() => elevationDeg.value > 0)

  // ─── Solar phase ─────────────────────────────────────────────────────────────

  const solarPhase = computed<string>(() => {
    const el = elevationDeg.value
    const t = now.value.getTime()
    const sunriseMs = sunriseTime.value.getTime()
    const sunsetMs = sunsetTime.value.getTime()
    const noonMs = solarNoon.value.getTime()
    const dawnMs = times.value.dawn.getTime()
    const duskMs = times.value.dusk.getTime()
    const nightMs = times.value.night.getTime()
    if (el >= 60) return 'High Sun'
    if (el >= 15 && t > sunriseMs && t < sunsetMs) {
      if (Math.abs(t - noonMs) < 90 * 60 * 1000) return 'Solar Noon'
      return 'Day'
    }
    if (el > 0) return 'Day'
    if (t >= dawnMs && t < sunriseMs) return 'Civil Twilight'
    if (t > sunsetMs && t <= duskMs) return 'Civil Twilight'
    if (t > duskMs && t <= nightMs) return 'Nautical Twilight'
    if (t < dawnMs || t > nightMs) return 'Night'
    return 'Night'
  })

  return {
    now,
    times,
    position,
    elevationDeg,
    wakeWindowStart,
    wakeWindowEnd,
    sunriseTime,
    sunsetTime,
    solarNoon,
    nadir,
    goldenHour,
    dawn,
    dusk,
    night,
    isDaytime,
    solarPhase,
    refreshNow
  }
})
