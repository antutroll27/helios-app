import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it } from 'vitest'

import { useGeoStore } from '@/stores/geo'
import { useSolarStore } from '@/stores/solar'
import {
  buildDestinationComparisons,
  buildLocalSolarSnapshot,
  getInitialSelectedDestinationId,
  useCobeGlobeData,
} from './useCobeGlobeData'

describe('buildLocalSolarSnapshot', () => {
  it('formats the local solar snapshot for the HUD', () => {
    const snapshot = buildLocalSolarSnapshot({
      elevationDeg: 17.4,
      phase: 'Day',
      sunrise: new Date('2026-04-10T23:12:00Z'),
      sunset: new Date('2026-04-10T11:21:00Z'),
      timeZone: 'Asia/Bangkok',
    })

    expect(snapshot.elevationDeg).toBe(17.4)
    expect(snapshot.phase).toBe('Day')
    expect(snapshot.sunriseLabel).toBe('06:12')
    expect(snapshot.sunsetLabel).toBe('18:21')
  })
})

describe('buildDestinationComparisons', () => {
  it('derives timezone, solar, and travel context for multiple destinations', () => {
    const comparisons = buildDestinationComparisons({
      anchorDate: new Date('2026-04-10T12:00:00Z'),
      current: {
        id: 'current',
        label: 'Bangkok',
        lat: 13.7563,
        lng: 100.5018,
        timezone: 'Asia/Bangkok',
        elevationDeg: 52.1,
        sunrise: new Date('2026-04-10T23:11:00Z'),
        sunset: new Date('2026-04-10T11:36:00Z'),
      },
      destinations: [
        {
          id: 'tokyo',
          label: 'Tokyo',
          lat: 35.6762,
          lng: 139.6503,
          timezone: 'Asia/Tokyo',
          elevationDeg: 34.2,
          sunrise: new Date('2026-04-10T20:19:00Z'),
          sunset: new Date('2026-04-10T09:11:00Z'),
        },
        {
          id: 'london',
          label: 'London',
          lat: 51.5074,
          lng: -0.1278,
          timezone: 'Europe/London',
          elevationDeg: 11.6,
          sunrise: new Date('2026-04-10T05:18:00Z'),
          sunset: new Date('2026-04-10T18:42:00Z'),
        },
      ],
    })

    expect(comparisons).toHaveLength(2)
    expect(comparisons[0]).toMatchObject({
      id: 'tokyo',
      timezoneDeltaHours: 2,
      travelReadiness: 'Light shift. Low travel strain expected.',
    })
    expect(comparisons[1]).toMatchObject({
      id: 'london',
      timezoneDeltaHours: -6,
      travelReadiness: 'Large shift. Expect meaningful circadian strain.',
    })
  })
})

describe('initial selected destination behavior', () => {
  it('prefers the first destination when no selection is provided', () => {
    expect(
      getInitialSelectedDestinationId([
        { id: 'tokyo', label: 'Tokyo' },
        { id: 'london', label: 'London' },
      ]),
    ).toBe('tokyo')
  })

  it('returns null when there are no destinations', () => {
    expect(getInitialSelectedDestinationId([])).toBeNull()
  })

  it('initializes the composable in countdown mode (no destination selected by default)', () => {
    const globe = useCobeGlobeData({
      current: {
        id: 'current',
        label: 'Bangkok',
        lat: 13.7563,
        lng: 100.5018,
        timezone: 'Asia/Bangkok',
      },
      destinations: [
        {
          id: 'tokyo',
          label: 'Tokyo',
          lat: 35.6762,
          lng: 139.6503,
          timezone: 'Asia/Tokyo',
        },
        {
          id: 'london',
          label: 'London',
          lat: 51.5074,
          lng: -0.1278,
          timezone: 'Europe/London',
        },
      ],
      now: new Date('2026-04-10T12:00:00Z'),
    })

    expect(globe.selectedDestinationId.value).toBeNull()
    expect(globe.selectedDestination.value).toBeNull()
  })

  it('reacts to store-backed location and solar updates', () => {
    setActivePinia(createPinia())

    const geoStore = useGeoStore()
    const solarStore = useSolarStore()

    geoStore.locationName = 'Da Nang, Vietnam'
    geoStore.timezone = 'Asia/Bangkok'
    geoStore.lat = 16.0544
    geoStore.lng = 108.2022
    solarStore.now = new Date('2026-04-10T12:00:00Z')
    solarStore.refreshNow()

    const globe = useCobeGlobeData()
    expect(globe.currentSnapshot.value.label).toBe('Da Nang, Vietnam')

    geoStore.locationName = 'Tokyo, Japan'
    geoStore.timezone = 'Asia/Tokyo'
    geoStore.lat = 35.6762
    geoStore.lng = 139.6503
    solarStore.now = new Date('2026-04-10T03:00:00Z')

    expect(globe.currentSnapshot.value.label).toBe('Tokyo, Japan')
    expect(globe.currentSnapshot.value.timezone).toBe('Asia/Tokyo')
    expect(globe.localSolar.value.phase.length).toBeGreaterThan(0)
  })
})
