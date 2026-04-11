# Protocol Intelligence Section — Design Spec
**Date:** 2026-04-12
**Phases:** A (Quick Wins) + B (New Visualisations)
**Status:** Approved

---

## Overview

Add a "Protocol Intelligence" section directly below the existing biometrics bento grid on `/biometrics`. No tabs, no separate page — same scroll, same surface language. The section surfaces three scientifically-grounded Phase A cards (DLMO estimate, caffeine cutoff, nap window) and three Phase B visualisations (Body Clock Dial, Sleep Regularity Index, Sleep Debt), all computed from data already in the biometrics store.

---

## Scope

### In scope
- Phase A: DLMO estimate card, caffeine cutoff card, nap window card
- Phase B: Body Clock Dial (SVG), SRI card + 30-day sparkline, Sleep Debt card + 14-day sparkline
- New computed properties in `src/stores/biometrics.ts`
- 5 new Vue components in `src/components/biometrics/`
- One import added to `BiometricsPage.vue`

### Out of scope
- Kp disruption warning (removed — insufficient scientific signal for a card)
- Social Jet Lag tile (removed)
- Phase C (personalised correlations — requires Supabase history)
- Backend API wiring — all values computed client-side from existing store data
- CYP1A2 / genetic personalisation of caffeine cutoff (Phase C)

---

## Page Layout

```
── existing bento grid (unchanged) ─────────────────────────────────

PROTOCOL INTELLIGENCE                                    [section header]
────────────────────────────────────────────────────────────────────────
[ DLMO ~21:30        ] [ Caffeine cutoff 18:15 ] [ Nap 13:30 · 26min ]
────────────────────────────────────────────────────────────────────────
[  Body Clock Dial   ] [    SRI 84/100        ] [  Sleep Debt −38min ]
[  (~45% width)      ] [    30d sparkline     ] [  14d sparkline     ]
```

**Grid:** CSS Grid, no Tailwind arbitrary values.
```css
.protocol-phase-a { grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
.protocol-phase-b { grid-template-columns: 1.6fr 1fr 1fr; gap: 0.75rem; align-items: start; }

@media (max-width: 640px) {
  .protocol-phase-a { grid-template-columns: 1fr; }
  .protocol-phase-b { grid-template-columns: 1fr; }
}
```

Card surface: `var(--bg-card)`, border `var(--border-card)`, `border-radius: 0.75rem` — matches existing bento tiles exactly.

---

## Store Additions (`src/stores/biometrics.ts`)

All new items are added to the existing store. After defining them, **all new computed properties and the `nowAngle` ref must be added to the `return {}` block** (currently ends at line 761).

### ISO time helper functions

Add these inside the store's `defineStore` callback (not exported):

```typescript
// Parses "HH:MM" or ISO datetime string ("2024-03-15T23:10:00") → minutes since midnight
function timeToMinutes(s: string): number {
  const hhmm = s.length > 5 ? s.slice(11, 16) : s  // ISO → "HH:MM"
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

// Minutes since midnight → "HH:MM", wrapping at 1440
function minutesToTime(min: number): string {
  const wrapped = ((min % 1440) + 1440) % 1440
  const h = Math.floor(wrapped / 60).toString().padStart(2, '0')
  const m = Math.floor(wrapped % 60).toString().padStart(2, '0')
  return `${h}:${m}`
}

function avg(nums: number[]): number {
  return nums.reduce((a, b) => a + b, 0) / nums.length
}
```

### Live now-angle ref

Add a reactive ref that updates every 60s. Defined at store setup level, not inside a computed:

```typescript
const nowAngle = ref<number>(
  ((new Date().getHours() * 60 + new Date().getMinutes()) / 1440) * 360
)

const _nowTimer = setInterval(() => {
  nowAngle.value = ((new Date().getHours() * 60 + new Date().getMinutes()) / 1440) * 360
}, 60_000)

// Note: Pinia stores are singletons — the interval lives as long as the app.
// If store teardown is needed in tests, call clearInterval(_nowTimer) manually.
```

### Phase A — Scalar computed values

```typescript
// DLMO estimate: average sleep onset minus 2 hours
// Basis: Czeisler & Gooley 2007 — DLMO precedes sleep onset by ~2h in entrained adults
// Fallback: '--:--' if fewer than 3 nights with sleep_onset available
const dlmoEstimate = computed<string>(() => {
  const valid = logs.value.filter(l => l.sleep_onset)
  if (valid.length < 3) return '--:--'
  const avgOnsetMin = avg(valid.map(l => timeToMinutes(l.sleep_onset)))
  return minutesToTime(avgOnsetMin - 120)
})

// Caffeine cutoff: average sleep onset minus 6 hours
// Basis: Drake et al. 2013 — caffeine 6h before bedtime reduces sleep by ~1h (JCSM)
// 6h ≈ 5× half-life ÷ 2, ensures <12.5% caffeine remaining at sleep onset
// Fallback: '--:--' if fewer than 3 nights available
const caffeineCutoff = computed<string>(() => {
  const valid = logs.value.filter(l => l.sleep_onset)
  if (valid.length < 3) return '--:--'
  const avgOnsetMin = avg(valid.map(l => timeToMinutes(l.sleep_onset)))
  return minutesToTime(avgOnsetMin - 360)
})

// Nap window: average wake time plus 7 hours
// Basis: Dinges 1992 — post-lunch circadian dip peaks ~7h post-awakening
// Fallback: '--:--' if fewer than 3 nights available
const napWindow = computed<string>(() => {
  const valid = logs.value.filter(l => l.wake_time)
  if (valid.length < 3) return '--:--'
  const avgWakeMin = avg(valid.map(l => timeToMinutes(l.wake_time)))
  return minutesToTime(avgWakeMin + 420)
})
```

### Phase B — Sleep Regularity Index

```typescript
// SRI scalar: 0–100 proxy for sleep regularity
// Adapted from Windred et al. 2024 — proxy formula using MAD of sleep midpoints.
// (True Windred SRI requires minute-level epoch data; this is a clinically reasonable
// approximation from nightly summaries.)
// Formula: 100 − clamp(MAD_of_midpoints / 120 × 100, 0, 100)
// Null if fewer than 7 nights available
const sri = computed<number | null>(() => {
  const valid = logs.value.filter(l => l.sleep_onset && l.wake_time)
  if (valid.length < 7) return null
  const midpoints = valid.map(l => {
    const onset = timeToMinutes(l.sleep_onset)
    const wake  = timeToMinutes(l.wake_time)
    return (onset + wake) / 2
  })
  const meanMid = avg(midpoints)
  const mad = avg(midpoints.map(m => Math.abs(m - meanMid)))
  return Math.max(0, Math.round(100 - (mad / 120) * 100))
})

// SRI 30-day series: one SRI value per day using the preceding 7 nights as the window.
// Returns array of { date: string, value: number | null }
// Used by SRICard sparkline (dates + values extracted separately for buildSparkline())
const sriSeries = computed<{ date: string; value: number | null }[]>(() => {
  const all = logs.value.filter(l => l.sleep_onset && l.wake_time)
  const startIdx = Math.max(0, all.length - 30)
  const last30 = all.slice(startIdx)
  return last30.map((entry, i) => {
    const absIdx = startIdx + i
    const window = all.slice(Math.max(0, absIdx - 6), absIdx + 1)  // up to 7 nights
    if (window.length < 7) return { date: entry.date, value: null }
    const midpoints = window.map(l => (timeToMinutes(l.sleep_onset) + timeToMinutes(l.wake_time)) / 2)
    const meanMid = avg(midpoints)
    const mad = avg(midpoints.map(m => Math.abs(m - meanMid)))
    return { date: entry.date, value: Math.max(0, Math.round(100 - (mad / 120) * 100)) }
  })
})
```

### Phase B — Sleep Debt

```typescript
// Rolling 14-day sleep debt (minutes). Always uses raw logs.value, not windowedLogs,
// so the 7d/30d toggle does not affect debt — debt is always a fixed 14-day window.
// TARGET = 480 min (8h). Positive = surplus, negative = deficit.
const sleepDebtMin = computed<number>(() => {
  const TARGET = 480
  const last14 = logs.value.slice(-14)
  return last14.reduce((acc, l) => acc + (l.total_sleep_min - TARGET), 0)
})

// 14-day daily debt series for sparkline (cumulative daily deviation, not rolling sum)
const sleepDebtSeries = computed<{ date: string; value: number }[]>(() => {
  const TARGET = 480
  return logs.value.slice(-14).map(l => ({
    date: l.date,
    value: l.total_sleep_min - TARGET  // per-night deviation in minutes
  }))
})
```

### Phase B — Dial data

```typescript
interface DialData {
  sleepWindowStart: number  // degrees, 0 = midnight, clockwise
  sleepWindowEnd:   number
  peakAlertStart:   number
  peakAlertEnd:     number
  dlmoAngle:        number
  solarNoonAngle:   number  // from solar store; falls back to 720 min (noon) if unavailable
  // nowAngle is a separate live ref — not included here
}

// Import solar store at top of biometrics store:
// import { useSolarStore } from './solar'
// const solarStore = useSolarStore()

const dialData = computed<DialData | null>(() => {
  if (dlmoEstimate.value === '--:--') return null
  const toAngle = (minutes: number) => (minutes / 1440) * 360
  const valid = logs.value.filter(l => l.sleep_onset && l.wake_time)
  if (valid.length < 3) return null
  const avgOnsetMin = avg(valid.map(l => timeToMinutes(l.sleep_onset)))
  const avgWakeMin  = avg(valid.map(l => timeToMinutes(l.wake_time)))

  // solarStore.solarNoon is a computed<Date>
  // Falls back to solar noon at 720 min (12:00) if solarNoon is unavailable
  const solarNoonDate = solarStore.solarNoon
  const solarNoonMin  = solarNoonDate
    ? solarNoonDate.getHours() * 60 + solarNoonDate.getMinutes()
    : 720

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

**Return block update** — add to the `return {}` in `defineStore`:
```typescript
dlmoEstimate, caffeineCutoff, napWindow,
sri, sriSeries, sleepDebtMin, sleepDebtSeries,
dialData, nowAngle,
```

---

## New Components

All in `src/components/biometrics/`.

### `ProtocolIntelligenceSection.vue`
Container only — no logic. Reads store, renders section header + two grid rows.

```html
<section class="protocol-intelligence">
  <header class="section-header">
    <span class="section-label">PROTOCOL INTELLIGENCE</span>
  </header>
  <div class="protocol-phase-a">
    <PhaseATile label="MELATONIN ONSET" :value="store.dlmoEstimate"
      subtext="dim lights 1h before" accent="#00D4AA" />
    <PhaseATile label="CAFFEINE CUTOFF" :value="store.caffeineCutoff"
      subtext="last coffee by this time" accent="#FFBD76" />
    <PhaseATile label="OPTIMAL NAP" :value="store.napWindow"
      subtext="26 min · NASA protocol" accent="var(--text-muted)" />
  </div>
  <div class="protocol-phase-b">
    <BodyClockDial :data="store.dialData" :now-angle="store.nowAngle" />
    <SRICard :score="store.sri" :series="store.sriSeries" />
    <SleepDebtCard :debt-min="store.sleepDebtMin" :series="store.sleepDebtSeries" />
  </div>
</section>
```

### `PhaseATile.vue`
Props: `label: string`, `value: string`, `subtext: string`, `accent: string`

```
┌─────────────────────────────┐
│ MELATONIN ONSET             │  ← label: text-xs2 (0.5rem), monospace, accent colour
│ 21:30                       │  ← value: 1.4rem, font-weight 800, var(--text-primary)
│ dim lights 1h before        │  ← subtext: text-xs2 (0.5rem), var(--text-muted)
└─────────────────────────────┘
```

Use `text-xs2` (0.5rem `@theme` token from style.css) for both label and subtext. Left border stripe: `border-left: 2.5px solid <accent>`, matches `CircadianInsightsPanel` style.

Value font size (1.4rem) is a scoped CSS value — not a Tailwind class.

### `BodyClockDial.vue`
Props: `data: DialData | null`, `nowAngle: number`

When `data` is null: render the track ring only with a centred "–" label. Do not hide the component.

**ViewBox:** `0 0 200 200`, centre `(100, 100)`, outer radius `r = 88`

**Coordinate system:** 0° = midnight, clockwise. SVG's native 0° is 3 o'clock, so apply a `−90°` offset to all arc/dot positions.

**SVG layers (back to front):**

| # | Element | Spec |
|---|---|---|
| 1 | Track ring | `r=88`, stroke `rgba(255,246,233,0.06)`, `stroke-width=14` |
| 2 | Sleep window arc | `r=88`, stroke `#9B8BFA` opacity 0.5, `stroke-width=14` |
| 3 | Peak alertness arc | `r=88`, stroke `#00D4AA` opacity 0.45, `stroke-width=8` |
| 4 | Solar noon dot | position at `r=88` from `solarNoonAngle`, fill `#FFBD76` opacity 0.5, `r=4` |
| 5 | DLMO dot | position at `r=88` from `dlmoAngle`, fill `#9B8BFA`, `r=5`, white stroke 1.5 |
| 6 | Hour labels | 00/06/12/18 at `r=100`, `font-size=9`, `rgba(255,246,233,0.3)`, `font-family: monospace` |
| 7 | Now needle | line from `(100,100)` to point at `r=72` from `nowAngle`, stroke `rgba(255,246,233,0.85)`, `stroke-width=1.5`, `stroke-linecap=round` |
| 8 | Centre dot | `r=3.5`, fill `#FFF6E9` |

**Arc geometry** — `stroke-dasharray` / `stroke-dashoffset` on a `<circle>`:
```typescript
const CIRC = 2 * Math.PI * 88  // ≈ 552.9

// angleStart, angleEnd: degrees (0 = midnight, clockwise)
function arcDash(angleStart: number, angleEnd: number) {
  const delta   = ((angleEnd - angleStart + 360) % 360)
  const dashLen = (delta / 360) * CIRC
  // SVG offset: subtract arc start from full circumference, then apply −90° correction
  const offset  = CIRC - (angleStart / 360) * CIRC + CIRC * 0.25
  return {
    strokeDasharray:  `${dashLen} ${CIRC - dashLen}`,
    strokeDashoffset: offset,
  }
}
```

**Dot positions** — convert angle to SVG `(x, y)`:
```typescript
function angleToXY(angleDeg: number, r: number, cx = 100, cy = 100) {
  const rad = ((angleDeg - 90) * Math.PI) / 180  // −90° so 0° = top
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}
```

**Hover tooltip:** use SVG `<title>` on each arc — browser-native, no custom tooltip needed in V1.

### `SRICard.vue`
Props: `score: number | null`, `series: { date: string; value: number | null }[]`

```
┌─────────────────────────────┐
│ SLEEP REGULARITY INDEX      │  ← text-xs3, monospace, var(--text-muted)
│ 84 / 100                    │  ← score: 1.6rem bold #00D4AA, "/100" text-muted
│ [30-day sparkline]          │  ← buildSparkline(values, 200, 28) — teal stroke
│ adapted · Windred 2024      │  ← text-xs3, var(--text-muted), italic
└─────────────────────────────┘
```

When `score` is null: render `--` in place of the number, omit sparkline, show "Need 7+ nights".

Sparkline: extract `series.map(s => s.value)` and `series.map(s => s.date)` and pass to `buildSparkline()` from `useSparkline.ts`.

### `SleepDebtCard.vue`
Props: `debtMin: number`, `series: { date: string; value: number }[]`

```
┌─────────────────────────────┐
│ SLEEP DEBT · 14-DAY         │  ← text-xs3, monospace, var(--text-muted)
│ −38 min                     │  ← value: 1.6rem bold, accent by threshold (see below)
│ [14-day sparkline]          │  ← per-night deviation bars
└─────────────────────────────┘
```

**Accent colour by threshold:**
- Surplus (`debtMin > 0`): `#00D4AA` (Calm)
- Deficit < 60 min (`debtMin` between −60 and 0): `#FFBD76` (Nectarine)
- Deficit ≥ 60 min (`debtMin ≤ −60`): `#FF4444` (Storm)

Sparkline: per-night deviation values. Zero-line rendered as a faint dashed horizontal rule in the SVG at the midpoint.

---

## Integration

In `BiometricsPage.vue`, add below the existing bento section:
```html
<ProtocolIntelligenceSection />
```

One import, one tag. The section is entirely self-contained.

---

## Scientific Basis

| Feature | Basis |
|---|---|
| DLMO −2h from sleep onset | Czeisler & Gooley 2007 — DLMO precedes sleep onset by ~2h in entrained adults |
| Caffeine cutoff −6h | Drake et al. 2013 — caffeine 6h before bedtime reduces sleep by ~1h (JCSM) |
| Nap at wake+7h | Dinges 1992 — post-lunch dip peaks 7–8h post-awakening |
| SRI (adapted) | Windred et al. 2024 — sleep regularity predicts mortality; proxy formula using MAD of midpoints |

---

## Verification

1. Navigate to `/biometrics` — Protocol Intelligence section renders below bento with no console errors
2. `dlmoEstimate` = average sleep onset − 120 min; verify against mock data manually
3. `caffeineCutoff` = average sleep onset − 360 min
4. `napWindow` = average wake time + 420 min
5. All three Phase A tiles show `--:--` when mock data is replaced with fewer than 3 nights
6. Body Clock Dial renders all arcs — sleep window violet, peak alertness teal
7. Now needle points to the correct current time (compare to system clock)
8. Needle moves without page refresh after 61 seconds
9. `dialData` is null and dial shows `–` empty state when fewer than 3 nights available
10. `solarNoonAngle` defaults to `toAngle(720)` (12:00) when solar store returns null
11. SRI card shows `--` / "Need 7+ nights" when fewer than 7 nights in `logs`
12. `sleepDebtMin` always uses the last 14 entries from `logs.value` regardless of 7d/30d toggle
13. Sleep Debt accent is teal for surplus, nectarine for 0–59 min deficit, red for ≥60 min deficit
14. `sriSeries` and `sleepDebtSeries` are both exported from the store return block
15. Mobile (≤640px): both rows stack to single column, all components visible without horizontal scroll
