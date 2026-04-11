import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import SunCalc from 'suncalc'
import { getTimezoneOffsetHours } from '@/lib/timezoneUtils'

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface TripInput {
  originTz: string
  destinationTz: string
  travelDate: string // ISO date string, e.g. "2026-04-15"
  destinationLat: number
  destinationLng: number
}

export interface DayProtocol {
  day: number
  date: Date
  lightWindowStart: Date
  lightWindowEnd: Date
  caffeineWindow: { open: Date; close: Date }
  targetSleepTime: Date
  targetWakeTime: Date
  phaseShiftDirection: 'advance' | 'delay'
  phaseShiftHours: number
  totalShiftNeeded: number
}

// ─── Timezone → city metadata ─────────────────────────────────────────────────

export interface CityMeta {
  lat: number
  lng: number
  label: string
}

export const TIMEZONE_CITIES: Record<string, CityMeta> = {
  'America/New_York': { lat: 40.7128, lng: -74.006, label: 'New York' },
  'America/Los_Angeles': { lat: 34.0522, lng: -118.2437, label: 'Los Angeles' },
  'America/Chicago': { lat: 41.8781, lng: -87.6298, label: 'Chicago' },
  'America/Denver': { lat: 39.7392, lng: -104.9903, label: 'Denver' },
  'Europe/London': { lat: 51.5074, lng: -0.1278, label: 'London' },
  'Europe/Paris': { lat: 48.8566, lng: 2.3522, label: 'Paris' },
  'Europe/Berlin': { lat: 52.52, lng: 13.405, label: 'Berlin' },
  'Europe/Moscow': { lat: 55.7558, lng: 37.6173, label: 'Moscow' },
  'Asia/Tokyo': { lat: 35.6762, lng: 139.6503, label: 'Tokyo' },
  'Asia/Shanghai': { lat: 31.2304, lng: 121.4737, label: 'Shanghai' },
  'Asia/Singapore': { lat: 1.3521, lng: 103.8198, label: 'Singapore' },
  'Asia/Dubai': { lat: 25.2048, lng: 55.2708, label: 'Dubai' },
  'Asia/Kolkata': { lat: 28.6139, lng: 77.209, label: 'New Delhi' },
  'Asia/Ho_Chi_Minh': { lat: 10.8231, lng: 106.6297, label: 'Ho Chi Minh City' },
  'Asia/Bangkok': { lat: 13.7563, lng: 100.5018, label: 'Bangkok' },
  'Australia/Sydney': { lat: -33.8688, lng: 151.2093, label: 'Sydney' },
  'Pacific/Auckland': { lat: -36.8485, lng: 174.7633, label: 'Auckland' },
  'Africa/Lagos': { lat: 6.5244, lng: 3.3792, label: 'Lagos' },
  'America/Sao_Paulo': { lat: -23.5505, lng: -46.6333, label: 'São Paulo' }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Build a Date on a specific calendar date (in local clock terms of the
 * destination timezone) at a given hour:minute.
 * Since JavaScript Dates are always UTC internally, we construct the value by
 * using the target timezone offset to back-compute the UTC instant.
 */
function buildDateInTz(
  isoDate: string, // "YYYY-MM-DD"
  hourOfDay: number,
  minuteOfHour: number,
  tzOffsetHours: number
): Date {
  const [year, month, day] = isoDate.split('-').map(Number)
  // Local noon as UTC: subtract the offset
  const utcMs =
    Date.UTC(year, month - 1, day, hourOfDay, minuteOfHour, 0) -
    tzOffsetHours * 3_600_000
  return new Date(utcMs)
}

/** Advance a Date by N days */
function addDays(date: Date, days: number): Date {
  return new Date(date.getTime() + days * 86_400_000)
}

/** Advance a Date by N hours */
function addHours(date: Date, hours: number): Date {
  return new Date(date.getTime() + hours * 3_600_000)
}

/** Format an ISO date "YYYY-MM-DD" from a Date */
function toIsoDate(date: Date): string {
  return date.toISOString().substring(0, 10)
}

// ─── Core schedule generator ──────────────────────────────────────────────────

/**
 * Generates a day-by-day jet-lag recovery protocol.
 *
 * Science basis:
 * - The circadian clock can shift at most ~1.5 h per day under optimal light
 *   exposure (NASA ISS research; Czeisler et al.).
 * - Eastward travel (positive offset delta) requires phase advance:
 *   bright morning light + earlier sleep each night.
 * - Westward travel (negative offset delta) requires phase delay:
 *   bright evening light + later sleep each night.
 * - Caffeine is permitted from local wake time and cut off 6 h before the
 *   target sleep time as a conservative default to reduce residual caffeine
 *   burden and possible sleep disruption or circadian phase delay.
 */
function generateJetLagSchedule(input: TripInput): DayProtocol[] {
  const travelDate = new Date(input.travelDate + 'T12:00:00Z') // noon UTC anchor

  const originOffset = getTimezoneOffsetHours(input.originTz, travelDate)
  const destOffset = getTimezoneOffsetHours(input.destinationTz, travelDate)

  const totalShiftHours = destOffset - originOffset

  if (totalShiftHours === 0) {
    // No phase shift required — return a single day with no adjustments
    const sunTimes = SunCalc.getTimes(travelDate, input.destinationLat, input.destinationLng)
    const sleepTime = buildDateInTz(input.travelDate, 23, 0, destOffset)
    const wakeTime = buildDateInTz(input.travelDate, 7, 0, destOffset)

    const result: DayProtocol = {
      day: 1,
      date: travelDate,
      lightWindowStart: sunTimes.sunrise,
      lightWindowEnd: addHours(sunTimes.sunrise, 1),
      caffeineWindow: {
        open: wakeTime,
        close: addHours(sleepTime, -6)
      },
      targetSleepTime: sleepTime,
      targetWakeTime: wakeTime,
      phaseShiftDirection: 'advance',
      phaseShiftHours: 0,
      totalShiftNeeded: 0
    }
    return [result]
  }

  const direction: 'advance' | 'delay' = totalShiftHours > 0 ? 'advance' : 'delay'
  const absShift = Math.abs(totalShiftHours)

  // Max 1.5 h shift per day (NASA protocol)
  const MAX_SHIFT_PER_DAY = 1.5
  const daysNeeded = Math.ceil(absShift / MAX_SHIFT_PER_DAY)

  // Estimate the traveller's origin sleep/wake baseline in destination local time.
  // The user lands and their body is still on origin time: origin sleep time ≈ 23:00
  // expressed in destination-local hours = 23 + (destOffset - originOffset).
  const originSleepLocalHour = 23 + totalShiftHours // destination-local hour on day 0
  const originWakeLocalHour = 7 + totalShiftHours //  destination-local hour on day 0

  const schedule: DayProtocol[] = []

  for (let i = 0; i < daysNeeded; i++) {
    const currentDate = addDays(travelDate, i)
    const currentIso = toIsoDate(currentDate)

    // Increment applied so far on this day (index i means i full shifts done)
    const shiftApplied = Math.min((i + 1) * MAX_SHIFT_PER_DAY, absShift)
    const dailyShift = i === 0 ? Math.min(MAX_SHIFT_PER_DAY, absShift) : Math.min(MAX_SHIFT_PER_DAY, absShift - i * MAX_SHIFT_PER_DAY)

    // Target sleep/wake for this day in destination-local hours
    let targetSleepLocalHour: number
    let targetWakeLocalHour: number

    if (direction === 'advance') {
      // Sleep and wake progressively earlier
      targetSleepLocalHour = originSleepLocalHour - shiftApplied
      targetWakeLocalHour = originWakeLocalHour - shiftApplied
    } else {
      // Sleep and wake progressively later
      targetSleepLocalHour = originSleepLocalHour + shiftApplied
      targetWakeLocalHour = originWakeLocalHour + shiftApplied
    }

    // Normalise hour into 0-47 range (allows crossing midnight)
    const normSleepH = ((targetSleepLocalHour % 24) + 24) % 24
    const normWakeH = ((targetWakeLocalHour % 24) + 24) % 24

    const sleepHour = Math.floor(normSleepH)
    const sleepMinute = Math.round((normSleepH - sleepHour) * 60)
    const wakeHour = Math.floor(normWakeH)
    const wakeMinute = Math.round((normWakeH - wakeHour) * 60)

    const targetSleepTime = buildDateInTz(currentIso, sleepHour, sleepMinute, destOffset)
    const targetWakeTime = buildDateInTz(currentIso, wakeHour, wakeMinute, destOffset)

    // SunCalc times at the destination for light-window placement
    const sunTimes = SunCalc.getTimes(currentDate, input.destinationLat, input.destinationLng)

    let lightWindowStart: Date
    let lightWindowEnd: Date

    if (direction === 'advance') {
      // Eastward: morning light is the phase-advance cue
      // Use sunrise as the anchor; ensure it's after wake time
      lightWindowStart = sunTimes.sunrise.getTime() < targetWakeTime.getTime()
        ? targetWakeTime
        : sunTimes.sunrise
      lightWindowEnd = addHours(lightWindowStart, 1)
    } else {
      // Westward: evening light is the phase-delay cue
      // Use golden hour / 2 h before sunset as anchor
      lightWindowStart = addHours(sunTimes.sunset, -2)
      lightWindowEnd = sunTimes.sunset
    }

    // Caffeine: open at wake, close 6 h before target sleep as the default conservative cutoff
    const caffeineOpen = targetWakeTime
    const caffeineClose = addHours(targetSleepTime, -6)

    schedule.push({
      day: i + 1,
      date: currentDate,
      lightWindowStart,
      lightWindowEnd,
      caffeineWindow: { open: caffeineOpen, close: caffeineClose },
      targetSleepTime,
      targetWakeTime,
      phaseShiftDirection: direction,
      phaseShiftHours: Math.round(dailyShift * 10) / 10,
      totalShiftNeeded: Math.round(absShift * 10) / 10
    })
  }

  return schedule
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useJetLagStore = defineStore('jetlag', () => {
  // ─── State ────────────────────────────────────────────────────────────────

  const tripInput = ref<TripInput | null>(null)

  // ─── Computed ─────────────────────────────────────────────────────────────

  /**
   * Reactively derived recovery schedule.
   * Returns an empty array when no trip input has been set.
   */
  const schedule = computed<DayProtocol[]>(() => {
    if (!tripInput.value) return []
    return generateJetLagSchedule(tripInput.value)
  })

  /**
   * Total phase shift hours required for this trip.
   * Positive = eastward (advance); negative = westward (delay).
   */
  const totalShiftHours = computed<number>(() => {
    if (!tripInput.value) return 0
    const anchor = new Date(tripInput.value.travelDate + 'T12:00:00Z')
    const originOffset = getTimezoneOffsetHours(tripInput.value.originTz, anchor)
    const destOffset = getTimezoneOffsetHours(tripInput.value.destinationTz, anchor)
    return Math.round((destOffset - originOffset) * 10) / 10
  })

  /**
   * Number of recovery days needed at maximum 1.5 h/day shift rate.
   * Returns 1 when there is no phase shift (no-jet-lag baseline day still shown).
   */
  const recoveryDays = computed<number>(() => {
    const abs = Math.abs(totalShiftHours.value)
    if (abs === 0) return tripInput.value ? 1 : 0
    return Math.ceil(abs / 1.5)
  })

  /**
   * Phase shift direction for the current trip.
   */
  const shiftDirection = computed<'advance' | 'delay' | null>(() => {
    if (!tripInput.value) return null
    return totalShiftHours.value > 0 ? 'advance' : 'delay'
  })

  // ─── Actions ───────────────────────────────────────────────────────────────

  function setTrip(input: TripInput): void {
    tripInput.value = { ...input }
  }

  function clearTrip(): void {
    tripInput.value = null
  }

  // ─── Exports ───────────────────────────────────────────────────────────────

  return {
    tripInput,
    schedule,
    totalShiftHours,
    recoveryDays,
    shiftDirection,
    setTrip,
    clearTrip
  }
})
