import { describe, it, expect } from 'vitest'
import { calculateNapRecommendation } from './useNapCalc'

describe('calculateNapRecommendation', () => {
  it('recommends 26 min at 14:00 with no debt', () => {
    const r = calculateNapRecommendation({ hoursAwake: 8, sleepDebtMin: 0, currentHour: 14 })
    expect(r.duration).toBe(26)
    expect(r.nightPenalty).toBe(0)
    expect(r.inWindow).toBe(true)
  })
  it('shows night penalty after 15:00', () => {
    const r = calculateNapRecommendation({ hoursAwake: 8, sleepDebtMin: 0, currentHour: 16 })
    expect(r.nightPenalty).toBeGreaterThan(0)
  })
  it('recommends 90 min full cycle when sleepDebtMin > 60', () => {
    const r = calculateNapRecommendation({ hoursAwake: 8, sleepDebtMin: 90, currentHour: 13 })
    expect(r.duration).toBe(90)
  })
  it('sets coffeeNap true for short naps', () => {
    const r = calculateNapRecommendation({ hoursAwake: 8, sleepDebtMin: 0, currentHour: 13 })
    expect(r.coffeeNap).toBe(true)
  })
})
