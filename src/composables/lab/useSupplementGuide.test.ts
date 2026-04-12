import { describe, it, expect } from 'vitest'
import { scoreSupplements } from './useSupplementGuide'

describe('scoreSupplements', () => {

  it('low HRV (32ms) with normal sleep → Ashwagandha ranks first, score 2', () => {
    const results = scoreSupplements(32, 82, 7.5)
    expect(results[0].key).toBe('ashwagandha')
    expect(results[0].score).toBe(2)
    expect(results[0].isTopPick).toBe(true)
    const mg = results.find(s => s.key === 'magnesium')!
    expect(mg.score).toBe(0)
    const glycine = results.find(s => s.key === 'glycine')!
    expect(glycine.score).toBe(0)
  })

  it('short sleep (6.1h) + low score (68) → Magnesium ranks first, score 3; Glycine score 2', () => {
    const results = scoreSupplements(50, 68, 6.1)
    expect(results[0].key).toBe('magnesium')
    expect(results[0].score).toBe(3)
    expect(results[0].isTopPick).toBe(true)
    const glycine = results.find(s => s.key === 'glycine')!
    expect(glycine.score).toBe(2)
  })

  it('all metrics healthy → all scores 0, fallback notes, Magnesium wins tie-break', () => {
    const results = scoreSupplements(55, 88, 7.8)
    expect(results.every(s => s.score === 0)).toBe(true)
    expect(results[0].key).toBe('magnesium')
    expect(results[0].isTopPick).toBe(true)
    const mg = results.find(s => s.key === 'magnesium')!
    expect(mg.note).toBe(
      'Your sleep metrics look healthy — Mg becomes more relevant if total sleep drops below 7h or sleep score below 75'
    )
    const ashwa = results.find(s => s.key === 'ashwagandha')!
    expect(ashwa.note).toBe(
      'Your HRV is in a good range — Ashwagandha becomes more relevant if HRV drops below 40ms'
    )
    const glycine = results.find(s => s.key === 'glycine')!
    expect(glycine.note).toBe(
      'Sleep onset appears normal — consider Glycine if sleep score drops below 72 or nightly hours below 6.5h'
    )
  })

  it('all null inputs → all scores 0, no throws, all notes non-empty', () => {
    const results = scoreSupplements(null, null, null)
    expect(results.every(s => s.score === 0)).toBe(true)
    expect(results.every(s => s.note.length > 0)).toBe(true)
  })

  it('exact boundary values → all scores 0 (strict < thresholds)', () => {
    // hrv === 40, sleepScore === 75, sleepHours === 7.0 — at the boundary, not below it
    const results = scoreSupplements(40, 75, 7.0)
    expect(results.every(s => s.score === 0)).toBe(true)
  })

})
