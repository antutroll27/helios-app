import { describe, expect, it } from 'vitest'
import {
  getAlignmentMetricCopy,
  getCaffeineCutoffNarrative,
  getDeepWorkWindowOffsets
} from './circadianTruth'

describe('getDeepWorkWindowOffsets', () => {
  it('moves the recommended deep-work window earlier for early chronotypes', () => {
    expect(getDeepWorkWindowOffsets('early')).toEqual({
      startHoursAfterWake: 5,
      endHoursAfterWake: 8
    })
  })

  it('uses a middle daytime window for intermediate chronotypes', () => {
    expect(getDeepWorkWindowOffsets('intermediate')).toEqual({
      startHoursAfterWake: 6,
      endHoursAfterWake: 9
    })
  })

  it('moves the recommended deep-work window later for late chronotypes', () => {
    expect(getDeepWorkWindowOffsets('late')).toEqual({
      startHoursAfterWake: 8,
      endHoursAfterWake: 11
    })
  })
})

describe('getAlignmentMetricCopy', () => {
  it('does not label the solar-midnight proxy as social jet lag', () => {
    const copy = getAlignmentMetricCopy()
    expect(copy.label).toBe('SOLAR ALIGNMENT')
    expect(copy.description).toContain('solar midnight')
    expect(copy.description).not.toContain('workday')
    expect(copy.description).not.toContain('Social Jet Lag')
  })
})

describe('getCaffeineCutoffNarrative', () => {
  it('uses default-risk language instead of guaranteed safety or melatonin suppression language', () => {
    const text = getCaffeineCutoffNarrative('16:00', '21:30')
    expect(text).toContain('default conservative cutoff')
    expect(text).toContain('possible circadian phase delay')
    expect(text).not.toContain('guarantees safety')
    expect(text).not.toContain('melatonin suppression')
  })
})
