import { describe, it, expect } from 'vitest'
import { calculateExercisePhaseShift } from './useExerciseTiming'

describe('calculateExercisePhaseShift', () => {
  it('late chronotype at 07:00 gets larger advance than early chronotype', () => {
    const late  = calculateExercisePhaseShift(7, 'late')
    const early = calculateExercisePhaseShift(7, 'early')
    expect(late.shiftMin).toBeGreaterThan(early.shiftMin)
  })
  it('evening exercise produces negative (delay) shift', () => {
    const r = calculateExercisePhaseShift(20, 'mid')
    expect(r.shiftMin).toBeLessThan(0)
  })
  it('morningMetabolicBonus true only at hour <= 10', () => {
    const morning = calculateExercisePhaseShift(8, 'mid')
    const evening = calculateExercisePhaseShift(18, 'mid')
    expect(morning.morningMetabolicBonus).toBe(true)
    expect(evening.morningMetabolicBonus).toBe(false)
  })
  it('label says "advance" for morning, "delay" for evening', () => {
    const morning = calculateExercisePhaseShift(7, 'mid')
    const evening = calculateExercisePhaseShift(20, 'mid')
    expect(morning.label).toContain('advance')
    expect(evening.label).toContain('delay')
  })
  it('late chronotype 7am: shiftMin = 90 (60 × 1.5)', () => {
    const r = calculateExercisePhaseShift(7, 'late')
    expect(r.shiftMin).toBe(90)
  })
  it('early chronotype 7am: shiftMin = 30 (60 × 0.5)', () => {
    const r = calculateExercisePhaseShift(7, 'early')
    expect(r.shiftMin).toBe(30)
  })
})
