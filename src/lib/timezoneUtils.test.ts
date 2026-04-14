import { describe, expect, it } from 'vitest'
import { fmtTimeInZone } from './timezoneUtils'

describe('fmtTimeInZone', () => {
  it('formats the same instant differently for different timezones', () => {
    const instant = new Date('2026-06-01T12:00:00Z')

    expect(fmtTimeInZone(instant, 'UTC')).not.toBe(fmtTimeInZone(instant, 'Asia/Bangkok'))
    expect(fmtTimeInZone(instant, 'UTC')).not.toBe(fmtTimeInZone(instant, 'America/Los_Angeles'))
  })
})
