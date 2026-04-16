/**
 * Generates SVG path strings for a sparkline from an array of values.
 * Uses a 0 0 W H viewBox coordinate space.
 */
export function buildSparkline(
  values: (number | null)[],
  viewW: number,
  viewH: number,
  padding = 4
): { line: string; fill: string } {
  const valid = values.filter((v): v is number => v != null)
  if (valid.length < 2) return { line: '', fill: '' }

  const min = Math.min(...valid)
  const max = Math.max(...valid)
  const range = max - min || 1
  const n = values.length
  const step = viewW / Math.max(n - 1, 1)
  const drawH = viewH - padding * 2

  const pts: [number, number][] = []
  values.forEach((v, i) => {
    if (v == null) return
    const x = i * step
    const y = padding + drawH - ((v - min) / range) * drawH
    pts.push([x, y])
  })

  if (pts.length < 2) return { line: '', fill: '' }

  const lineStr = pts
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`)
    .join(' ')
  const lastPt = pts[pts.length - 1]
  const fillStr = `${lineStr} L ${lastPt[0].toFixed(1)} ${viewH} L 0 ${viewH} Z`

  return { line: lineStr, fill: fillStr }
}

export interface SparkPoint {
  x: number
  y: number | null
  value: number | null
  date: string
  index: number
}

/**
 * Builds the full set of coordinate points for hover interaction.
 * Returns one entry per value, with null y for gaps.
 */
export function buildSparklinePoints(
  values: (number | null)[],
  dates: string[],
  viewW: number,
  viewH: number,
  padding = 4
): SparkPoint[] {
  const valid = values.filter((v): v is number => v != null)
  if (valid.length < 2) return []

  const min = Math.min(...valid)
  const max = Math.max(...valid)
  const range = max - min || 1
  const n = values.length
  const step = viewW / Math.max(n - 1, 1)
  const drawH = viewH - padding * 2

  return values.map((v, i) => ({
    x: i * step,
    y: v != null ? padding + drawH - ((v - min) / range) * drawH : null,
    value: v,
    date: dates[i] ?? '',
    index: i
  }))
}
