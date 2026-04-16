import { describe, it, expect } from 'vitest'
import { calculateMealWindow } from './useMealWindow'

describe('calculateMealWindow', () => {
  it('08:00 → 14:00, sleep 22:00 → valid, high score, earlyTRF true', () => {
    const r = calculateMealWindow(8, 14, 22)
    expect(r.valid).toBe(true)
    if (!r.valid) return
    expect(r.earlyTRF).toBe(true)
    expect(r.score).toBeGreaterThanOrEqual(80)
  })
  it('overnight window (20→8) → invalid', () => {
    const r = calculateMealWindow(20, 8, 23)
    expect(r.valid).toBe(false)
  })
  it('last meal after sleep time → invalid sleep order', () => {
    const r = calculateMealWindow(8, 21.5, 21)
    expect(r.valid).toBe(false)
  })
  it('equal last meal and sleep time → invalid', () => {
    const r = calculateMealWindow(8, 22, 22)
    expect(r.valid).toBe(false)
  })
  it('windowHours > 10 → no glucoseBenefit', () => {
    const r = calculateMealWindow(7, 20, 23)
    expect(r.valid).toBe(true)
    if (!r.valid) return
    expect(r.glucoseBenefit).toBeNull()
  })
})
