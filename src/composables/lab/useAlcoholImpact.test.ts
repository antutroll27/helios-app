import { describe, it, expect } from 'vitest'
import { calculateAlcoholImpact } from './useAlcoholImpact'

describe('calculateAlcoholImpact', () => {
  it('0 drinks → no HRV penalty, BAC 0, remLoss 0', () => {
    const r = calculateAlcoholImpact(0, 70, 'male', 23, 0)
    expect(r.hrvDropPct).toBe(0)
    expect(r.bac).toBe(0)
    expect(r.remLossMin).toBe(0)
  })
  it('5 drinks → -39.2% HRV drop', () => {
    const r = calculateAlcoholImpact(5, 70, 'male', 23, 0)
    expect(r.hrvDropPct).toBe(-39.2)
  })
  it('hoursToClear clamps to 0 when BAC already below 0.01', () => {
    const r = calculateAlcoholImpact(1, 80, 'male', 23, 6)
    expect(r.hoursToClear).toBe(0)
  })
  it('female has higher BAC than male same weight same drinks', () => {
    const female = calculateAlcoholImpact(3, 65, 'female', 23, 0)
    const male   = calculateAlcoholImpact(3, 65, 'male',   23, 0)
    expect(female.bac).toBeGreaterThan(male.bac)
  })
})
