import { describe, expect, it } from 'vitest'
import { scoreSupplements } from './useSupplementGuide'
import type { SupplementGuideContext } from './useSupplementGuide'

function buildContext(overrides: Partial<SupplementGuideContext> = {}): SupplementGuideContext {
  return {
    goal: 'sleep_onset',
    chronotype: 'intermediate',
    travelState: 'none',
    hrv: null,
    sleepScore: null,
    totalSleepHours: null,
    ...overrides,
  }
}

describe('scoreSupplements', () => {
  it('circadian realignment with eastbound shift and late chronotype ranks melatonin first', () => {
    const results = scoreSupplements(
      buildContext({
        goal: 'circadian_realignment',
        travelState: 'eastbound_shift',
        chronotype: 'late',
      }),
    )

    expect(results[0].key).toBe('melatonin')
    expect(results[0].isTopPick).toBe(true)
    expect(results[0].clinicianDisclaimer.length).toBeGreaterThan(0)
    expect(results[0].caveat.length).toBeGreaterThan(0)
    expect(results[0].note.length).toBeGreaterThan(0)
  })

  it('recovery support with low HRV and shorter sleep ranks magnesium ahead of glycine', () => {
    const results = scoreSupplements(
      buildContext({
        goal: 'recovery_support',
        hrv: 32,
        sleepScore: 68,
        totalSleepHours: 6.1,
      }),
    )

    const magnesium = results.find((supplement) => supplement.key === 'magnesium')
    const glycine = results.find((supplement) => supplement.key === 'glycine')

    expect(results[0].key).toBe('magnesium')
    expect(magnesium?.score).toBeGreaterThan(glycine?.score ?? -1)
    expect(magnesium?.evidenceTier).toBe('B')
    expect(magnesium?.clinicianDisclaimer.length).toBeGreaterThan(0)
    expect(glycine?.caveat.length).toBeGreaterThan(0)
  })

  it('sleep onset ties resolve toward the more goal-specific option', () => {
    const results = scoreSupplements(
      buildContext({
        goal: 'sleep_onset',
        sleepScore: 70,
      }),
    )

    expect(results[0].key).toBe('glycine')
    expect(results[1].key).toBe('magnesium')
  })

  it('healthy null-like inputs stay bounded and keep notes plus disclaimers', () => {
    const results = scoreSupplements(
      buildContext({
        goal: 'sleep_onset',
        hrv: null,
        sleepScore: null,
        totalSleepHours: null,
      }),
    )

    expect(results.every((supplement) => supplement.score === 0)).toBe(true)
    expect(results.every((supplement) => supplement.isTopPick === false)).toBe(true)
    expect(results.every((supplement) => supplement.note.length > 0)).toBe(true)
    expect(results.every((supplement) => supplement.caveat.length > 0)).toBe(true)
    expect(results.every((supplement) => supplement.clinicianDisclaimer.length > 0)).toBe(true)
    expect(results.every((supplement) => supplement.contraindications.length > 0)).toBe(true)
  })

  it('exact boundary values remain untriggered', () => {
    const results = scoreSupplements(
      buildContext({
        goal: 'recovery_support',
        hrv: 40,
        sleepScore: 75,
        totalSleepHours: 7.0,
      }),
    )

    expect(results.every((supplement) => supplement.score === 0)).toBe(true)
    expect(results.every((supplement) => supplement.isTopPick === false)).toBe(true)
  })
})
