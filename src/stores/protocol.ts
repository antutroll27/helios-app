import { defineStore } from 'pinia'
import { computed } from 'vue'
import { useSolarStore } from '@/stores/solar'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'
import { useUserStore } from '@/stores/user'
import { useEnvironmentStore } from '@/stores/environment'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ProtocolItem {
  key: string
  title: string
  time: Date
  icon: string
  citation: string
  subtitle: string
}

export interface DailyProtocol {
  wakeWindow: ProtocolItem
  morningLight: ProtocolItem
  peakFocus: ProtocolItem
  caffeineCutoff: ProtocolItem
  windDown: ProtocolItem
  sleepWindow: ProtocolItem
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Add minutes to a Date and return a new Date */
function addMinutes(date: Date, minutes: number): Date {
  return new Date(date.getTime() + minutes * 60_000)
}

/** Add hours to a Date and return a new Date */
function addHours(date: Date, hours: number): Date {
  return new Date(date.getTime() + hours * 60 * 60_000)
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useProtocolStore = defineStore('protocol', () => {
  const solar = useSolarStore()
  const spaceWeather = useSpaceWeatherStore()
  const user = useUserStore()
  const environment = useEnvironmentStore()

  // ─── Constants ──────────────────────────────────────────────────────────────

  /** Fixed caffeine half-life used throughout all calculations (hours) */
  const caffeineHalfLifeHours = 6

  // ─── Core timing anchors ────────────────────────────────────────────────────

  /**
   * Today's projected sleep time as a Date object.
   * Delegates to the user store's getSleepTimeToday() which advances to tomorrow
   * if the sleep time has already passed for today.
   */
  const sleepTime = computed<Date>(() => user.getSleepTimeToday())

  /**
   * Estimated melatonin onset: 90 minutes before sleep time.
   * This is the physiological anchor for all pre-sleep calculations.
   */
  const melatoninOnset = computed<Date>(() => addMinutes(sleepTime.value, -90))

  // ─── Derived protocol timings ────────────────────────────────────────────────

  /**
   * Latest safe caffeine consumption time.
   * = melatonin onset minus one full caffeine half-life (6 h).
   * This ensures caffeine concentration is below ~1/64 of peak by sleep onset
   * after enough half-lives, but more practically eliminates the acute
   * 40-minute melatonin-delay effect documented by Burke et al. (2015).
   */
  const caffeineCutoff = computed<Date>(() =>
    addHours(melatoninOnset.value, -caffeineHalfLifeHours)
  )

  /**
   * Start of peak cognitive performance window.
   * Core body temperature peak typically precedes sleep onset by ~3 h,
   * which correlates with maximal alertness and working memory capacity.
   */
  const peakFocusStart = computed<Date>(() => addHours(sleepTime.value, -3))

  /**
   * End of peak cognitive performance window.
   * 1 h before sleep time — beyond this point alertness begins declining
   * as melatonin secretion ramps up.
   */
  const peakFocusEnd = computed<Date>(() => addHours(sleepTime.value, -1))

  /**
   * Wind-down start time.
   * Baseline: 90 min before sleep (coincides with melatonin onset).
   * If geomagnetic disruption score >= 3 (storm-level), advance by 30 min
   * to buffer against cortisol elevation caused by elevated Kp-index activity.
   */
  const windDownStart = computed<Date>(() => {
    const base = addMinutes(sleepTime.value, -90)
    if (spaceWeather.disruptionScore >= 3) {
      return addMinutes(base, -30)
    }
    return base
  })

  // ─── Supplementary metrics ───────────────────────────────────────────────────

  /**
   * Social jet lag in minutes.
   * Defined as the absolute difference between the solar nadir (true biological
   * midnight based on sun position) and the user's sleep midpoint.
   * Sleep midpoint is estimated as sleep onset + 4 h (midpoint of an 8-h night).
   * Larger values indicate greater misalignment between solar and behavioural clocks.
   */
  const socialJetLagMinutes = computed<number>(() => {
    try {
      // Compare only the time-of-day components (ignore calendar date)
      const sleepMidpoint = addHours(sleepTime.value, 4)
      const nadirMinOfDay = solar.nadir.getHours() * 60 + solar.nadir.getMinutes()
      const midpointMinOfDay = sleepMidpoint.getHours() * 60 + sleepMidpoint.getMinutes()
      let diff = Math.abs(nadirMinOfDay - midpointMinOfDay)
      // Wrap around midnight — shortest angular distance on 24h clock
      if (diff > 720) diff = 1440 - diff
      // Sanity cap — social jet lag over 360 min (6h) is unreasonable
      return Math.min(Math.round(diff), 360)
    } catch {
      return 0
    }
  })

  /**
   * Recommended morning bright-light exposure duration in minutes.
   * Baseline: 20 min (sufficient for robust CAR and circadian entrainment).
   * Reduced to 10 min when AQI > 150 (Unhealthy category) to limit particulate
   * inhalation during mandatory outdoor exposure.
   */
  const morningLightDurationMin = computed<number>(() => {
    return environment.aqiLevel > 150 ? 10 : 20
  })

  // ─── Full daily protocol ─────────────────────────────────────────────────────

  /**
   * The complete daily biological protocol object.
   * Each item carries a key, human title, computed Date anchor, Lucide icon name,
   * peer-reviewed citation, and a context-aware subtitle.
   */
  const dailyProtocol = computed<DailyProtocol>(() => {
    const lightDuration = morningLightDurationMin.value
    const aqiWarning =
      environment.aqiLevel > 150
        ? ` (reduced to ${lightDuration} min — AQI ${environment.aqiLevel} is unhealthy)`
        : ` (${lightDuration} min)`

    const windDownAdj =
      spaceWeather.disruptionScore >= 3
        ? ' (advanced 30 min — geomagnetic storm active)'
        : ''

    const jetLagNote =
      socialJetLagMinutes.value > 60
        ? ` Social jet lag detected: ${Math.round(socialJetLagMinutes.value / 60 * 10) / 10} h.`
        : ''

    return {
      wakeWindow: (() => {
        // Smart wake: sleep time + 8h for adequate rest, but nudge toward sunrise if possible
        const idealWake = addHours(sleepTime.value, 8)
        const sunrise = solar.wakeWindowStart
        // If ideal wake is after sunrise, use ideal wake (night owl — don't sacrifice sleep)
        // If ideal wake is before sunrise, use sunrise (early bird — catch the light)
        const smartWake = idealWake > sunrise ? idealWake : sunrise
        const smartWakeEnd = addMinutes(smartWake, 30)
        const isNightOwl = idealWake > sunrise
        return {
          key: 'wakeWindow',
          title: 'Wake Window',
          time: smartWake,
          icon: 'Sunrise',
          citation:
            'Cortisol awakening response peaks within 30 min of solar elevation > 6°',
          subtitle: isNightOwl
            ? `Rise at ${fmt(smartWake)} (8h sleep). Get sunlight within 30 min of waking.`
            : `Rise between ${fmt(smartWake)} – ${fmt(smartWakeEnd)} to anchor your circadian clock.`
        }
      })(),

      morningLight: {
        key: 'morningLight',
        title: 'Morning Light',
        time: solar.wakeWindowEnd,
        icon: 'Sun',
        citation:
          'NASA ISS protocol: timed bright light for circadian entrainment',
        subtitle:
          `Get ${lightDuration} min of bright outdoor light starting at ${fmt(solar.wakeWindowStart)}${aqiWarning}.`
      },

      peakFocus: {
        key: 'peakFocus',
        title: 'Peak Focus',
        time: peakFocusStart.value,
        icon: 'Brain',
        citation:
          'Core body temperature peak aligns with cognitive performance maximum',
        subtitle:
          `Schedule deep work ${fmt(peakFocusStart.value)} – ${fmt(peakFocusEnd.value)} for maximal cognitive output.`
      },

      caffeineCutoff: {
        key: 'caffeineCutoff',
        title: 'Caffeine Cutoff',
        time: caffeineCutoff.value,
        icon: 'Coffee',
        citation:
          'Burke et al. (2015): caffeine 3h before bed delays melatonin by 40 min',
        subtitle:
          `No caffeine after ${fmt(caffeineCutoff.value)} to protect melatonin onset at ${fmt(melatoninOnset.value)}.`
      },

      windDown: {
        key: 'windDown',
        title: 'Wind-Down',
        time: windDownStart.value,
        icon: 'Moon',
        citation:
          'Begin screen dimming 90 min before estimated melatonin onset',
        subtitle:
          `Start dimming screens and lowering stimulation at ${fmt(windDownStart.value)}${windDownAdj}.`
      },

      sleepWindow: {
        key: 'sleepWindow',
        title: 'Sleep Window',
        time: sleepTime.value,
        icon: 'BedDouble',
        citation:
          'Optimal sleep onset aligned with solar cycle and chronotype',
        subtitle:
          `Target sleep by ${fmt(sleepTime.value)} (${user.chronotype} chronotype).${jetLagNote}`
      }
    }
  })

  // ─── Utility ─────────────────────────────────────────────────────────────────

  return {
    // constants
    caffeineHalfLifeHours,

    // computed timings
    sleepTime,
    melatoninOnset,
    caffeineCutoff,
    peakFocusStart,
    peakFocusEnd,
    windDownStart,

    // metrics
    socialJetLagMinutes,
    morningLightDurationMin,

    // full protocol
    dailyProtocol
  }
})

// ─── Internal formatter (not exported) ───────────────────────────────────────

function fmt(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
