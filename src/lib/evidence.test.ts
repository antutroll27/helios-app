import { describe, expect, it } from 'vitest'
import { buildEvidenceProfile } from './evidence'

describe('buildEvidenceProfile', () => {
  it('normalizes the shared evidence structure', () => {
    const profile = buildEvidenceProfile({
      evidenceTier: 'B',
      effectSummary: '+16 min total sleep time in insomnia-focused trials',
      populationSummary: 'Adults with insomnia symptoms or low magnesium intake',
      mainCaveat: 'Population-level effect, not diagnosis',
      uncertaintyFactors: ['baseline deficiency', 'dose form'],
      claimBoundary: 'General wellness support only',
    })

    expect(profile.evidenceTier).toBe('B')
    expect(profile.uncertaintyFactors).toEqual(['baseline deficiency', 'dose form'])
  })

  it('rejects blank required text fields', () => {
    expect(() =>
      buildEvidenceProfile({
        evidenceTier: 'B',
        effectSummary: ' ',
        populationSummary: 'Adults with insomnia symptoms or low magnesium intake',
        mainCaveat: 'Population-level effect, not diagnosis',
        uncertaintyFactors: ['baseline deficiency'],
        claimBoundary: 'General wellness support only',
      }),
    ).toThrow('effectSummary')
  })
})
