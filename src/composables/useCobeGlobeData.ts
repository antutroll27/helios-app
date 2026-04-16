import { computed, readonly, shallowRef } from 'vue'
import SunCalc from 'suncalc'

import { getTimezoneOffsetHours } from '@/lib/timezoneUtils'
import { useGeoStore } from '@/stores/geo'
import { TIMEZONE_CITIES } from '@/stores/jetlag'
import { useSolarStore } from '@/stores/solar'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'

export interface GlobeDestination {
  id: string
  label: string
  lat: number
  lng: number
  timezone: string
}

export interface GlobeSolarSnapshotInput {
  elevationDeg: number
  phase: string
  sunrise: Date
  sunset: Date
  timeZone: string
}

export interface GlobeSolarSnapshot {
  elevationDeg: number
  phase: string
  sunriseLabel: string
  sunsetLabel: string
}

export interface GlobeDestinationSnapshot extends GlobeDestination {
  elevationDeg: number
  sunrise: Date
  sunset: Date
}

export interface GlobeComparison {
  id: string
  label: string
  lat: number
  lng: number
  timezone: string
  timezoneDeltaHours: number
  destinationElevationDeg: number
  sunriseDeltaMinutes: number
  sunsetDeltaMinutes: number
  sunriseLabel: string
  sunsetLabel: string
  travelReadiness: string
}

interface UseCobeGlobeDataOptions {
  current?: GlobeDestination
  destinations?: GlobeDestination[]
  now?: Date
}

function formatTimeLabel(date: Date, timeZone: string) {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

function getTravelReadiness(timezoneDeltaHours: number) {
  const abs = Math.abs(timezoneDeltaHours)
  if (abs === 0) return 'Aligned with your current schedule.'
  if (abs <= 2) return 'Light shift. Low travel strain expected.'
  if (abs <= 5) return 'Moderate shift. Plan light timing deliberately.'
  return 'Large shift. Expect meaningful circadian strain.'
}

function buildDestinationSnapshot(destination: GlobeDestination, now: Date): GlobeDestinationSnapshot {
  const times = SunCalc.getTimes(now, destination.lat, destination.lng)
  const position = SunCalc.getPosition(now, destination.lat, destination.lng)

  return {
    ...destination,
    elevationDeg: Number(((position.altitude * 180) / Math.PI).toFixed(1)),
    sunrise: times.sunrise,
    sunset: times.sunset,
  }
}

function getDefaultDestinations() {
  return ['Asia/Tokyo', 'Europe/London', 'America/New_York']
    .map((timeZone, index) => {
      const city = TIMEZONE_CITIES[timeZone]
      if (!city) {
        return null
      }

      return {
        id: `destination-${index + 1}`,
        label: city.label,
        lat: city.lat,
        lng: city.lng,
        timezone: timeZone,
      } satisfies GlobeDestination
    })
    .filter((destination): destination is GlobeDestination => destination !== null)
}

export function buildLocalSolarSnapshot(input: GlobeSolarSnapshotInput): GlobeSolarSnapshot {
  return {
    elevationDeg: input.elevationDeg,
    phase: input.phase,
    sunriseLabel: formatTimeLabel(input.sunrise, input.timeZone),
    sunsetLabel: formatTimeLabel(input.sunset, input.timeZone),
  }
}

export function buildDestinationComparisons(input: {
  anchorDate: Date
  current: GlobeDestinationSnapshot
  destinations: GlobeDestinationSnapshot[]
}): GlobeComparison[] {
  const currentOffset = getTimezoneOffsetHours(input.current.timezone, input.anchorDate)

  return input.destinations.map((destination) => {
    const destinationOffset = getTimezoneOffsetHours(destination.timezone, input.anchorDate)
    const timezoneDeltaHours = Math.round((destinationOffset - currentOffset) * 10) / 10

    return {
      id: destination.id,
      label: destination.label,
      lat: destination.lat,
      lng: destination.lng,
      timezone: destination.timezone,
      timezoneDeltaHours,
      destinationElevationDeg: destination.elevationDeg,
      sunriseDeltaMinutes: Math.round(
        (destination.sunrise.getTime() - input.current.sunrise.getTime()) / 60_000,
      ),
      sunsetDeltaMinutes: Math.round(
        (destination.sunset.getTime() - input.current.sunset.getTime()) / 60_000,
      ),
      sunriseLabel: formatTimeLabel(destination.sunrise, destination.timezone),
      sunsetLabel: formatTimeLabel(destination.sunset, destination.timezone),
      travelReadiness: getTravelReadiness(timezoneDeltaHours),
    }
  })
}

export function getInitialSelectedDestinationId<T extends { id: string }>(destinations: T[]) {
  return destinations[0]?.id ?? null
}

export function useCobeGlobeData(options: UseCobeGlobeDataOptions = {}) {
  const staticNow = options.now ?? null
  const geoStore = options.current ? null : useGeoStore()
  const solarStore = options.current ? null : useSolarStore()
  const spaceWeatherStore = options.current ? null : useSpaceWeatherStore()

  const anchorDate = computed(() => staticNow ?? solarStore?.now ?? new Date())

  const currentBase = computed<GlobeDestination>(() => {
    if (options.current) {
      return options.current
    }

    return {
      id: 'current-location',
      label: geoStore?.locationName ?? 'Current Location',
      lat: geoStore?.lat ?? 13.7563,
      lng: geoStore?.lng ?? 100.5018,
      timezone: geoStore?.timezone ?? 'Asia/Bangkok',
    }
  })

  const currentSnapshot = computed<GlobeDestinationSnapshot>(() => {
    if (solarStore) {
      return {
        ...currentBase.value,
        elevationDeg: Number(solarStore.elevationDeg),
        sunrise: solarStore.sunriseTime,
        sunset: solarStore.sunsetTime,
      }
    }

    return buildDestinationSnapshot(currentBase.value, anchorDate.value)
  })

  const destinations = shallowRef<GlobeDestination[]>(options.destinations ?? getDefaultDestinations())
  const selectedDestinationId = shallowRef<string | null>(null)

  const selectedDestination = computed<GlobeDestination | null>(
    () => destinations.value.find((destination) => destination.id === selectedDestinationId.value) ?? null,
  )

  const localSolar = computed(() =>
    buildLocalSolarSnapshot({
      elevationDeg: currentSnapshot.value.elevationDeg,
      phase: solarStore?.solarPhase ?? (currentSnapshot.value.elevationDeg > 0 ? 'Day' : 'Night'),
      sunrise: currentSnapshot.value.sunrise,
      sunset: currentSnapshot.value.sunset,
      timeZone: currentSnapshot.value.timezone,
    }),
  )

  const destinationSnapshots = computed(() =>
    destinations.value.map((destination) => buildDestinationSnapshot(destination, anchorDate.value)),
  )

  const comparisons = computed(() =>
    buildDestinationComparisons({
      anchorDate: anchorDate.value,
      current: currentSnapshot.value,
      destinations: destinationSnapshots.value,
    }),
  )

  const selectedComparison = computed(
    () => comparisons.value.find((comparison) => comparison.id === selectedDestinationId.value) ?? null,
  )

  const orbitalContext = computed(() => {
    if (!spaceWeatherStore) {
      return {
        label: 'Orbital context only',
        summary: 'ISS context is visual unless a live orbital data source is wired.',
      }
    }

    const stormLevel = spaceWeatherStore.disruptionLabel
    return {
      label: 'Contextual orbital layer',
      summary: `${stormLevel}. ISS and orbital context are observational, not a personal health forecast.`,
    }
  })

  function selectDestination(destinationId: string) {
    if (destinations.value.some((destination) => destination.id === destinationId)) {
      selectedDestinationId.value = destinationId
    }
  }

  function clearDestination() {
    selectedDestinationId.value = null
  }

  return {
    currentSnapshot,
    destinations: readonly(destinations),
    localSolar,
    comparisons,
    selectedDestinationId: readonly(selectedDestinationId),
    selectedDestination,
    selectedComparison,
    orbitalContext,
    selectDestination,
    clearDestination,
  }
}
