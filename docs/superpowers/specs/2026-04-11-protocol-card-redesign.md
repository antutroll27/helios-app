# Protocol Card Redesign — Design Spec

## Overview

Replace the current `ProtocolCard.vue` (left accent bar, horizontal bar/tick strip, plain-text status) with a Swiss-style solid-tinted card featuring icon-specific SVG visualizations, JetBrains Mono typography, pill status buttons, and semi-interactive hover crosshairs on curve charts.

Reference mockup: `helios-app/.superpowers/brainstorm/3322-1775877764/card-solid-v6.html`

---

## Files to Modify

| File | Change |
|---|---|
| `src/stores/protocol.ts` | Add `VizData` interface + `vizData` field to `ProtocolItem`; wire per-card values |
| `src/components/ProtocolTimeline.vue` | Pass `:viz-data="item.vizData"` prop to `<ProtocolCard>` |
| `src/components/ProtocolCard.vue` | Full visual redesign — all CSS and template |

---

## 1. Data Model (`protocol.ts`)

### New interface

```typescript
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
```

Add `vizData?: VizData` to `ProtocolItem`.

### Wire in `dailyProtocol` computed

**Wake Window** (`Sunrise`):
```typescript
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
}
```

**Morning Light** (`Sun`):
```typescript
vizData: {
  supLabel: `${morningLightDurationMin.value} MIN`,
}
```
`morningLightDurationMin` is already a computed in `protocol.ts` (AQI-adjusted duration).

**Peak Focus** (`Brain`):
```typescript
vizData: { supLabel: '3H WIN' }
```

**Caffeine Cutoff** (`Coffee`):
```typescript
vizData: { supLabel: '6H T½' }
```

**Wind-Down** (`Moon`):
```typescript
vizData: (() => {
  const durationMin = Math.round((sleepTime.value.getTime() - windDownStart.value.getTime()) / 60_000)
  const h = Math.floor(durationMin / 60)
  const m = durationMin % 60
  return {
    supLabel: `${durationMin} MIN`,
    ringPct: Math.min(Math.round((durationMin / 180) * 100), 100),
    ringCenter: String(durationMin),
    ringUnit: 'MIN',
    stat1Label: 'Until sleep',
    stat1Value: h > 0 ? `${h}h ${m > 0 ? m + 'm' : ''}`.trim() : `${m}m`,
    stat2Label: 'Melatonin onset',
    stat2Value: fmt(melatoninOnset.value),
  }
})()
```

**Sleep Window** (`BedDouble`):
```typescript
vizData: (() => {
  const nadir = solar.nadir  // SunCalc nadir — confirmed present in useSolarStore
  const gapMs = nadir ? Math.abs(sleepTime.value.getTime() - nadir.getTime()) : 0
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
    stat2Value: nadir ? fmt(nadir) : '--:--',
  }
})()
```

Note: `solar.nadir` is the confirmed property name in `useSolarStore` (returned directly from SunCalc via `times.value.nadir`). SunCalc always returns a Date for nadir, but before geo resolves (lat/lng = 0/0) the value may be an unexpected epoch-adjacent Date — the defensive guard shown above is fine. `fmt` is already imported in `protocol.ts` as `fmtTime as fmt` from `@/lib/timezoneUtils`. All values (`wakeWindowTime`, `wakeWindowEnd`, `sleepTime`, `melatoninOnset`, `windDownStart`) are local `computed` refs inside the store function — they are in scope within `dailyProtocol`.

---

## 2. ProtocolTimeline.vue

Single addition — pass the new prop:

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

---

## 3. ProtocolCard.vue — Full Redesign

### Props

```typescript
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
```

Import `VizData` from `@/stores/protocol`.

### Theme (unchanged from current)

```typescript
const cardThemes: Record<string, string> = {
  Sunrise:   '#FFBD76',
  Sun:       '#E8C547',
  Brain:     '#9B8BFA',
  Coffee:    '#F08060',
  Moon:      '#5BBFD6',
  BedDouble: '#8899CC',
}
const theme = computed(() => cardThemes[props.icon] ?? '#FFBD76')
```

Remove all of: `windowRefMs`, `barPct`, `hasBar`, `tickFillMap`, `tickFilled`, `ticks`, `iconMap`, `iconComponent`, `isPassed`, `isActive`.

Keep: `theme`, `timeParts` (unchanged — `timeParts` is used in the Caffeine SVG to render the cutoff time inline).

### New computed

```typescript
const isCurveCard = computed(() =>
  ['Sun', 'Brain', 'Coffee'].includes(props.icon)
)
const isRingCard = computed(() =>
  ['Moon', 'BedDouble'].includes(props.icon)
)
const isArcCard = computed(() => props.icon === 'Sunrise')
```

### Unique gradient ID per instance

SVG `<defs>` IDs are global in the DOM. Because 6 cards render simultaneously, each must use unique gradient IDs to avoid collisions. Generate a per-instance suffix:

```typescript
const uid = Math.random().toString(36).slice(2, 6)
// Gradient IDs: `g-sun-${uid}`, `g-foc-${uid}`, `g-caf-${uid}`
// Reference in fill: `url(#g-sun-${uid})` etc. — use :id binding and string interpolation
```

In the template, bind `:id` on `<linearGradient>` elements and use `:fill="\`url(#g-sun-${uid})\`"` on the fill paths.

### Crosshair state (for curve cards)

```typescript
import { ref, computed } from 'vue'

const curveWrapRef = ref<HTMLElement | null>(null)
const crosshairX = ref(0)
const crosshairY = ref(0)
const crosshairVisible = ref(false)
```

Path data (hardcoded per card — these match the v6 bezier SVGs):

```typescript
const curvePathPoints: Record<string, [number, number][]> = {
  Sun: [[0,68],[18,65],[36,55],[55,40],[68,29],[80,19],[95,10],[108,3],[118,2],[125,3],[132,4],[145,10],[155,20],[168,33],[185,52],[200,64],[210,66],[216,68]],
  Brain: [[0,68],[20,66],[40,60],[60,46],[80,30],[100,14],[108,7],[114,3],[120,2],[125,2],[130,2],[136,4],[145,10],[155,18],[168,30],[180,46],[196,60],[210,66],[216,68]],
  Coffee: [[0,12],[40,12],[80,12],[88,12],[100,16],[115,25],[130,36],[148,48],[165,57],[185,63],[205,66],[216,68]],
}

const VB_W = 216, VB_H = 75

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
  const innerW = rect.width - PAD_L - 8
  const innerH = rect.height - PAD_T - 4
  const mx = e.clientX - rect.left - PAD_L
  const svgX = Math.max(0, Math.min(VB_W, (mx / innerW) * VB_W))
  const svgY = getYatX(curvePathPoints[props.icon] ?? [], svgX)
  crosshairX.value = mx + PAD_L
  crosshairY.value = (svgY / VB_H) * innerH + PAD_T
}
```

### Ring progress dashoffset

The rings use `stroke-dasharray="188.5"` (circumference of r=30 circle). Dashoffset = `188.5 * (1 - ringPct/100)`.

```typescript
const ringDashoffset = computed(() => {
  const pct = props.vizData?.ringPct ?? 0
  return 188.5 * (1 - pct / 100)
})
```

### Template structure

```html
<template>
  <div class="card" :class="{ 'card--passed': status === 'passed' }" :style="{ '--accent': theme }">

    <!-- Header -->
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

    <!-- Hero time -->
    <div class="card-time-wrap">
      <span class="t-h">{{ timeParts.h }}</span>
      <span class="t-sep">:</span>
      <span class="t-m">{{ timeParts.m }}</span>
      <span v-if="vizData?.supLabel" class="t-sup">{{ vizData.supLabel }}</span>
    </div>

    <!-- Viz pill -->
    <div class="pill-viz">

      <!-- Clock arc (Wake Window) -->
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

      <!-- Curve chart (Morning Light, Peak Focus, Caffeine Cutoff) -->
      <div
        v-else-if="isCurveCard"
        ref="curveWrapRef"
        class="pill-curve-wrap"
        @mousemove="onCurveMouseMove"
        @mouseenter="crosshairVisible = true"
        @mouseleave="crosshairVisible = false"
      >
        <div class="crosshair-line" :style="{ left: crosshairX + 'px', opacity: crosshairVisible ? 1 : 0 }" />
        <div class="crosshair-dot" :style="{ left: crosshairX + 'px', top: crosshairY + 'px', opacity: crosshairVisible ? 1 : 0 }" />

        <!-- Morning Light SVG -->
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

        <!-- Peak Focus SVG -->
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

        <!-- Caffeine Decay SVG -->
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
          <text x="65" y="74" font-size="7" :fill="theme" font-family="'JetBrains Mono',monospace">{{ timeParts.h }}:{{ timeParts.m }}</text>
          <text x="175" y="50" font-size="7" fill="rgba(255,246,233,0.22)" font-family="'JetBrains Mono',monospace">BED</text>
        </svg>
      </div>

      <!-- Ring (Wind-Down, Sleep Window) -->
      <div v-else-if="isRingCard" class="pill-data-wrap">
        <svg width="64" height="64" viewBox="0 0 76 76" style="flex-shrink:0">
          <circle cx="38" cy="38" r="30" fill="none" stroke="rgba(255,246,233,0.08)" stroke-width="5.5"/>
          <circle cx="38" cy="38" r="30" fill="none" :stroke="theme" stroke-width="5.5"
            stroke-dasharray="188.5" :stroke-dashoffset="ringDashoffset"
            stroke-linecap="round" transform="rotate(-90 38 38)"/>
          <text x="38" y="35" text-anchor="middle" font-size="13" font-weight="800" fill="#FFF6E9" font-family="'JetBrains Mono',monospace">{{ vizData?.ringCenter }}</text>
          <text x="38" y="47" text-anchor="middle" font-size="5.5" fill="rgba(255,246,233,0.35)" font-family="'JetBrains Mono',monospace">{{ vizData?.ringUnit }}</text>
        </svg>
        <div class="pill-stats">
          <div v-if="vizData?.stat1Label">
            <div class="pill-lbl">{{ vizData.stat1Label }}</div>
            <div class="pill-val-a">{{ vizData.stat1Value }}</div>
          </div>
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

### CSS (scoped)

Key rules — implement exactly as in v6 mockup:

```css
.card {
  display: flex; flex-direction: column;
  padding: 1rem; gap: 0.6rem;
  border-radius: 14px;
  background: color-mix(in srgb, var(--accent) 12%, #07111a);
  /* No border, no ::before accent bar */
}
.card--passed { opacity: 0.3; }

/* Header */
.card-header { display: flex; align-items: center; justify-content: space-between; }
.card-label-group { display: flex; align-items: center; gap: 0.35rem; }
.card-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }
.card-label {
  font-size: 0.48rem; font-weight: 700; letter-spacing: 0.2em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--accent) 85%, #FFF6E9);
}

/* Status pill */
.status-pill {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 0.2rem 0.5rem 0.2rem 0.38rem;
  border-radius: 999px; font-size: 0.38rem; font-weight: 700;
  letter-spacing: 0.1em; text-transform: uppercase;
}
.sdot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.pill-upcoming { background: rgba(255,246,233,0.08); color: rgba(255,246,233,0.45); }
.pill-upcoming .sdot { background: rgba(255,246,233,0.3); }
.pill-active   { background: rgba(0,212,170,0.12); color: #00D4AA; }
.pill-active   .sdot { background: #00D4AA; box-shadow: 0 0 4px rgba(0,212,170,0.8); animation: blink 2s ease-in-out infinite; }
.pill-passed   { background: rgba(255,68,68,0.1); color: rgba(255,68,68,0.75); }
.pill-passed   .sdot { background: #FF4444; }
@keyframes blink { 0%,100% { opacity:1 } 50% { opacity:0.35 } }

/* Hero time */
.card-time-wrap { display: flex; align-items: baseline; line-height: 1; }
.t-h, .t-m { font-size: 2.5rem; font-weight: 800; letter-spacing: -0.04em; color: #FFF6E9; }
.t-sep { font-size: 2.5rem; font-weight: 200; letter-spacing: -0.04em; color: #FFF6E9; opacity: 0.18; margin: 0 0.5px; }
.t-sup {
  font-size: 0.65rem; font-weight: 500; letter-spacing: 0.04em;
  color: rgba(255,246,233,0.35); margin-left: 0.35rem;
  align-self: flex-start; padding-top: 0.4rem;
}

/* Viz pill container */
.pill-viz { border-radius: 10px; background: color-mix(in srgb, var(--accent) 20%, #04090d); overflow: hidden; }

/* Curve wrap */
.pill-curve-wrap {
  height: 76px; display: flex; align-items: stretch;
  padding: 0.45rem 0.55rem 0.28rem; position: relative; cursor: crosshair;
}
.pill-curve-wrap svg { width: 100%; height: 100%; display: block; }

/* Crosshair */
.crosshair-line {
  position: absolute; top: 7px; bottom: 7px; width: 1px;
  background: rgba(255,246,233,0.35); pointer-events: none; transition: opacity 0.1s;
}
.crosshair-dot {
  position: absolute; width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent); border: 1.5px solid #FFF6E9;
  transform: translate(-50%, -50%); pointer-events: none; transition: opacity 0.1s;
}

/* Data rows (arc + ring cards) */
.pill-data-wrap { display: flex; align-items: center; gap: 0.85rem; padding: 0.65rem 0.8rem; }
.pill-stats { display: flex; flex-direction: column; gap: 0.35rem; }
.pill-lbl { font-size: 0.34rem; letter-spacing: 0.14em; text-transform: uppercase; color: color-mix(in srgb, var(--accent) 55%, rgba(255,246,233,0.25)); margin-bottom: 0.04rem; }
/* pill-val = white (secondary stat); pill-val-a = accent colour (primary stat — e.g. "1.5h until sleep") */
.pill-val   { font-size: 0.95rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1; color: #FFF6E9; }
.pill-val-a { font-size: 1.05rem; font-weight: 800; letter-spacing: -0.04em; line-height: 1; color: var(--accent); }

/* Footer */
.card-desc { font-family: var(--font-body); font-size: 0.5rem; color: rgba(255,246,233,0.52); line-height: 1.55; }
.card-cite { font-size: 0.36rem; color: rgba(255,246,233,0.18); }
```

**Important CSS note:** Use scoped CSS only — no Tailwind arbitrary values. The existing `color-mix()` usage is fine as it's in scoped styles, not Tailwind classes.

---

## 4. Template note — `icon` in template vs `props.icon` in script

In Vue 3 `<script setup>`, the template has implicit access to all props by name (i.e. `icon` in the template is the same as `props.icon`). The script side must use `props.icon`. The spec uses `props.icon` in script functions (`onCurveMouseMove`, `curvePathPoints` lookup) and bare `icon` in template conditions (`v-if="icon === 'Sun'"`). Both are correct — do not "fix" them to be consistent.

---

## 5. Verification Checklist

1. `npm run build` — zero TypeScript errors
2. All 6 cards render with correct accent colours
3. No left accent bar (`::before`), no card border
4. Status pills show correct colour: green (active), red (passed), muted (upcoming)
5. Wake Window shows clock arc + window/sleep stats
6. Morning Light, Peak Focus, Caffeine Cutoff show SVG curves; hover crosshair tracks mouse
7. Wind-Down shows ring + stats (duration, melatonin onset)
8. Sleep Window shows ring + stats (alignment %, solar gap, solar midnight)
9. Passed cards dim to 0.3 opacity
10. Responsive breakpoints intact (900px → 2-col, 500px → 1-col) — no changes needed in ProtocolTimeline.vue grid
