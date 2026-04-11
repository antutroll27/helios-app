# Protocol Card Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current ProtocolCard design (left accent bar, bar/tick data strip, plain-text status) with Swiss-style solid-tinted cards featuring icon-specific SVG visualisations, pill status buttons, and semi-interactive hover crosshairs.

**Architecture:** Three files change in dependency order — `protocol.ts` adds `VizData` data, `ProtocolTimeline.vue` passes it as a prop, `ProtocolCard.vue` is fully rewritten to consume it and render icon-specific SVG visualisations. No new files are created.

**Tech Stack:** Vue 3 `<script setup>` + TypeScript, Pinia, scoped CSS (no Tailwind arbitrary values — all custom values go in `<style scoped>`)

**Spec:** `helios-app/docs/superpowers/specs/2026-04-11-protocol-card-redesign.md`
**Reference mockup:** `helios-app/.superpowers/brainstorm/3322-1775877764/card-solid-v6.html`

---

## File Map

| File | Change |
|---|---|
| `src/stores/protocol.ts` | Add `VizData` export interface; add `vizData?: VizData` to `ProtocolItem`; wire per-card values inside `dailyProtocol` computed |
| `src/components/ProtocolTimeline.vue` | Add `:viz-data="item.vizData"` to the `<ProtocolCard>` binding |
| `src/components/ProtocolCard.vue` | Full rewrite — new script (remove old computeds, add new), new template (SVG viz), new scoped CSS |

---

## Task 1: Add `VizData` to `protocol.ts`

**Files:**
- Modify: `src/stores/protocol.ts:14-22` (ProtocolItem interface) and `src/stores/protocol.ts:122-203` (dailyProtocol computed)

**Context:** `protocol.ts` has no test file — verification is `npm run build` with zero TypeScript errors.

- [ ] **Step 1: Add the `VizData` interface and `vizData` field to `ProtocolItem`**

Open `src/stores/protocol.ts`. Insert the new `VizData` interface **before** the `ProtocolItem` interface (currently at line 14), and add `vizData?: VizData` as the last field of `ProtocolItem`:

```typescript
// Insert this block BEFORE the existing `export interface ProtocolItem {`
export interface VizData {
  supLabel: string       // superscript next to time: "AM" | "20 MIN" | "3H WIN" | "6H T½" | "90 MIN" | "LATE"
  ringPct?: number       // 0–100, for ring cards (Wind-Down, Sleep Window)
  ringCenter?: string    // text inside ring: "90" | alignment score string
  ringUnit?: string      // unit below ring center: "MIN" | "ALIGN%"
  stat1Label?: string
  stat1Value?: string
  stat2Label?: string
  stat2Value?: string
}

export interface ProtocolItem {
  key: string
  title: string
  time: Date
  endTime?: Date
  icon: string
  citation: string
  subtitle: string
  vizData?: VizData      // ← new field
}
```

The existing `ProtocolItem` block (lines 14–22) should be **replaced** with the version above that includes `vizData?: VizData`.

- [ ] **Step 2: Wire `vizData` into each protocol item inside `dailyProtocol`**

In the `dailyProtocol` computed (currently lines 122–203), add a `vizData` property to each of the six items. The values are computed from local refs that are already in scope (`wakeWindowTime`, `wakeWindowEnd`, `sleepTime`, `melatoninOnset`, `windDownStart`, `morningLightDurationMin`, `solar`, `fmt`).

Replace the six items in the `return { ... }` block with this complete block:

```typescript
return {
  wakeWindow: {
    key: 'wakeWindow',
    title: 'Wake Window',
    time: wakeWindowTime.value,
    endTime: wakeWindowEnd.value,
    icon: 'Sunrise',
    citation: 'Cortisol awakening response peaks within 30 min of solar elevation > 6 degrees',
    subtitle: isNightOwlWake
      ? `Rise at ${fmt(wakeWindowTime.value)} (8h sleep). Get sunlight within 30 min of waking.`
      : `Rise between ${fmt(wakeWindowTime.value)} - ${fmt(wakeWindowEnd.value)} to anchor your circadian clock.`,
    vizData: {
      supLabel: 'AM',
      stat1Label: 'Window',
      stat1Value: `${Math.round((wakeWindowEnd.value.getTime() - wakeWindowTime.value.getTime()) / 60_000)} min`,
      stat2Label: 'Sleep',
      stat2Value: (() => {
        const ms = wakeWindowTime.value.getTime() - sleepTime.value.getTime()
        const h = Math.floor(ms / 3_600_000)
        const m = Math.round((ms % 3_600_000) / 60_000)
        return `${h}h ${m}m`
      })(),
    },
  },

  morningLight: {
    key: 'morningLight',
    title: 'Morning Light',
    time: solar.wakeWindowEnd,
    endTime: new Date(solar.wakeWindowEnd.getTime() + morningLightDurationMin.value * 60_000),
    icon: 'Sun',
    citation: 'NASA ISS protocol: timed bright light for circadian entrainment',
    subtitle: `Get ${lightDuration} min of bright outdoor light starting at ${fmt(solar.wakeWindowStart)}${aqiWarning}.`,
    vizData: {
      supLabel: `${morningLightDurationMin.value} MIN`,
    },
  },

  peakFocus: {
    key: 'peakFocus',
    title: 'Peak Focus',
    time: peakFocusStart.value,
    endTime: peakFocusEnd.value,
    icon: 'Brain',
    citation: 'Cognitive performance peaks in late afternoon/evening, paralleling core body temperature rhythm',
    subtitle: `Recommended deep-work window: ${fmt(peakFocusStart.value)} - ${fmt(peakFocusEnd.value)}. The pre-sleep wake-maintenance zone is a separate alertness phenomenon, not your default best focus window.`,
    vizData: {
      supLabel: '3H WIN',
    },
  },

  caffeineCutoff: {
    key: 'caffeineCutoff',
    title: 'Caffeine Cutoff',
    time: caffeineCutoff.value,
    icon: 'Coffee',
    citation: 'Burke et al. (2015): caffeine 3h before bed delays melatonin by 40 min',
    subtitle: getCaffeineCutoffNarrative(fmt(caffeineCutoff.value), fmt(sleepTime.value)),
    vizData: {
      supLabel: '6H T½',
    },
  },

  windDown: {
    key: 'windDown',
    title: 'Wind-Down',
    time: windDownStart.value,
    endTime: sleepTime.value,
    icon: 'Moon',
    citation: 'Begin screen dimming 90 min before estimated melatonin onset',
    subtitle: `Start dimming screens and lowering stimulation at ${fmt(windDownStart.value)}${windDownAdj}.`,
    vizData: (() => {
      const durationMin = Math.round(
        (sleepTime.value.getTime() - windDownStart.value.getTime()) / 60_000
      )
      const h = Math.floor(durationMin / 60)
      const m = durationMin % 60
      return {
        supLabel: `${durationMin} MIN`,
        ringPct: Math.min(Math.round((durationMin / 180) * 100), 100),
        ringCenter: String(durationMin),
        ringUnit: 'MIN',
        stat1Label: 'Until sleep',
        stat1Value: h > 0 ? `${h}h${m > 0 ? ` ${m}m` : ''}` : `${m}m`,
        stat2Label: 'Melatonin onset',
        stat2Value: fmt(melatoninOnset.value),
      }
    })(),
  },

  sleepWindow: {
    key: 'sleepWindow',
    title: 'Sleep Window',
    time: sleepTime.value,
    icon: 'BedDouble',
    citation: 'Optimal sleep onset aligned with solar cycle and chronotype',
    subtitle: `Target sleep by ${fmt(sleepTime.value)} (${user.chronotype} chronotype).${solarAlignmentNote}`,
    vizData: (() => {
      const nadir = solar.nadir
      const gapMs = Math.abs(sleepTime.value.getTime() - nadir.getTime())
      const gapH = (gapMs / 3_600_000).toFixed(1)
      const alignPct = Math.max(0, Math.round((1 - gapMs / (6 * 3_600_000)) * 100))
      return {
        supLabel: 'LATE',
        ringPct: alignPct,
        ringCenter: String(alignPct),
        ringUnit: 'ALIGN%',
        stat1Label: 'Solar gap',
        stat1Value: `${gapH}h`,
        stat2Label: 'Solar midnight',
        stat2Value: fmt(nadir),
      }
    })(),
  },
}
```

- [ ] **Step 3: Build to verify zero TypeScript errors**

```bash
cd helios-app && npm run build
```

Expected: build completes with no errors. If TypeScript complains about `vizData` being unknown, confirm the `ProtocolItem` interface change from Step 1 was saved.

- [ ] **Step 4: Commit**

```bash
git add helios-app/src/stores/protocol.ts
git commit -m "feat(protocol): add VizData interface and wire per-card viz data"
```

---

## Task 2: Pass `vizData` prop in `ProtocolTimeline.vue`

**Files:**
- Modify: `src/components/ProtocolTimeline.vue:54-64` (the `<ProtocolCard>` binding block)

**Context:** `ProtocolTimeline.vue` renders 6 `<ProtocolCard>` items from `protocolItems`. It already passes `title`, `time`, `end-time`, `icon`, `citation`, `subtitle`, `status`. Add `:viz-data`.

- [ ] **Step 1: Add the `:viz-data` binding**

In `src/components/ProtocolTimeline.vue`, find the `<ProtocolCard>` template (lines 54–64) and add one line:

```html
<ProtocolCard
  v-for="item in protocolItems"
  :key="item.key"
  :title="item.title"
  :time="item.time"
  :end-time="item.endTime"
  :icon="item.icon"
  :citation="item.citation"
  :subtitle="item.subtitle"
  :status="getStatus(item.time, item.endTime)"
  :viz-data="item.vizData"
/>
```

- [ ] **Step 2: Build to verify**

```bash
cd helios-app && npm run build
```

Expected: zero errors. TypeScript may warn about `vizData` being an unknown prop on `ProtocolCard` until Task 3 is done — that is expected.

- [ ] **Step 3: Commit**

```bash
git add helios-app/src/components/ProtocolTimeline.vue
git commit -m "feat(timeline): pass vizData prop to ProtocolCard"
```

---

## Task 3: Rewrite `ProtocolCard.vue`

**Files:**
- Modify: `src/components/ProtocolCard.vue` (full rewrite of `<script setup>`, `<template>`, `<style scoped>`)

**Context:** This is a complete visual redesign. The existing component has:
- Left accent bar (`::before`), card border, hairline, bar/tick strip
- Plain-text status label

The new design has:
- Solid accent-tinted background, no border, no `::before`, no hairline
- Pill status button with semantic colours (green=active, red=passed, muted=upcoming)
- Hero time with superscript label (`vizData.supLabel`)
- Icon-specific SVG viz pill: clock arc (Wake), bell curve with crosshair (Light/Focus/Caffeine), ring progress (Wind-Down/Sleep)

**Important CSS rule:** All pixel/rem values go in `<style scoped>`, never as Tailwind arbitrary bracket values.

**Important SVG rule:** SVG `<linearGradient>` IDs must be unique per component instance to avoid DOM collisions when 6 cards render simultaneously. Use a `uid` string generated once per instance.

- [ ] **Step 1: Replace the entire `<script setup>` block**

Replace everything between `<script setup lang="ts">` and `</script>` with:

```typescript
import { computed, ref } from 'vue'
import type { VizData } from '@/stores/protocol'

const props = defineProps<{
  title: string
  time: Date
  endTime?: Date
  icon: string
  citation: string
  subtitle: string
  status: 'upcoming' | 'active' | 'passed'
  vizData?: VizData
}>()

// ── Theme ─────────────────────────────────────────────────────────
const cardThemes: Record<string, string> = {
  Sunrise:   '#FFBD76',
  Sun:       '#E8C547',
  Brain:     '#9B8BFA',
  Coffee:    '#F08060',
  Moon:      '#5BBFD6',
  BedDouble: '#8899CC',
}
const theme = computed(() => cardThemes[props.icon] ?? '#FFBD76')

// ── Time display ───────────────────────────────────────────────────
// timeParts is also used in the Caffeine SVG to render cutoff time inline
const timeParts = computed(() => {
  try {
    const d = props.time instanceof Date ? props.time : new Date(props.time)
    const str = isNaN(d.getTime())
      ? String(props.time)
      : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    const [h, m] = str.split(':')
    return { h: h ?? str, m: m ?? '' }
  } catch {
    return { h: String(props.time), m: '' }
  }
})

// ── Viz type flags ─────────────────────────────────────────────────
const isArcCard   = computed(() => props.icon === 'Sunrise')
const isCurveCard = computed(() => ['Sun', 'Brain', 'Coffee'].includes(props.icon))
const isRingCard  = computed(() => ['Moon', 'BedDouble'].includes(props.icon))

// ── Unique gradient ID suffix (prevents SVG id collisions) ─────────
// 6 cards render simultaneously; each needs unique gradient element IDs
const uid = Math.random().toString(36).slice(2, 6)

// ── Ring progress ──────────────────────────────────────────────────
// Circumference of r=30 circle ≈ 188.5; dashoffset controls fill
const ringDashoffset = computed(() => {
  const pct = props.vizData?.ringPct ?? 0
  return 188.5 * (1 - pct / 100)
})

// ── Crosshair interactivity (curve cards only) ─────────────────────
const curveWrapRef = ref<HTMLElement | null>(null)
const crosshairX   = ref(0)
const crosshairY   = ref(0)
const crosshairVisible = ref(false)

// Sampled bezier points for linear interpolation — matches SVG path data below
const curvePathPoints: Record<string, [number, number][]> = {
  Sun:    [[0,68],[18,65],[36,55],[55,40],[68,29],[80,19],[95,10],[108,3],[118,2],[125,3],[132,4],[145,10],[155,20],[168,33],[185,52],[200,64],[210,66],[216,68]],
  Brain:  [[0,68],[20,66],[40,60],[60,46],[80,30],[100,14],[108,7],[114,3],[120,2],[125,2],[130,2],[136,4],[145,10],[155,18],[168,30],[180,46],[196,60],[210,66],[216,68]],
  Coffee: [[0,12],[40,12],[80,12],[88,12],[100,16],[115,25],[130,36],[148,48],[165,57],[185,63],[205,66],[216,68]],
}

const VB_W = 216
const VB_H = 75

function lerp(a: number, b: number, t: number) { return a + (b - a) * t }

function getYatX(points: [number, number][], x: number): number {
  for (let i = 0; i < points.length - 1; i++) {
    const [x0, y0] = points[i]
    const [x1, y1] = points[i + 1]
    if (x >= x0 && x <= x1) return lerp(y0, y1, (x - x0) / (x1 - x0))
  }
  return points[points.length - 1][1]
}

function onCurveMouseMove(e: MouseEvent) {
  if (!curveWrapRef.value) return
  const rect = curveWrapRef.value.getBoundingClientRect()
  const PAD_L = 8, PAD_T = 7
  const innerW = rect.width  - PAD_L - 8
  const innerH = rect.height - PAD_T - 4
  const mx    = e.clientX - rect.left - PAD_L
  const svgX  = Math.max(0, Math.min(VB_W, (mx / innerW) * VB_W))
  const svgY  = getYatX(curvePathPoints[props.icon] ?? [], svgX)
  crosshairX.value = mx + PAD_L
  crosshairY.value = (svgY / VB_H) * innerH + PAD_T
}
```

- [ ] **Step 2: Replace the entire `<template>` block**

Replace everything between `<template>` and `</template>` with:

```html
<template>
  <div
    class="card"
    :class="{ 'card--passed': status === 'passed' }"
    :style="{ '--accent': theme }"
  >

    <!-- Header: dot + label + status pill -->
    <div class="card-header">
      <div class="card-label-group">
        <span class="card-dot" />
        <span class="card-label">{{ title }}</span>
      </div>
      <span class="status-pill" :class="`pill-${status}`">
        <span class="sdot" />
        {{ status === 'active' ? 'Active' : status === 'passed' ? 'Passed' : 'Upcoming' }}
      </span>
    </div>

    <!-- Hero time: HH:MM + superscript context label -->
    <div class="card-time-wrap">
      <span class="t-h">{{ timeParts.h }}</span>
      <span class="t-sep">:</span>
      <span class="t-m">{{ timeParts.m }}</span>
      <span v-if="vizData?.supLabel" class="t-sup">{{ vizData.supLabel }}</span>
    </div>

    <!-- Viz pill -->
    <div class="pill-viz">

      <!-- Clock arc — Wake Window (Sunrise) -->
      <div v-if="isArcCard" class="pill-data-wrap">
        <svg width="68" height="68" viewBox="0 0 72 72" style="flex-shrink:0">
          <circle cx="36" cy="36" r="28" fill="none" stroke="rgba(255,246,233,0.07)" stroke-width="4"/>
          <path d="M36 8 A28 28 0 0 1 64 36" fill="none" stroke="rgba(255,246,233,0.09)" stroke-width="4" stroke-linecap="round"/>
          <path d="M64 36 A28 28 0 0 1 55.8 55.8" fill="none" :stroke="theme" stroke-width="5" stroke-linecap="round"/>
          <circle cx="64" cy="36" r="3" :fill="theme"/>
          <line x1="36" y1="8"  x2="36" y2="13"  stroke="rgba(255,246,233,0.14)" stroke-width="1.2"/>
          <line x1="64" y1="36" x2="59" y2="36"  stroke="rgba(255,246,233,0.14)" stroke-width="1.2"/>
          <line x1="36" y1="64" x2="36" y2="59"  stroke="rgba(255,246,233,0.14)" stroke-width="1.2"/>
          <line x1="8"  y1="36" x2="13" y2="36"  stroke="rgba(255,246,233,0.14)" stroke-width="1.2"/>
        </svg>
        <div class="pill-stats">
          <div v-if="vizData?.stat1Label">
            <div class="pill-lbl">{{ vizData.stat1Label }}</div>
            <div class="pill-val">{{ vizData.stat1Value }}</div>
          </div>
          <div v-if="vizData?.stat2Label">
            <div class="pill-lbl">{{ vizData.stat2Label }}</div>
            <div class="pill-val">{{ vizData.stat2Value }}</div>
          </div>
        </div>
      </div>

      <!-- Bell/decay curves — Morning Light (Sun), Peak Focus (Brain), Caffeine Cutoff (Coffee) -->
      <div
        v-else-if="isCurveCard"
        ref="curveWrapRef"
        class="pill-curve-wrap"
        @mousemove="onCurveMouseMove"
        @mouseenter="crosshairVisible = true"
        @mouseleave="crosshairVisible = false"
      >
        <!-- Crosshair overlays — positioned absolute, driven by JS -->
        <div
          class="crosshair-line"
          :style="{ left: crosshairX + 'px', opacity: crosshairVisible ? 1 : 0 }"
        />
        <div
          class="crosshair-dot"
          :style="{ left: crosshairX + 'px', top: crosshairY + 'px', opacity: crosshairVisible ? 1 : 0 }"
        />

        <!-- Morning Light: bell curve centred on solar noon, NOW marker at sunrise -->
        <svg v-if="icon === 'Sun'" viewBox="0 0 216 75" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient :id="`g-sun-${uid}`" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" :stop-color="theme" stop-opacity="0.5"/>
              <stop offset="100%" :stop-color="theme" stop-opacity="0.04"/>
            </linearGradient>
          </defs>
          <line x1="0" y1="68" x2="216" y2="68" stroke="rgba(255,246,233,0.09)" stroke-width="1"/>
          <path d="M0 68 C18 65 36 55 55 40 C68 29 80 19 95 10 C108 3 118 2 125 3 C132 4 145 10 155 20 C168 33 185 52 200 64 C208 66 216 68 216 68 Z" :fill="`url(#g-sun-${uid})`"/>
          <path d="M0 68 C18 65 36 55 55 40 C68 29 80 19 95 10 C108 3 118 2 125 3 C132 4 145 10 155 20 C168 33 185 52 200 64 C208 66 216 68" fill="none" :stroke="theme" stroke-width="2" stroke-linecap="round"/>
          <circle cx="60" cy="37" r="4.5" :fill="theme"/>
          <line x1="60" y1="37" x2="60" y2="68" :stroke="theme" stroke-opacity="0.3" stroke-width="1.5" stroke-dasharray="2 2"/>
          <rect x="60" y="4" width="24" height="64" :fill="theme" fill-opacity="0.1" rx="2"/>
          <text x="4"   y="74" font-size="7" fill="rgba(255,246,233,0.22)" font-family="'JetBrains Mono',monospace">DAWN</text>
          <text x="52"  y="74" font-size="7" :fill="theme" font-family="'JetBrains Mono',monospace">NOW</text>
          <text x="184" y="74" font-size="7" fill="rgba(255,246,233,0.22)" font-family="'JetBrains Mono',monospace">NOON</text>
        </svg>

        <!-- Peak Focus: bell curve with 15–18h window highlight -->
        <svg v-else-if="icon === 'Brain'" viewBox="0 0 216 75" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient :id="`g-foc-${uid}`" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" :stop-color="theme" stop-opacity="0.5"/>
              <stop offset="100%" :stop-color="theme" stop-opacity="0.04"/>
            </linearGradient>
          </defs>
          <line x1="0" y1="68" x2="216" y2="68" stroke="rgba(255,246,233,0.09)" stroke-width="1"/>
          <path d="M0 68 C20 66 40 60 60 46 C80 30 100 14 108 7 C114 3 120 2 125 2 C130 2 136 4 145 10 C155 18 168 30 180 46 C196 60 210 66 216 68 Z" :fill="`url(#g-foc-${uid})`"/>
          <path d="M0 68 C20 66 40 60 60 46 C80 30 100 14 108 7 C114 3 120 2 125 2 C130 2 136 4 145 10 C155 18 168 30 180 46 C196 60 210 66 216 68" fill="none" :stroke="theme" stroke-width="2" stroke-linecap="round"/>
          <rect x="108" y="2" width="47" height="66" :fill="theme" fill-opacity="0.13" rx="3"/>
          <circle cx="125" cy="2" r="4" :fill="theme"/>
          <text x="4"   y="74" font-size="7" fill="rgba(255,246,233,0.22)" font-family="'JetBrains Mono',monospace">WAKE</text>
          <text x="100" y="74" font-size="7" :fill="theme" font-family="'JetBrains Mono',monospace">15–18h</text>
          <text x="188" y="74" font-size="7" fill="rgba(255,246,233,0.22)" font-family="'JetBrains Mono',monospace">BED</text>
        </svg>

        <!-- Caffeine Cutoff: flat high → exponential decay at cutoff marker -->
        <svg v-else-if="icon === 'Coffee'" viewBox="0 0 216 75" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient :id="`g-caf-${uid}`" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" :stop-color="theme" stop-opacity="0.5"/>
              <stop offset="100%" :stop-color="theme" stop-opacity="0.03"/>
            </linearGradient>
          </defs>
          <line x1="0" y1="68" x2="216" y2="68" stroke="rgba(255,246,233,0.09)" stroke-width="1"/>
          <path d="M0 12 L88 12" :stroke="theme" stroke-width="1.8" stroke-dasharray="4 3" stroke-opacity="0.45" fill="none" stroke-linecap="round"/>
          <path d="M88 12 C102 12 112 18 126 28 C140 38 158 52 178 61 C196 67 210 68 216 68 Z" :fill="`url(#g-caf-${uid})`"/>
          <path d="M88 12 C102 12 112 18 126 28 C140 38 158 52 178 61 C196 67 210 68 216 68" fill="none" :stroke="theme" stroke-width="2" stroke-linecap="round"/>
          <line x1="88" y1="4" x2="88" y2="68" :stroke="theme" stroke-width="1.5" stroke-opacity="0.45" stroke-dasharray="3 2"/>
          <circle cx="88" cy="12" r="4.5" :fill="theme"/>
          <text x="4"  y="9"  font-size="7" fill="rgba(255,246,233,0.25)" font-family="'JetBrains Mono',monospace">HIGH</text>
          <text x="65" y="74" font-size="7" :fill="theme"                  font-family="'JetBrains Mono',monospace">{{ timeParts.h }}:{{ timeParts.m }}</text>
          <text x="175" y="50" font-size="7" fill="rgba(255,246,233,0.22)" font-family="'JetBrains Mono',monospace">BED</text>
        </svg>
      </div>

      <!-- Ring progress — Wind-Down (Moon), Sleep Window (BedDouble) -->
      <div v-else-if="isRingCard" class="pill-data-wrap">
        <svg width="64" height="64" viewBox="0 0 76 76" style="flex-shrink:0">
          <circle cx="38" cy="38" r="30" fill="none" stroke="rgba(255,246,233,0.08)" stroke-width="5.5"/>
          <circle
            cx="38" cy="38" r="30"
            fill="none" :stroke="theme" stroke-width="5.5"
            stroke-dasharray="188.5" :stroke-dashoffset="ringDashoffset"
            stroke-linecap="round" transform="rotate(-90 38 38)"
          />
          <text x="38" y="35" text-anchor="middle" font-size="13" font-weight="800" fill="#FFF6E9" font-family="'JetBrains Mono',monospace">{{ vizData?.ringCenter }}</text>
          <text x="38" y="47" text-anchor="middle" font-size="5.5" fill="rgba(255,246,233,0.35)" font-family="'JetBrains Mono',monospace">{{ vizData?.ringUnit }}</text>
        </svg>
        <div class="pill-stats">
          <!-- stat1 uses accent colour (primary metric) -->
          <div v-if="vizData?.stat1Label">
            <div class="pill-lbl">{{ vizData.stat1Label }}</div>
            <div class="pill-val-a">{{ vizData.stat1Value }}</div>
          </div>
          <!-- stat2 uses white (secondary metric) -->
          <div v-if="vizData?.stat2Label">
            <div class="pill-lbl">{{ vizData.stat2Label }}</div>
            <div class="pill-val">{{ vizData.stat2Value }}</div>
          </div>
        </div>
      </div>

    </div><!-- /pill-viz -->

    <!-- Description -->
    <p class="card-desc">{{ subtitle }}</p>

    <!-- Citation -->
    <p class="card-cite">/ {{ citation }}</p>

  </div>
</template>
```

- [ ] **Step 3: Replace the entire `<style scoped>` block**

Replace everything between `<style scoped>` and `</style>` with:

```css
/* ── Card shell ─────────────────────────────────────────────────────── */
.card {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  gap: 0.6rem;
  border-radius: 14px;
  background: color-mix(in srgb, var(--accent) 12%, #07111a);
  /* intentionally no border and no ::before accent bar */
}

.card--passed {
  opacity: 0.3;
}

/* ── Header ──────────────────────────────────────────────────────────── */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-label-group {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.card-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
}

.card-label {
  font-size: 0.48rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--accent) 85%, #FFF6E9);
}

/* ── Status pill ─────────────────────────────────────────────────────── */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.5rem 0.2rem 0.38rem;
  border-radius: 999px;
  font-size: 0.38rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.sdot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}

.pill-upcoming { background: rgba(255,246,233,0.08); color: rgba(255,246,233,0.45); }
.pill-upcoming .sdot { background: rgba(255,246,233,0.3); }

.pill-active { background: rgba(0,212,170,0.12); color: #00D4AA; }
.pill-active .sdot {
  background: #00D4AA;
  box-shadow: 0 0 4px rgba(0,212,170,0.8);
  animation: blink 2s ease-in-out infinite;
}

.pill-passed { background: rgba(255,68,68,0.10); color: rgba(255,68,68,0.75); }
.pill-passed .sdot { background: #FF4444; }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.35; }
}

/* ── Hero time ───────────────────────────────────────────────────────── */
.card-time-wrap {
  display: flex;
  align-items: baseline;
  line-height: 1;
  margin-bottom: 0.4rem;
}

.t-h,
.t-m {
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: #FFF6E9;
}

.t-sep {
  font-size: 2.5rem;
  font-weight: 200;
  letter-spacing: -0.04em;
  color: #FFF6E9;
  opacity: 0.18;
  margin: 0 0.5px;
}

.t-sup {
  font-size: 0.65rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  color: rgba(255,246,233,0.35);
  margin-left: 0.35rem;
  align-self: flex-start;
  padding-top: 0.4rem;
}

/* ── Viz pill container ──────────────────────────────────────────────── */
.pill-viz {
  border-radius: 10px;
  background: color-mix(in srgb, var(--accent) 20%, #04090d);
  overflow: hidden;
}

/* ── Curve wrap (Morning Light, Peak Focus, Caffeine) ────────────────── */
.pill-curve-wrap {
  height: 76px;
  display: flex;
  align-items: stretch;
  padding: 0.45rem 0.55rem 0.28rem;
  position: relative;
  cursor: crosshair;
}

.pill-curve-wrap svg {
  width: 100%;
  height: 100%;
  display: block;
}

/* Crosshair elements — positioned absolute over the SVG */
.crosshair-line {
  position: absolute;
  top: 7px;
  bottom: 7px;
  width: 1px;
  background: rgba(255,246,233,0.35);
  pointer-events: none;
  transition: opacity 0.1s;
}

.crosshair-dot {
  position: absolute;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  border: 1.5px solid #FFF6E9;
  transform: translate(-50%, -50%);
  pointer-events: none;
  transition: opacity 0.1s;
}

/* ── Arc + ring data rows (Wake, Wind-Down, Sleep) ───────────────────── */
.pill-data-wrap {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.65rem 0.8rem;
}

.pill-stats {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.pill-lbl {
  font-size: 0.34rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--accent) 55%, rgba(255,246,233,0.25));
  margin-bottom: 0.04rem;
}

/* pill-val = white — secondary stat (e.g. "23:00" melatonin onset) */
.pill-val {
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1;
  color: #FFF6E9;
}

/* pill-val-a = accent colour — primary stat (e.g. "1.5h" until sleep) */
.pill-val-a {
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
  color: var(--accent);
}

/* ── Footer ──────────────────────────────────────────────────────────── */
.card-desc {
  font-family: var(--font-body);
  font-size: 0.5rem;
  color: rgba(255,246,233,0.52);
  line-height: 1.55;
}

.card-cite {
  font-size: 0.36rem;
  color: rgba(255,246,233,0.18);
}
```

- [ ] **Step 4: Build to verify zero errors**

```bash
cd helios-app && npm run build
```

Expected: zero TypeScript errors. If you see errors about missing `VizData` export, verify Task 1 exported the interface with `export interface VizData`.

- [ ] **Step 5: Visual verification in dev server**

```bash
cd helios-app && npm run dev
```

Open the app in the browser. Check all 6 protocol cards:

| Card | Expected viz |
|---|---|
| Wake Window | Clock arc SVG + "Window / Sleep" stats |
| Morning Light | Bell curve SVG + NOW marker; hover → crosshair tracks mouse |
| Peak Focus | Bell curve + 15–18h highlight; hover crosshair |
| Caffeine Cutoff | Decay curve + cutoff marker; hover crosshair |
| Wind-Down | Ring progress + "Until sleep / Melatonin onset" stats |
| Sleep Window | Ring progress (alignment %) + "Solar gap / Solar midnight" |

Also verify:
- No left accent bar on any card
- No card border
- Status pills: green dot (active), red dot (passed), muted dot (upcoming)
- Passed cards dim to 30% opacity
- Responsive: at 900px → 2-col, at 500px → 1-col (grid is in ProtocolTimeline.vue, unchanged)

- [ ] **Step 6: Commit**

```bash
git add helios-app/src/components/ProtocolCard.vue
git commit -m "feat(card): redesign ProtocolCard with SVG viz, pill status, solid accent background"
```

---

## Final verification

```bash
cd helios-app && npm run build
```

Zero errors = done. Push to `dev` branch when confirmed working.
