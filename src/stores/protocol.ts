import { defineStore } from 'pinia'
import { computed } from 'vue'
import {
  getAlignmentMetricCopy,
  getCaffeineCutoffNarrative,
  getDeepWorkWindowOffsets,
} from '@/lib/circadianTruth'
import { fmtTime as fmt } from '@/lib/timezoneUtils'
import { useEnvironmentStore } from '@/stores/environment'
import { useSolarStore } from '@/stores/solar'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'
import { useUserStore } from '@/stores/user'

export interface VizData {
  supLabel: string       // superscript next to time: "AM" | "20 MIN" | "3H WIN" | "6H T½" | "90 MIN" | "LATE"
  ringPct?: number       // 0–100, for ring cards (Wind-Down, Sleep Window)
  ringCenter?: string    // text inside ring: "90" | alignment score string
  ringUnit?: string      // unit below ring center: "MIN" | "ALIGN%"
  stat1Label?: string
  stat1Value?: string
  stat2Label?: string
  stat2Value?: string
}

export interface ProtocolItem {
  key: string
  title: string
  time: Date
  endTime?: Date
  icon: string
  citation: string
  subtitle: string
  vizData?: VizData
}

export interface DailyProtocol {
  wakeWindow: ProtocolItem
  morningLight: ProtocolItem
  peakFocus: ProtocolItem
  caffeineCutoff: ProtocolItem
  windDown: ProtocolItem
  sleepWindow: ProtocolItem
}

function addMinutes(date: Date, minutes: number): Date {
  return new Date(date.getTime() + minutes * 60_000)
}

function addHours(date: Date, hours: number): Date {
  return new Date(date.getTime() + hours * 60 * 60_000)
}

export const useProtocolStore = defineStore('protocol', () => {
  const solar = useSolarStore()
  const spaceWeather = useSpaceWeatherStore()
  const user = useUserStore()
  const environment = useEnvironmentStore()

  const caffeineHalfLifeHours = 6

  const sleepTime = computed<Date>(() => {
    void solar.now
    return user.getSleepTimeToday()
  })

  const melatoninOnset = computed<Date>(() => addMinutes(sleepTime.value, -90))

  const wakeWindowTime = computed<Date>(() => {
    const idealWake = addHours(sleepTime.value, 8)
    return idealWake.getTime() > solar.wakeWindowStart.getTime() ? idealWake : solar.wakeWindowStart
  })

  const wakeWindowEnd = computed<Date>(() => addMinutes(wakeWindowTime.value, 30))

  /**
   * Default conservative caffeine cutoff.
   * = estimated melatonin onset minus one default half-life (6 h).
   * This reduces residual caffeine burden near bedtime, but it is not a
   * personalized guarantee for every dose or metabolism.
   */
  const caffeineCutoff = computed<Date>(() =>
    addHours(melatoninOnset.value, -caffeineHalfLifeHours)
  )

  /**
   * HELIOS uses a chronotype-based daytime heuristic rather than the pre-sleep
   * wake-maintenance zone as the default deep-work window.
   */
  const deepWorkWindowOffsets = computed(() => getDeepWorkWindowOffsets(user.chronotype))

  const peakFocusStart = computed<Date>(() =>
    addHours(wakeWindowTime.value, deepWorkWindowOffsets.value.startHoursAfterWake)
  )

  const peakFocusEnd = computed<Date>(() =>
    addHours(wakeWindowTime.value, deepWorkWindowOffsets.value.endHoursAfterWake)
  )

  /**
   * If geomagnetic disruption score >= 3 (storm-level), advance wind-down by
   * 30 min as a conservative recovery cue rather than a deterministic forecast.
   */
  const windDownStart = computed<Date>(() => {
    const base = addMinutes(sleepTime.value, -90)
    if (spaceWeather.disruptionScore >= 3) {
      return addMinutes(base, -30)
    }
    return base
  })

  /**
   * Solar alignment gap in minutes.
   * Defined as the absolute difference between solar nadir and the user's
   * estimated sleep midpoint. This is not the standard workday-vs-free-day
   * social jet lag metric.
   */
  const solarAlignmentGapMinutes = computed<number>(() => {
    try {
      const sleepMidpoint = addHours(sleepTime.value, 4)
      const nadirMinOfDay = solar.nadir.getHours() * 60 + solar.nadir.getMinutes()
      const midpointMinOfDay = sleepMidpoint.getHours() * 60 + sleepMidpoint.getMinutes()
      let diff = Math.abs(nadirMinOfDay - midpointMinOfDay)
      if (diff > 720) diff = 1440 - diff
      return Math.min(Math.round(diff), 360)
    } catch {
      return 0
    }
  })

  const morningLightDurationMin = computed<number>(() => {
    return environment.aqiLevel > 150 ? 10 : 20
  })

  const dailyProtocol = computed<DailyProtocol>(() => {
    const lightDuration = morningLightDurationMin.value
    const alignmentMetricCopy = getAlignmentMetricCopy()
    const aqiWarning =
      environment.aqiLevel > 150
        ? ` (reduced to ${lightDuration} min - AQI ${environment.aqiLevel} is unhealthy)`
        : ` (${lightDuration} min)`

    const windDownAdj =
      spaceWeather.disruptionScore >= 3
        ? ' (advanced 30 min as a conservative recovery adjustment during storm conditions)'
        : ''

    const solarAlignmentNote =
      solarAlignmentGapMinutes.value > 60
        ? ` ${alignmentMetricCopy.label}: ${Math.round(solarAlignmentGapMinutes.value / 60 * 10) / 10} h from solar midnight.`
        : ''

    const isNightOwlWake = wakeWindowTime.value.getTime() > solar.wakeWindowStart.getTime()

    return {
      wakeWindow: {
        key: 'wakeWindow',
        title: 'Wake Window',
        time: wakeWindowTime.value,
        endTime: wakeWindowEnd.value,
        icon: 'Sunrise',
        citation: 'Cortisol awakening response peaks within 30 min of solar elevation > 6 degrees',
        subtitle: isNightOwlWake
          ? `Rise at ${fmt(wakeWindowTime.value)} (8h sleep). Get sunlight within 30 min of waking.`
          : `Rise between ${fmt(wakeWindowTime.value)} - ${fmt(wakeWindowEnd.value)} to anchor your circadian clock.`,
        vizData: {
          supLabel: 'AM',
          stat1Label: 'Window',
          stat1Value: `${Math.round((wakeWindowEnd.value.getTime() - wakeWindowTime.value.getTime()) / 60_000)} min`,
          stat2Label: 'Sleep',
          stat2Value: (() => {
            const ms = wakeWindowTime.value.getTime() - sleepTime.value.getTime()
            const h = Math.floor(ms / 3_600_000)
            const m = Math.round((ms % 3_600_000) / 60_000)
            return `${h}h ${m}m`
          })(),
        },
      },

      morningLight: {
        key: 'morningLight',
        title: 'Morning Light',
        time: solar.wakeWindowEnd,
        endTime: new Date(solar.wakeWindowEnd.getTime() + morningLightDurationMin.value * 60_000),
        icon: 'Sun',
        citation: 'NASA ISS protocol: timed bright light for circadian entrainment',
        subtitle: `Get ${lightDuration} min of bright outdoor light starting at ${fmt(solar.wakeWindowStart)}${aqiWarning}.`,
        vizData: {
          supLabel: `${morningLightDurationMin.value} MIN`,
        },
      },

      peakFocus: {
        key: 'peakFocus',
        title: 'Peak Focus',
        time: peakFocusStart.value,
        endTime: peakFocusEnd.value,
        icon: 'Brain',
        citation: 'Cognitive performance peaks in late afternoon/evening, paralleling core body temperature rhythm',
        subtitle: `Recommended deep-work window: ${fmt(peakFocusStart.value)} - ${fmt(peakFocusEnd.value)}. The pre-sleep wake-maintenance zone is a separate alertness phenomenon, not your default best focus window.`,
        vizData: {
          supLabel: '3H WIN',
        },
      },

      caffeineCutoff: {
        key: 'caffeineCutoff',
        title: 'Caffeine Cutoff',
        time: caffeineCutoff.value,
        icon: 'Coffee',
        citation: 'Burke et al. (2015): caffeine 3h before bed delays melatonin by 40 min',
        subtitle: getCaffeineCutoffNarrative(fmt(caffeineCutoff.value), fmt(sleepTime.value)),
        vizData: {
          supLabel: '6H T½',
        },
      },

      windDown: {
        key: 'windDown',
        title: 'Wind-Down',
        time: windDownStart.value,
        endTime: sleepTime.value,
        icon: 'Moon',
        citation: 'Begin screen dimming 90 min before estimated melatonin onset',
        subtitle: `Start dimming screens and lowering stimulation at ${fmt(windDownStart.value)}${windDownAdj}.`,
        vizData: (() => {
          const durationMin = Math.round(
            (sleepTime.value.getTime() - windDownStart.value.getTime()) / 60_000
          )
          const h = Math.floor(durationMin / 60)
          const m = durationMin % 60
          return {
            supLabel: `${durationMin} MIN`,
            ringPct: Math.min(Math.round((durationMin / 180) * 100), 100),
            ringCenter: String(durationMin),
            ringUnit: 'MIN',
            stat1Label: 'Until sleep',
            stat1Value: h > 0 ? `${h}h${m > 0 ? ` ${m}m` : ''}` : `${m}m`,
            stat2Label: 'Melatonin onset',
            stat2Value: fmt(melatoninOnset.value),
          }
        })(),
      },

      sleepWindow: {
        key: 'sleepWindow',
        title: 'Sleep Window',
        time: sleepTime.value,
        icon: 'BedDouble',
        citation: 'Optimal sleep onset aligned with solar cycle and chronotype',
        subtitle: `Target sleep by ${fmt(sleepTime.value)} (${user.chronotype} chronotype).${solarAlignmentNote}`,
        vizData: (() => {
          const nadir = solar.nadir
          const gapMs = Math.abs(sleepTime.value.getTime() - nadir.getTime())
          const gapH = (gapMs / 3_600_000).toFixed(1)
          const alignPct = Math.max(0, Math.round((1 - gapMs / (6 * 3_600_000)) * 100))
          return {
            supLabel: 'LATE',
            ringPct: alignPct,
            ringCenter: String(alignPct),
            ringUnit: 'ALIGN%',
            stat1Label: 'Solar gap',
            stat1Value: `${gapH}h`,
            stat2Label: 'Solar midnight',
            stat2Value: fmt(nadir),
          }
        })(),
      },
    }
  })

  return {
    caffeineHalfLifeHours,
    sleepTime,
    melatoninOnset,
    caffeineCutoff,
    peakFocusStart,
    peakFocusEnd,
    windDownStart,
    solarAlignmentGapMinutes,
    morningLightDurationMin,
    dailyProtocol,
  }
})
