export type Chronotype = 'early' | 'intermediate' | 'late'

export function getDeepWorkWindowOffsets(chronotype: Chronotype): {
  startHoursAfterWake: number
  endHoursAfterWake: number
} {
  if (chronotype === 'early') return { startHoursAfterWake: 5, endHoursAfterWake: 8 }
  if (chronotype === 'late') return { startHoursAfterWake: 8, endHoursAfterWake: 11 }
  return { startHoursAfterWake: 6, endHoursAfterWake: 9 }
}

export function getAlignmentMetricCopy(): {
  label: string
  description: string
} {
  return {
    label: 'SOLAR ALIGNMENT',
    description: 'Difference between solar midnight and your estimated sleep midpoint.'
  }
}

export function getCaffeineCutoffNarrative(cutoffTime: string, estimatedSleepTime: string): string {
  return `default conservative cutoff: no caffeine after ${cutoffTime}. This reduces residual caffeine near ${estimatedSleepTime} and lowers the risk of possible circadian phase delay or sleep disruption, but it does not guarantee safety for every dose or every metabolism.`
}
