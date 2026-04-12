# Protocol Intelligence Phase A+B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Protocol Intelligence section below the existing biometrics bento — 3 Phase A info cards (DLMO, caffeine cutoff, nap window) and 3 Phase B visualisations (Body Clock Dial, SRI, Sleep Debt) — all computed from the existing biometrics store.

**Architecture:** Extend `src/stores/biometrics.ts` with 6 new computed properties + a live `nowAngle` ref; build 5 new Vue components that consume them; wire the container into `BiometricsPage.vue`. No new stores, no new data sources, no backend calls.

**Tech Stack:** Vue 3 `<script setup lang="ts">`, Pinia, Vitest, hand-crafted SVG (no ECharts for this feature), `useSparkline.ts` composable already present.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/stores/biometrics.ts` | Modify | Add helpers, nowAngle ref, 6 computeds, update return block |
| `src/stores/biometrics.protocol.test.ts` | Create | Vitest tests for all new store computeds |
| `src/components/biometrics/PhaseATile.vue` | Create | Reusable Phase A info card (label / value / subtext) |
| `src/components/biometrics/BodyClockDial.vue` | Create | 24h SVG dial — arcs, dots, now-needle |
| `src/components/biometrics/SRICard.vue` | Create | SRI score + 30-day sparkline |
| `src/components/biometrics/SleepDebtCard.vue` | Create | Sleep debt value + 14-day sparkline |
| `src/components/biometrics/ProtocolIntelligenceSection.vue` | Create | Container — section header + Phase A row + Phase B row |
| `src/pages/BiometricsPage.vue` | Modify (line 66) | Import + render ProtocolIntelligenceSection below bento |

---

## Task 1 — Store helpers + Phase A computeds

**Files:**
- Modify: `src/stores/biometrics.ts` (insert after line 518, inside `defineStore` callback)
- Create: `src/stores/biometrics.protocol.test.ts`

### Step 1a — Write failing tests

- [ ] Create `src/stores/biometrics.protocol.test.ts`:

```typescript
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBiometricsStore } from './biometrics'

// Mock the solar store — it requires geolocation/SunCalc which don't work in Vitest
vi.mock('./solar', () => ({
  useSolarStore: () => ({ solarNoon: new Date('2026-04-12T12:00:00.000Z') })
}))

function makeLogs(overrides: Partial<{
  sleep_onset: string
  wake_time: string
  total_sleep_min: number
}>[] = []) {
  const defaults = {
    sleep_onset: '2026-03-14T23:00:00.000Z',  // 23:00
    wake_time:   '2026-03-15T07:00:00.000Z',  // 07:00
    total_sleep_min: 480,
    source: 'mock' as const,
  }
  return overrides.map((o, i) => ({
    ...defaults,
    ...o,
    date: `2026-03-${String(14 + i).padStart(2, '0')}`,
    deep_sleep_min: 90,
    rem_sleep_min: 110,
  }))
}

describe('Phase A computeds', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns "--:--" for dlmoEstimate when fewer than 3 nights', () => {
    store.logs = makeLogs([{}, {}])
    expect(store.dlmoEstimate).toBe('--:--')
  })

  it('computes dlmoEstimate as avg sleep onset minus 2 hours', () => {
    // avg sleep onset = 23:00 → DLMO = 21:00
    store.logs = makeLogs([{}, {}, {}])
    expect(store.dlmoEstimate).toBe('21:00')
  })

  it('computes caffeineCutoff as avg sleep onset minus 6 hours', () => {
    // avg sleep onset = 23:00 → cutoff = 17:00
    store.logs = makeLogs([{}, {}, {}])
    expect(store.caffeineCutoff).toBe('17:00')
  })

  it('computes napWindow as avg wake time plus 7 hours', () => {
    // avg wake = 07:00 → nap = 14:00
    store.logs = makeLogs([{}, {}, {}])
    expect(store.napWindow).toBe('14:00')
  })

  it('wraps napWindow correctly for late chronotypes', () => {
    // avg wake = 10:00 → nap = 17:00
    const logs = makeLogs([
      { wake_time: '2026-03-15T10:00:00.000Z' },
      { wake_time: '2026-03-16T10:00:00.000Z' },
      { wake_time: '2026-03-17T10:00:00.000Z' },
    ])
    store.logs = logs
    expect(store.napWindow).toBe('17:00')
  })
})

describe('Phase B — sri', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns null when fewer than 7 nights', () => {
    store.logs = makeLogs(Array(6).fill({}))
    expect(store.sri).toBeNull()
  })

  it('returns 100 for perfectly regular sleep (zero deviation)', () => {
    // All nights identical onset/wake → MAD = 0
    store.logs = makeLogs(Array(7).fill({}))
    expect(store.sri).toBe(100)
  })

  it('returns lower SRI when midpoints vary significantly', () => {
    // Mix of early and late midpoints
    const logs = makeLogs([
      { sleep_onset: '2026-03-14T22:00:00.000Z', wake_time: '2026-03-15T06:00:00.000Z' },
      { sleep_onset: '2026-03-15T00:00:00.000Z', wake_time: '2026-03-16T08:00:00.000Z' },
      { sleep_onset: '2026-03-16T22:00:00.000Z', wake_time: '2026-03-17T06:00:00.000Z' },
      { sleep_onset: '2026-03-17T00:00:00.000Z', wake_time: '2026-03-18T08:00:00.000Z' },
      { sleep_onset: '2026-03-18T22:00:00.000Z', wake_time: '2026-03-19T06:00:00.000Z' },
      { sleep_onset: '2026-03-19T00:00:00.000Z', wake_time: '2026-03-20T08:00:00.000Z' },
      { sleep_onset: '2026-03-20T22:00:00.000Z', wake_time: '2026-03-21T06:00:00.000Z' },
    ])
    store.logs = logs
    expect(store.sri).toBeLessThan(100)
    expect(store.sri).toBeGreaterThanOrEqual(0)
  })
})

describe('Phase B — sleepDebtMin', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns negative debt when sleeping less than 480 min/night', () => {
    // 14 nights × (400 - 480) = -1120 min
    store.logs = makeLogs(Array(14).fill({ total_sleep_min: 400 }))
    expect(store.sleepDebtMin).toBe(-1120)
  })

  it('returns positive surplus when sleeping more than 480 min/night', () => {
    store.logs = makeLogs(Array(14).fill({ total_sleep_min: 500 }))
    expect(store.sleepDebtMin).toBe(280)
  })

  it('uses raw logs (last 14), not windowedLogs — unaffected by dateRange toggle', () => {
    // 20 logs total. dateRange is 7 by default.
    // Debt should use last 14 logs, not last 7.
    store.logs = makeLogs([
      ...Array(6).fill({ total_sleep_min: 600 }),  // surplus nights (not in last 14)
      ...Array(14).fill({ total_sleep_min: 400 }),  // deficit nights (in last 14)
    ])
    // 14 × (400 - 480) = -1120
    expect(store.sleepDebtMin).toBe(-1120)
  })
})

describe('Phase B — sleepDebtSeries', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns per-night deviation from 480 min target', () => {
    store.logs = makeLogs([
      { total_sleep_min: 480 },  // 0 deviation
      { total_sleep_min: 420 },  // -60
      { total_sleep_min: 510 },  // +30
    ])
    const vals = store.sleepDebtSeries.map(s => s.value)
    expect(vals).toEqual([0, -60, 30])
  })
})

describe('Phase B — sriSeries', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns null for entries where fewer than 7 nights are in the window', () => {
    store.logs = makeLogs(Array(10).fill({}))
    const series = store.sriSeries
    // First 6 entries (indices 0-5) have windows of size 1-6 → null
    expect(series[0].value).toBeNull()
    expect(series[5].value).toBeNull()
    // Entry at index 6 has a 7-night window → should have a value
    expect(series[6].value).not.toBeNull()
  })

  it('returns 100 for perfectly regular sleep', () => {
    // All identical → MAD = 0 → SRI = 100
    store.logs = makeLogs(Array(10).fill({}))
    const series = store.sriSeries
    const withValues = series.filter(s => s.value !== null)
    withValues.forEach(s => expect(s.value).toBe(100))
  })
})

describe('Phase B — dialData', () => {
  let store: ReturnType<typeof useBiometricsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBiometricsStore()
  })

  it('returns null when fewer than 3 nights', () => {
    store.logs = makeLogs([{}, {}])
    expect(store.dialData).toBeNull()
  })

  it('returns non-null dial data with 3+ nights', () => {
    store.logs = makeLogs([{}, {}, {}])
    expect(store.dialData).not.toBeNull()
  })

  it('sleep window start angle = (avgOnsetMinutes / 1440) * 360', () => {
    // avg onset = 23:00 = 1380 min → angle = (1380/1440)*360 = 345°
    store.logs = makeLogs([{}, {}, {}])
    expect(store.dialData!.sleepWindowStart).toBeCloseTo(345, 0)
  })

  it('uses solar noon fallback (720 min = 180°) when solarNoon unavailable', () => {
    // The mock returns solarNoon = 12:00 UTC = 720 min → angle = 180°
    store.logs = makeLogs([{}, {}, {}])
    expect(store.dialData!.solarNoonAngle).toBeCloseTo(180, 0)
  })
})
```

- [ ] Run tests to verify they fail (store properties don't exist yet):
```bash
cd helios-app && npx vitest run src/stores/biometrics.protocol.test.ts
```
Expected: Multiple failures — `store.dlmoEstimate is not a function` or `undefined`

### Step 1b — Add helpers + Phase A computeds to store

- [ ] In `src/stores/biometrics.ts`, find the line after `const dataSource = ref<'mock' | 'uploaded'>('mock')` (line 523). Add the import for solar store and all helpers **before** the first computed:

```typescript
import { useSolarStore } from './solar'
```
Add at top of file with other imports (line 2, after `import { ref, computed } from 'vue'`).

- [ ] Insert after line 523 (`const dataSource = ref...`), inside the `defineStore` callback:

```typescript
  // ---------------------------------------------------------------------------
  // Helpers (store-scoped, not exported)
  // ---------------------------------------------------------------------------

  // Parses "HH:MM" or ISO datetime ("2026-03-14T23:10:00.000Z") → minutes since midnight
  function timeToMinutes(s: string): number {
    const hhmm = s.length > 5 ? s.slice(11, 16) : s
    const [h, m] = hhmm.split(':').map(Number)
    return h * 60 + m
  }

  // Minutes since midnight → "HH:MM", wraps at 1440
  function minutesToTime(min: number): string {
    const wrapped = ((min % 1440) + 1440) % 1440
    const h = Math.floor(wrapped / 60).toString().padStart(2, '0')
    const m = Math.floor(wrapped % 60).toString().padStart(2, '0')
    return `${h}:${m}`
  }

  function helperAvg(nums: number[]): number {
    return nums.reduce((a, b) => a + b, 0) / nums.length
  }

  // ---------------------------------------------------------------------------
  // Live now-angle (updates every 60s for the body clock dial needle)
  // ---------------------------------------------------------------------------
  const nowAngle = ref<number>(
    ((new Date().getHours() * 60 + new Date().getMinutes()) / 1440) * 360
  )
  // Keep the handle so Vitest tests can call clearInterval(_nowTimer) to avoid leaks
  const _nowTimer = setInterval(() => {
    nowAngle.value = ((new Date().getHours() * 60 + new Date().getMinutes()) / 1440) * 360
  }, 60_000)

  // Instantiate solar store at setup level (not inside computed) for testability
  const solarStore = useSolarStore()

  // ---------------------------------------------------------------------------
  // Phase A — scalar circadian timing computeds
  // ---------------------------------------------------------------------------

  // DLMO estimate: avg sleep onset − 2h (Czeisler & Gooley 2007)
  const dlmoEstimate = computed<string>(() => {
    const valid = logs.value.filter(l => l.sleep_onset)
    if (valid.length < 3) return '--:--'
    const avgOnsetMin = helperAvg(valid.map(l => timeToMinutes(l.sleep_onset)))
    return minutesToTime(avgOnsetMin - 120)
  })

  // Caffeine cutoff: avg sleep onset − 6h (Drake et al. 2013)
  const caffeineCutoff = computed<string>(() => {
    const valid = logs.value.filter(l => l.sleep_onset)
    if (valid.length < 3) return '--:--'
    const avgOnsetMin = helperAvg(valid.map(l => timeToMinutes(l.sleep_onset)))
    return minutesToTime(avgOnsetMin - 360)
  })

  // Nap window: avg wake time + 7h (Dinges 1992 post-lunch dip)
  const napWindow = computed<string>(() => {
    const valid = logs.value.filter(l => l.wake_time)
    if (valid.length < 3) return '--:--'
    const avgWakeMin = helperAvg(valid.map(l => timeToMinutes(l.wake_time)))
    return minutesToTime(avgWakeMin + 420)
  })
```

- [ ] Run tests again — Phase A tests should now pass:
```bash
npx vitest run src/stores/biometrics.protocol.test.ts
```
Expected: Phase A tests PASS, Phase B tests still FAIL

### Step 1c — Commit

- [ ] Commit:
```bash
git add src/stores/biometrics.ts src/stores/biometrics.protocol.test.ts
git commit -m "feat(biometrics): add Phase A store computeds + helpers (DLMO, caffeine, nap)"
```

---

## Task 2 — Phase B computeds (SRI, Sleep Debt, Dial)

**Files:**
- Modify: `src/stores/biometrics.ts` (continue after Phase A computeds)
- Modify: `src/stores/biometrics.protocol.test.ts` (all tests already written in Task 1)

### Step 2a — Add Phase B computeds

- [ ] Append after the Phase A computed block (after `napWindow`):

```typescript
  // ---------------------------------------------------------------------------
  // Phase B — Sleep Regularity Index (adapted from Windred et al. 2024)
  // ---------------------------------------------------------------------------

  // SRI scalar: 0–100. Null if fewer than 7 nights.
  const sri = computed<number | null>(() => {
    const valid = logs.value.filter(l => l.sleep_onset && l.wake_time)
    if (valid.length < 7) return null
    const midpoints = valid.map(l => (timeToMinutes(l.sleep_onset) + timeToMinutes(l.wake_time)) / 2)
    const meanMid = helperAvg(midpoints)
    const mad = helperAvg(midpoints.map(m => Math.abs(m - meanMid)))
    return Math.max(0, Math.round(100 - (mad / 120) * 100))
  })

  // SRI 30-day series — sliding 7-night window, one value per day
  const sriSeries = computed<{ date: string; value: number | null }[]>(() => {
    const all = logs.value.filter(l => l.sleep_onset && l.wake_time)
    const startIdx = Math.max(0, all.length - 30)
    const last30 = all.slice(startIdx)
    return last30.map((entry, i) => {
      const absIdx = startIdx + i
      const window = all.slice(Math.max(0, absIdx - 6), absIdx + 1)
      if (window.length < 7) return { date: entry.date, value: null }
      const midpoints = window.map(l => (timeToMinutes(l.sleep_onset) + timeToMinutes(l.wake_time)) / 2)
      const meanMid = helperAvg(midpoints)
      const mad = helperAvg(midpoints.map(m => Math.abs(m - meanMid)))
      return { date: entry.date, value: Math.max(0, Math.round(100 - (mad / 120) * 100)) }
    })
  })

  // ---------------------------------------------------------------------------
  // Phase B — Sleep Debt (rolling 14-day, always uses raw logs not windowedLogs)
  // ---------------------------------------------------------------------------

  const SLEEP_TARGET_MIN = 480  // 8 hours

  // Total accumulated debt over the last 14 nights (positive = surplus, negative = deficit)
  const sleepDebtMin = computed<number>(() => {
    return logs.value.slice(-14).reduce((acc, l) => acc + (l.total_sleep_min - SLEEP_TARGET_MIN), 0)
  })

  // Per-night deviation series for sparkline
  const sleepDebtSeries = computed<{ date: string; value: number }[]>(() => {
    return logs.value.slice(-14).map(l => ({
      date: l.date,
      value: l.total_sleep_min - SLEEP_TARGET_MIN
    }))
  })

  // ---------------------------------------------------------------------------
  // Phase B — Body Clock Dial data
  // ---------------------------------------------------------------------------

  interface DialData {
    sleepWindowStart: number
    sleepWindowEnd:   number
    peakAlertStart:   number
    peakAlertEnd:     number
    dlmoAngle:        number
    solarNoonAngle:   number
  }

  const dialData = computed<DialData | null>(() => {
    if (dlmoEstimate.value === '--:--') return null
    const validOnset = logs.value.filter(l => l.sleep_onset)
    const validWake  = logs.value.filter(l => l.wake_time)
    if (validOnset.length < 3 || validWake.length < 3) return null

    const toAngle = (min: number) => (min / 1440) * 360
    const avgOnsetMin = helperAvg(validOnset.map(l => timeToMinutes(l.sleep_onset)))
    const avgWakeMin  = helperAvg(validWake.map(l => timeToMinutes(l.wake_time)))

    const solarNoonDate = solarStore.solarNoon
    const solarNoonMin  = solarNoonDate instanceof Date
      ? solarNoonDate.getHours() * 60 + solarNoonDate.getMinutes()
      : 720  // fallback: noon

    return {
      sleepWindowStart: toAngle(avgOnsetMin),
      sleepWindowEnd:   toAngle(avgWakeMin),
      peakAlertStart:   toAngle(avgWakeMin + 120),
      peakAlertEnd:     toAngle(avgWakeMin + 600),
      dlmoAngle:        toAngle(timeToMinutes(dlmoEstimate.value)),
      solarNoonAngle:   toAngle(solarNoonMin),
    }
  })
```

### Step 2b — Update return block

- [ ] In `src/stores/biometrics.ts`, find the `return {` block (line 754) and add the new exports:

```typescript
  return {
    logs, dateRange, uploadStatus, uploadError, dataSource,
    windowedLogs, hrvSeries, kpOverlaySeries, sleepArchitectureSeries,
    sleepScoreSeries, restingHRSeries, skinTempSeries,
    avgHRV, avgSleepScore, avgRestingHR, avgTotalSleepH,
    protocolAdherence, avgAdherencePct, insights,
    // Phase A
    dlmoEstimate, caffeineCutoff, napWindow,
    // Phase B
    sri, sriSeries, sleepDebtMin, sleepDebtSeries, dialData, nowAngle,
    setDateRange, loadMockData, ingestParsedLogs, setUploadStatus
  }
```

### Step 2c — Run all tests

- [ ] Run full test suite:
```bash
npx vitest run src/stores/biometrics.protocol.test.ts
```
Expected: All tests PASS

- [ ] Also run full project tests to check nothing broke:
```bash
npm test
```
Expected: All existing tests still pass

### Step 2d — Commit

- [ ] Commit:
```bash
git add src/stores/biometrics.ts
git commit -m "feat(biometrics): add Phase B store computeds (SRI, sleep debt, dial data)"
```

---

## Task 3 — PhaseATile.vue

**Files:**
- Create: `src/components/biometrics/PhaseATile.vue`

No test file — pure presentational component with no logic.

### Step 3a — Create component

- [ ] Create `src/components/biometrics/PhaseATile.vue`:

```vue
<script setup lang="ts">
defineProps<{
  label: string
  value: string
  subtext: string
  accent: string
}>()
</script>

<template>
  <div class="phase-a-tile bento-card" :style="{ '--tile-accent': accent }">
    <div class="phase-a-tile__label">{{ label }}</div>
    <div class="phase-a-tile__value">{{ value }}</div>
    <div class="phase-a-tile__sub">{{ subtext }}</div>
  </div>
</template>

<style scoped>
.phase-a-tile {
  padding: 1rem 1.1rem;
  border-left: 2.5px solid var(--tile-accent);
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.phase-a-tile__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;           /* text-xs2 */
  letter-spacing: 0.1em;
  color: var(--tile-accent);
  font-weight: 700;
  text-transform: uppercase;
}

.phase-a-tile__value {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  line-height: 1;
  margin: 0.15rem 0;
}

.phase-a-tile__sub {
  font-size: 0.5rem;            /* text-xs2 */
  color: var(--text-muted);
  line-height: 1.4;
}
</style>
```

### Step 3b — Manual visual check

- [ ] Run dev server: `npm run dev`
- [ ] Temporarily add to `BiometricsPage.vue` inside the `v-if` block to verify rendering:
```html
<PhaseATile label="MELATONIN ONSET" value="21:30" subtext="dim lights 1h before" accent="#00D4AA" />
```
- [ ] Confirm: label in teal monospace, large value, muted subtext, left accent stripe visible
- [ ] Remove the temporary usage (will be added properly in Task 7)

### Step 3c — Commit

- [ ] Commit:
```bash
git add src/components/biometrics/PhaseATile.vue
git commit -m "feat(biometrics): add PhaseATile component"
```

---

## Task 4 — BodyClockDial.vue

**Files:**
- Create: `src/components/biometrics/BodyClockDial.vue`

### Step 4a — Create component

- [ ] Create `src/components/biometrics/BodyClockDial.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue'

interface DialData {
  sleepWindowStart: number
  sleepWindowEnd:   number
  peakAlertStart:   number
  peakAlertEnd:     number
  dlmoAngle:        number
  solarNoonAngle:   number
}

const props = defineProps<{
  data: DialData | null
  nowAngle: number
}>()

const CX = 100
const CY = 100
const R  = 88
const CIRC = 2 * Math.PI * R  // ≈ 552.9

// Convert degrees (0=midnight, clockwise) to SVG (x, y) at given radius
function angleToXY(deg: number, r: number) {
  const rad = ((deg - 90) * Math.PI) / 180
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) }
}

// stroke-dasharray / stroke-dashoffset for an arc from angleStart to angleEnd
function arcDash(angleStart: number, angleEnd: number) {
  const delta   = ((angleEnd - angleStart + 360) % 360)
  const dashLen = (delta / 360) * CIRC
  const offset  = CIRC - (angleStart / 360) * CIRC + CIRC * 0.25
  return {
    strokeDasharray:  `${dashLen} ${CIRC - dashLen}`,
    strokeDashoffset: offset,
  }
}

const sleepArc    = computed(() => props.data ? arcDash(props.data.sleepWindowStart, props.data.sleepWindowEnd) : null)
const peakArc     = computed(() => props.data ? arcDash(props.data.peakAlertStart,  props.data.peakAlertEnd)   : null)
const dlmoDot     = computed(() => props.data ? angleToXY(props.data.dlmoAngle, R)     : null)
const solarDot    = computed(() => props.data ? angleToXY(props.data.solarNoonAngle, R) : null)
const nowNeedle   = computed(() => angleToXY(props.nowAngle, 72))

// Hour labels at 00/06/12/18
const hourLabels = [
  { label: '00', ...angleToXY(0,   R + 12) },
  { label: '06', ...angleToXY(90,  R + 12) },
  { label: '12', ...angleToXY(180, R + 12) },
  { label: '18', ...angleToXY(270, R + 12) },
]
</script>

<template>
  <div class="body-clock-dial bento-card">
    <div class="body-clock-dial__header">
      <span class="body-clock-dial__label">BODY CLOCK</span>
      <span class="body-clock-dial__sub">24h circadian phase</span>
    </div>

    <div class="body-clock-dial__svg-wrap">
      <svg viewBox="0 0 200 200" class="body-clock-dial__svg" aria-label="24-hour body clock dial">

        <!-- Track ring -->
        <circle :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="rgba(255,246,233,0.06)" stroke-width="14" />

        <!-- Sleep window arc (violet) -->
        <circle v-if="sleepArc" :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="#9B8BFA" stroke-width="14" opacity="0.5"
          :stroke-dasharray="sleepArc.strokeDasharray"
          :stroke-dashoffset="sleepArc.strokeDashoffset"
          stroke-linecap="round">
          <title>Sleep window</title>
        </circle>

        <!-- Peak alertness arc (teal, thinner) -->
        <circle v-if="peakArc" :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="#00D4AA" stroke-width="8" opacity="0.45"
          :stroke-dasharray="peakArc.strokeDasharray"
          :stroke-dashoffset="peakArc.strokeDashoffset"
          stroke-linecap="round">
          <title>Peak alertness window</title>
        </circle>

        <!-- Solar noon dot -->
        <circle v-if="solarDot"
          :cx="solarDot.x" :cy="solarDot.y" r="4"
          fill="#FFBD76" opacity="0.5">
          <title>Solar noon</title>
        </circle>

        <!-- DLMO dot -->
        <circle v-if="dlmoDot"
          :cx="dlmoDot.x" :cy="dlmoDot.y" r="5"
          fill="#9B8BFA" stroke="#FFF6E9" stroke-width="1.5">
          <title>DLMO (melatonin onset)</title>
        </circle>

        <!-- Hour labels -->
        <text v-for="h in hourLabels" :key="h.label"
          :x="h.x" :y="h.y"
          text-anchor="middle" dominant-baseline="middle"
          fill="rgba(255,246,233,0.3)"
          font-size="9"
          font-family="'Geist Mono', monospace">
          {{ h.label }}
        </text>

        <!-- Now needle -->
        <line :x1="CX" :y1="CY" :x2="nowNeedle.x" :y2="nowNeedle.y"
          stroke="rgba(255,246,233,0.85)" stroke-width="1.5" stroke-linecap="round" />

        <!-- Centre dot -->
        <circle :cx="CX" :cy="CY" r="3.5" fill="#FFF6E9" />

        <!-- Empty state -->
        <text v-if="!data"
          x="100" y="105"
          text-anchor="middle" fill="rgba(255,246,233,0.2)"
          font-size="18" font-family="'Geist Mono', monospace">
          –
        </text>
      </svg>
    </div>

    <!-- Legend -->
    <div v-if="data" class="body-clock-dial__legend">
      <span class="legend-item legend-item--violet">Sleep</span>
      <span class="legend-item legend-item--teal">Peak</span>
      <span class="legend-item legend-item--nectarine">Solar noon</span>
    </div>
  </div>
</template>

<style scoped>
.body-clock-dial {
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.body-clock-dial__header {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.body-clock-dial__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.body-clock-dial__sub {
  font-size: 0.5rem;
  color: var(--text-muted);
}

.body-clock-dial__svg-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
}

.body-clock-dial__svg {
  width: 100%;
  max-width: 180px;
  height: auto;
}

.body-clock-dial__legend {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
}

.legend-item {
  font-family: 'Geist Mono', monospace;
  font-size: 0.45rem;
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.legend-item::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 3px;
  border-radius: 2px;
}

.legend-item--violet::before  { background: #9B8BFA; }
.legend-item--teal::before    { background: #00D4AA; }
.legend-item--nectarine::before { background: #FFBD76; }
</style>
```

### Step 4b — Manual visual check

- [ ] Temporarily import and render `BodyClockDial` in `BiometricsPage.vue` with mock data:
```html
<BodyClockDial :data="biometrics.dialData" :now-angle="biometrics.nowAngle" />
```
- [ ] Confirm: violet sleep arc, teal peak arc, DLMO dot, solar noon dot, now needle all visible
- [ ] Confirm needle points to the correct time quadrant (check against your system clock)
- [ ] Remove temporary usage

### Step 4c — Commit

- [ ] Commit:
```bash
git add src/components/biometrics/BodyClockDial.vue
git commit -m "feat(biometrics): add BodyClockDial SVG component"
```

---

## Task 5 — SRICard.vue

**Files:**
- Create: `src/components/biometrics/SRICard.vue`

### Step 5a — Create component

- [ ] Create `src/components/biometrics/SRICard.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { buildSparkline } from '@/composables/useSparkline'

const props = defineProps<{
  score: number | null
  series: { date: string; value: number | null }[]
}>()

// buildSparkline returns { line: string; fill: string } — SVG path strings
const sparklinePath = computed(() => {
  const values = props.series.map(s => s.value)
  return buildSparkline(values, 160, 28).line
})

const hasEnoughData = computed(() => props.score !== null)
</script>

<template>
  <div class="sri-card bento-card">
    <div class="sri-card__label">SLEEP REGULARITY INDEX</div>

    <div class="sri-card__score">
      <span class="sri-card__number">{{ score ?? '--' }}</span>
      <span class="sri-card__denom">/ 100</span>
    </div>

    <svg v-if="hasEnoughData"
      class="sri-card__spark"
      viewBox="0 0 160 28"
      preserveAspectRatio="none"
      aria-hidden="true">
      <path
        :d="sparklinePath"
        fill="none"
        stroke="#00D4AA"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        opacity="0.8"
      />
    </svg>

    <div v-if="!hasEnoughData" class="sri-card__empty">Need 7+ nights</div>

    <div class="sri-card__citation">adapted · Windred et al. 2024</div>
  </div>
</template>

<style scoped>
.sri-card {
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.sri-card__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.sri-card__score {
  display: flex;
  align-items: baseline;
  gap: 0.2rem;
  margin: 0.2rem 0;
}

.sri-card__number {
  font-size: 1.6rem;
  font-weight: 800;
  color: #00D4AA;
  letter-spacing: -0.02em;
  line-height: 1;
}

.sri-card__denom {
  font-size: 0.5rem;
  color: var(--text-muted);
}

.sri-card__spark {
  width: 100%;
  height: 28px;
  display: block;
  margin-top: 0.2rem;
}

.sri-card__empty {
  font-size: 0.5rem;
  color: var(--text-muted);
  font-style: italic;
}

.sri-card__citation {
  font-size: 0.45rem;
  color: var(--text-muted);
  font-style: italic;
  margin-top: 0.1rem;
}
</style>
```

### Step 5b — Commit

- [ ] Commit:
```bash
git add src/components/biometrics/SRICard.vue
git commit -m "feat(biometrics): add SRICard component"
```

---

## Task 6 — SleepDebtCard.vue

**Files:**
- Create: `src/components/biometrics/SleepDebtCard.vue`

### Step 6a — Create component

- [ ] Create `src/components/biometrics/SleepDebtCard.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { buildSparkline } from '@/composables/useSparkline'

const props = defineProps<{
  debtMin: number
  series: { date: string; value: number }[]
}>()

// Accent colour based on deficit threshold
const accent = computed(() => {
  if (props.debtMin > 0)    return '#00D4AA'   // surplus — Calm
  if (props.debtMin > -60)  return '#FFBD76'   // minor deficit — Nectarine
  return '#FF4444'                              // major deficit (≥60 min) — Storm
})

const displayValue = computed(() => {
  const abs = Math.abs(props.debtMin)
  const h = Math.floor(abs / 60)
  const m = abs % 60
  const sign = props.debtMin >= 0 ? '+' : '−'
  return h > 0 ? `${sign}${h}h ${m}m` : `${sign}${m} min`
})

// Zero-line position in the 28px viewBox
const SPARK_H = 28
const values  = computed(() => props.series.map(s => s.value))
// buildSparkline returns { line: string; fill: string } — use .line for <path d="...">
const sparklinePath = computed(() => buildSparkline(values.value, 160, SPARK_H).line)

// Compute zero-line Y position based on value range
const zeroY = computed(() => {
  const vals = values.value
  if (!vals.length) return SPARK_H / 2
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const range = max - min
  if (range === 0) return SPARK_H / 2
  return SPARK_H - ((0 - min) / range) * SPARK_H
})
</script>

<template>
  <div class="debt-card bento-card">
    <div class="debt-card__label">SLEEP DEBT · 14-DAY</div>

    <div class="debt-card__value" :style="{ color: accent }">
      {{ displayValue }}
    </div>

    <svg class="debt-card__spark"
      viewBox="0 0 160 28"
      preserveAspectRatio="none"
      aria-hidden="true">
      <!-- Zero line -->
      <line x1="0" :y1="zeroY" x2="160" :y2="zeroY"
        stroke="rgba(255,246,233,0.1)" stroke-width="0.5" stroke-dasharray="3 3" />
      <!-- Debt sparkline -->
      <path
        :d="sparklinePath"
        fill="none"
        :stroke="accent"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        opacity="0.75"
      />
    </svg>
  </div>
</template>

<style scoped>
.debt-card {
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.debt-card__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.debt-card__value {
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1;
  margin: 0.2rem 0;
}

.debt-card__spark {
  width: 100%;
  height: 28px;
  display: block;
  margin-top: 0.2rem;
}
</style>
```

### Step 6b — Commit

- [ ] Commit:
```bash
git add src/components/biometrics/SleepDebtCard.vue
git commit -m "feat(biometrics): add SleepDebtCard component"
```

---

## Task 7 — ProtocolIntelligenceSection.vue

**Files:**
- Create: `src/components/biometrics/ProtocolIntelligenceSection.vue`

### Step 7a — Create container component

- [ ] Create `src/components/biometrics/ProtocolIntelligenceSection.vue`:

```vue
<script setup lang="ts">
import { useBiometricsStore } from '@/stores/biometrics'
import PhaseATile from './PhaseATile.vue'
import BodyClockDial from './BodyClockDial.vue'
import SRICard from './SRICard.vue'
import SleepDebtCard from './SleepDebtCard.vue'

const store = useBiometricsStore()
</script>

<template>
  <section class="proto-intel">
    <header class="proto-intel__header">
      <span class="proto-intel__title">PROTOCOL INTELLIGENCE</span>
      <span class="proto-intel__sub">Derived from your sleep patterns</span>
    </header>

    <!-- Phase A: 3 info tiles -->
    <div class="proto-intel__phase-a">
      <PhaseATile
        label="MELATONIN ONSET"
        :value="store.dlmoEstimate"
        subtext="dim lights 1h before"
        accent="#00D4AA"
      />
      <PhaseATile
        label="CAFFEINE CUTOFF"
        :value="store.caffeineCutoff"
        subtext="last coffee by this time"
        accent="#FFBD76"
      />
      <PhaseATile
        label="OPTIMAL NAP"
        :value="store.napWindow"
        subtext="26 min · NASA protocol"
        accent="var(--text-muted)"
      />
    </div>

    <!-- Phase B: Dial + SRI + Debt -->
    <div class="proto-intel__phase-b">
      <BodyClockDial
        :data="store.dialData"
        :now-angle="store.nowAngle"
      />
      <SRICard
        :score="store.sri"
        :series="store.sriSeries"
      />
      <SleepDebtCard
        :debt-min="store.sleepDebtMin"
        :series="store.sleepDebtSeries"
      />
    </div>
  </section>
</template>

<style scoped>
.proto-intel {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.proto-intel__header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--border-card);
}

.proto-intel__title {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.15em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.proto-intel__sub {
  font-size: 0.5rem;
  color: var(--text-muted);
}

.proto-intel__phase-a {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.proto-intel__phase-b {
  display: grid;
  grid-template-columns: 1.6fr 1fr 1fr;
  gap: 0.75rem;
  align-items: start;
}

@media (max-width: 640px) {
  .proto-intel__phase-a {
    grid-template-columns: 1fr;
  }
  .proto-intel__phase-b {
    grid-template-columns: 1fr;
  }
}
</style>
```

### Step 7b — Commit

- [ ] Commit:
```bash
git add src/components/biometrics/ProtocolIntelligenceSection.vue
git commit -m "feat(biometrics): add ProtocolIntelligenceSection container"
```

---

## Task 8 — Integration into BiometricsPage.vue

**Files:**
- Modify: `src/pages/BiometricsPage.vue`

### Step 8a — Add import and template tag

- [ ] In `src/pages/BiometricsPage.vue`, add the import after line 14 (after `BiometricsEmptyState` import):

```typescript
import ProtocolIntelligenceSection from '@/components/biometrics/ProtocolIntelligenceSection.vue'
```

- [ ] In the template, add `<ProtocolIntelligenceSection />` after the closing `</div>` of the `.bento` grid (after line 66, still inside the `v-if="biometrics.logs.length > 0"` block):

The `v-if` block in `BiometricsPage.vue` currently looks like:
```html
<div v-if="biometrics.logs.length > 0" class="bento mt-4">
  ...bento content...
</div>

<BiometricsEmptyState v-else ... />
```

Wrap both the bento and Protocol Intelligence in a single `v-if` fragment:
```html
<template v-if="biometrics.logs.length > 0">
  <div class="bento mt-4">
    ...existing bento content unchanged...
  </div>
  <ProtocolIntelligenceSection />
</template>

<BiometricsEmptyState v-else class="mt-4" @upload-click="triggerFileInput" />
```

### Step 8b — End-to-end visual verification

- [ ] Run dev server: `npm run dev`
- [ ] Navigate to `/biometrics`
- [ ] Verify Phase A row: 3 tiles visible with correct computed times (DLMO, caffeine cutoff, nap)
- [ ] Verify DLMO tile value = caffeine tile value + 4h (both derived from sleep onset)
- [ ] Verify Phase B row: dial renders, SRI score shows (should be ~high given consistent mock data), debt card shows value
- [ ] Toggle 7d/30d — Phase A tiles update (they use `logs.value` not `windowedLogs`, but avg changes); sleep debt does NOT change
- [ ] Verify now-needle points to the correct time quadrant for current time
- [ ] Resize to 640px — both rows stack to single column
- [ ] Open browser console — zero errors

### Step 8c — Run full test suite

- [ ] Run all tests:
```bash
npm test
```
Expected: All pass

### Step 8d — Final commit + push

- [ ] Commit:
```bash
git add src/pages/BiometricsPage.vue
git commit -m "feat(biometrics): wire ProtocolIntelligenceSection into BiometricsPage"
```

- [ ] Push:
```bash
git push origin dev
```

---

## Verification Checklist

Before marking complete, confirm all spec verification steps pass:

- [ ] 1. No console errors on `/biometrics`
- [ ] 2. `dlmoEstimate` = avg sleep onset − 2h (spot-check against mock data: onset ~23:00 → DLMO ~21:00)
- [ ] 3. `caffeineCutoff` = avg sleep onset − 6h (~17:00)
- [ ] 4. `napWindow` = avg wake time + 7h (wake ~07:00 → nap ~14:00)
- [ ] 5. All three tiles show `--:--` when `logs.length < 3` (test by temporarily clearing `logs` in Vue devtools)
- [ ] 6. Sleep window arc is violet, peak alertness arc is teal
- [ ] 7. Now needle matches current time
- [ ] 8. SRI shows null state with "Need 7+ nights" message when data < 7 nights
- [ ] 9. Sleep debt accent: teal for surplus, nectarine for 0–59 min deficit, red for ≥60 min
- [ ] 10. `sleepDebtMin` unchanged when toggling 7d/30d
- [ ] 11. Mobile at 640px: single-column layout, all visible
