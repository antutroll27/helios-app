import { describe, it, expect } from 'vitest'
import { calculateBreathworkResponse } from './useBreathwork'

describe('calculateBreathworkResponse', () => {
  it('resonance 20min > box 5min', () => {
    const a = calculateBreathworkResponse('resonance', 20)
    const b = calculateBreathworkResponse('box', 5)
    expect(a.rmssdBoost).toBeGreaterThan(b.rmssdBoost)
  })
  it('extended-exhale techniques apply ratio bonus', () => {
    // resonance baseBoost(30) × 0.75 × 1.15 = 25.875 → 26
    // box baseBoost(20) × 0.75 × 1.0 = 15
    const withBonus    = calculateBreathworkResponse('resonance', 10)
    const withoutBonus = calculateBreathworkResponse('box', 10)
    expect(withBonus.rmssdBoost).toBe(26)
    expect(withoutBonus.rmssdBoost).toBe(15)
  })
  it('bpm matches technique constant', () => {
    const r = calculateBreathworkResponse('resonance', 20)
    expect(r.bpm).toBe(5.5)
  })
  it('residualHours scales with duration', () => {
    const short  = calculateBreathworkResponse('resonance', 5)
    const long   = calculateBreathworkResponse('resonance', 30)
    expect(long.residualHours).toBeGreaterThan(short.residualHours)
  })
})
