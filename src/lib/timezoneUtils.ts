/**
 * Returns the UTC offset in hours for a given IANA timezone at a given instant.
 * Uses Intl.DateTimeFormat.formatToParts to read local time parts and computes
 * the offset vs UTC, handling DST automatically.
 * Result is rounded to the nearest quarter-hour to avoid floating-point noise.
 */
export function getTimezoneOffsetHours(timeZone: string, date: Date): number {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(date)

  const pick = (type: string) => Number(parts.find((p) => p.type === type)?.value ?? 0)

  const localMs = Date.UTC(
    pick('year'),
    pick('month') - 1,
    pick('day'),
    pick('hour'),
    pick('minute'),
    pick('second'),
  )

  return Math.round(((localMs - date.getTime()) / 3_600_000) * 4) / 4
}

/**
 * Formats a Date as a locale time string (HH:MM, 2-digit hour and minute).
 * Uses the system locale (no explicit locale string) for consistency across the codebase.
 */
export function fmtTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
