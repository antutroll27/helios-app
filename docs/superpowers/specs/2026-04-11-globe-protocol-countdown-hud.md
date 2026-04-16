# Globe Protocol Countdown HUD — Spec

## Goal

Replace the static DESTINATIONS comparison rail (`GlobeComparisonHud.vue`) with a dual-mode Protocol Countdown card that shows actionable real-time circadian data by default, and swaps to destination comparison when a city is selected from the globe.

## Context

The globe panel (`HeliosGlobePanel.vue`) currently has two overlays:
- **Left** — header (HELIOS · COBE, Orbital View, route) + `GlobeOrbitalContext.vue` (solar elevation card)
- **Right** — `GlobeComparisonHud.vue` (DESTINATIONS rail: Tokyo, London, NYC with timezone delta and travel readiness), plus a mobile-only pill toggle button

The destinations rail only has value when the user is actively planning travel. For the majority of sessions — users living their daily circadian routine — it answers a question they aren't asking.

Research evidence (Rise Science, Timeshifter UX, PubMed 38668986) shows that **time-relative, event-countdown framing** ("Peak Focus in 23 min") is significantly more actionable than informational metric displays. All data needed to compute this is already available in `useProtocolStore` and `useSolarStore` — no backend or new API calls required.

## Files to Modify

| File | Change |
|---|---|
| `src/components/globe/GlobeProtocolCountdown.vue` | **Create** — new dual-mode card component |
| `src/components/globe/HeliosGlobePanel.vue` | Add `GlobeProtocolCountdown` to left overlay; remove right overlay, `GlobeComparisonHud`, mobile pill, and all associated refs/handlers |
| `src/stores/protocol.ts` | Export `wakeWindowTime` from the store's `return` block |
| `src/composables/useCobeGlobeData.ts` | Change initial `selectedDestinationId` to `null` so countdown card shows by default |
| `src/pages/HomePage.vue` | Increase `.data-section` `margin-top` to push stat strip further below globe |

`GlobeComparisonHud.vue` is **not deleted** from disk (keep for reference) but is no longer imported or rendered.

---

## Section 1 — protocol.ts: Export wakeWindowTime

In the `return` block of `useProtocolStore`, add `wakeWindowTime`:

```typescript
return {
  caffeineHalfLifeHours,
  sleepTime,
  melatoninOnset,
  wakeWindowTime,       // ← add this line
  caffeineCutoff,
  peakFocusStart,
  peakFocusEnd,
  windDownStart,
  solarAlignmentGapMinutes,
  morningLightDurationMin,
  dailyProtocol,
}
```

No other changes to `protocol.ts`.

---

## Section 2 — useCobeGlobeData.ts: Null initial selection + clearDestination

**Change 1 — null initial value.** Find the line (around line 189–191) that reads:

```typescript
const selectedDestinationId = shallowRef<string | null>(getInitialSelectedDestinationId(destinations.value))
```

Replace the entire initializer call with `null`:

```typescript
const selectedDestinationId = shallowRef<string | null>(null)
```

The `getInitialSelectedDestinationId` function can be left in place (or removed if unused elsewhere); only the call site changes.

**Change 2 — add `clearDestination`.** `selectedDestinationId` is exposed as `readonly` from the composable, so external code cannot set `.value` directly. Add a companion function inside `useCobeGlobeData` and export it:

```typescript
function clearDestination() {
  selectedDestinationId.value = null
}
```

Add `clearDestination` to the composable's `return` object alongside `selectDestination`.

This ensures `selectedComparison` is `null` on first load so the new card opens in countdown mode. Globe marker clicks still set a destination ID as before — that behaviour is unchanged.

---

## Section 3 — GlobeProtocolCountdown.vue (new component)

### Props and emits

```typescript
interface Props {
  selectedComparison?: GlobeComparison | null
  comparisons: GlobeComparison[]        // for the destination chip row
}

const emit = defineEmits<{
  'select-destination': [id: string | null]
}>()
```

`GlobeComparison` is the existing type from `useCobeGlobeData`. Import with:
```typescript
import type { GlobeComparison } from '@/composables/useCobeGlobeData'
```

### Script — Composable dependencies

```typescript
import { computed } from 'vue'
import { useProtocolStore } from '@/stores/protocol'
import { useSolarStore } from '@/stores/solar'

const protocol = useProtocolStore()
const solar = useSolarStore()
```

### Script — Protocol items as array

`dailyProtocol` is a keyed `DailyProtocol` object. Convert to array for all computeds:

```typescript
const protocolItems = computed(() =>
  Object.values(protocol.dailyProtocol).sort((a, b) => a.time.getTime() - b.time.getTime())
)
```

Sorting by `time` is explicit and correct regardless of key-insertion order in `DailyProtocol`.

### Script — Computeds

**`nextEvent`** — first item whose `time` is in the future:

```typescript
const nextEvent = computed(() => {
  const now = solar.now.getTime()
  return protocolItems.value.find(item => item.time.getTime() > now) ?? null
})
```

**`eventQueue`** — next 2 items after `nextEvent`:

```typescript
const eventQueue = computed(() => {
  if (!nextEvent.value) return []
  const now = solar.now.getTime()
  return protocolItems.value
    .filter(item => item.time.getTime() > now && item !== nextEvent.value)
    .slice(0, 2)
})
```

**`countdownMinutes`** — minutes until next event, floored, minimum 0:

```typescript
const countdownMinutes = computed(() => {
  if (!nextEvent.value) return 0
  return Math.max(0, Math.floor((nextEvent.value.time.getTime() - solar.now.getTime()) / 60000))
})
```

**`countdownDisplay`** — split into `value` and `unit` for mixed-weight typography:

```typescript
const countdownDisplay = computed(() => {
  const m = countdownMinutes.value
  if (m < 60) return { value: String(m), unit: 'min' }
  const h = Math.floor(m / 60)
  const rem = m % 60
  return { value: `${h}h`, unit: rem > 0 ? `${rem}m` : '' }
})
```

Rendered in template as two inline spans: `<span class="cd-num">{{ countdownDisplay.value }}</span><span class="cd-unit">{{ countdownDisplay.unit }}</span>` — baseline-aligned via flex.

**`progressPct`** — percentage of current inter-event window elapsed (0–100), drives the bar fill:

```typescript
const progressPct = computed(() => {
  if (!nextEvent.value) return 100
  const now = solar.now.getTime()
  const allTimes = protocolItems.value.map(i => i.time.getTime()).sort((a, b) => a - b)
  const nextT = nextEvent.value.time.getTime()
  const prevTimes = allTimes.filter(t => t <= now)
  const prevT = prevTimes.length > 0 ? prevTimes[prevTimes.length - 1] : allTimes[0]
  const window = nextT - prevT
  if (window <= 0) return 0
  return Math.min(100, Math.round(((now - prevT) / window) * 100))
})
```

**`hoursAwake`** — hours elapsed since `wakeWindowTime` (now exported from protocol store):

```typescript
const hoursAwake = computed(() => {
  const wakeMs = protocol.wakeWindowTime.getTime()
  const nowMs = solar.now.getTime()
  return Math.max(0, (nowMs - wakeMs) / 3600000)
})
```

**`napWindowOpen`** — true when nap conditions are met:

```typescript
const napWindowOpen = computed(() => {
  const h = solar.now.getHours()
  return hoursAwake.value >= 6 && hoursAwake.value <= 9 && h >= 12 && h < 15
})
```

### Template — Default mode (countdown)

When `props.selectedComparison` is `null` or `undefined`:

```
┌─────────────────────────────────────────┐
│ NEXT EVENT                    ● LIVE    │  chip + live dot
│                                         │
│ Coming up                               │  event sub-label
│ Peak Focus                              │  event name (1.02rem, weight 700)
│ 23 min                                  │  hero: value (2.4rem) + unit (0.88rem)
│ [████████████░░░░░░░░░░░░░░░░░░░░░░]   │  4px progress bar
│ ─────────────────────────────────────   │  hairline
│ Caffeine Cutoff              2h 14m     │  queue row 1
│ Wind-Down                    5h 40m     │  queue row 2
│ ● Nap Window Open · 20 min             │  nap badge (teal pill, conditional)
│ ─────────────────────────────────────   │  hairline
│ [Tokyo]  [London]  [NYC]               │  destination chips (one per comparison)
└─────────────────────────────────────────┘
```

**Destination chip row** (always visible in default mode, below nap badge):
- One chip per item in `props.comparisons`
- Chip: `0.38rem` mono, weight `700`, `letter-spacing: 0.12em`, `padding: 0.16rem 0.38rem`, `border-radius: 20px`
- Resting style: `background: rgba(155,139,250,0.1)`, `border: 1px solid rgba(155,139,250,0.18)`, `color: rgba(200,190,250,0.65)`
- On click: `emit('select-destination', comparison.id)`

### Template — Comparison mode

When `props.selectedComparison` is non-null, replace the countdown interior with destination data. The card has **no city-selection UI** — it is display-only, driven entirely by globe marker clicks. Content:

```
┌─────────────────────────────────────────┐
│ DESTINATION              ● ACTIVE       │  chip + active pill (if selected)
│                                         │
│ Tokyo                         +5.5h     │  city name (0.9rem 700) + tz delta (#FFBD76)
│ ─────────────────────────────────────   │  hairline
│ Day — High Sun                          │  destination solar phase (derived inline)
│ Moderate shift. Plan light timing…      │  travelReadiness string (0.46rem muted)
│                                     ✕  │  dismiss button (top-right corner)
└─────────────────────────────────────────┘
```

**Dismiss button** (comparison mode only): small `✕` button positioned `top-right` inside the card. On click: `emit('select-destination', null)` — returns the card to countdown mode.

Use `selectedComparison.label`, `selectedComparison.timezoneDeltaHours` (formatted with sign), and `selectedComparison.travelReadiness`.

`GlobeComparison` has no `destinationSolarPhase` field — derive it inline from `destinationElevationDeg` via a computed:

```typescript
const destSolarPhase = computed(() => {
  const deg = props.selectedComparison?.destinationElevationDeg ?? 0
  if (deg > 20) return 'Day — High Sun'
  if (deg > 6) return 'Day — Low Angle'
  if (deg > 0) return 'Civil Twilight'
  return 'Night'
})
```

### Visual Design

**Card shell (both modes):**
- `background: color-mix(in srgb, #9B8BFA 18%, #07111a)` — soft violet tint, fully opaque
- `border-radius: 1rem`
- `padding: 1rem 1rem 0.9rem`
- No `border-left` bar, no `backdrop-filter`, no `::before`

**Top row:**
- Chip: `NEXT EVENT` / `DESTINATION` — `0.46rem` JetBrains Mono, weight `700`, `letter-spacing: 0.18em`, `color: rgba(200,190,250,0.62)`
- Live indicator (default mode): green dot `#00D4AA` (5px, `box-shadow: 0 0 5px #00D4AA`) + `LIVE` label — `0.42rem` mono, `color: #00D4AA`
- Active pill (comparison mode): `background: rgba(0,212,170,0.12)`, `border: 1px solid rgba(0,212,170,0.22)`, `color: #00D4AA`, `0.4rem` mono, `border-radius: 20px`

**Event name (default):** `1.02rem` Plus Jakarta Sans, weight `700`, `color: rgba(255,245,225,0.95)`

**Hero countdown (default):**
- Value span `.cd-num`: `2.4rem` JetBrains Mono, weight `800`, `letter-spacing: -0.04em`, `color: rgba(255,245,225,0.97)`
- Unit span `.cd-unit`: `0.88rem` mono, weight `600`, `color: rgba(200,190,250,0.55)`, `padding-bottom: 0.2rem`, baseline-aligned

**Progress bar:**
- Track: `height: 4px`, `border-radius: 2px`, `background: rgba(155,139,250,0.1)`, `margin-bottom: 0.58rem`, `overflow: hidden`
- Fill: `background: linear-gradient(90deg, rgba(155,139,250,0.4), #9B8BFA)`, `width: progressPct + '%'`, `transition: width 1.2s ease`

**Hairline:** `height: 1px`, `background: rgba(155,139,250,0.12)`, `margin-bottom: 0.52rem`

**Queue rows:**
- Container: `display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.48rem`
- Name: `0.55rem` mono, weight `600`, `color: rgba(255,245,225,0.68)`
- Time: `0.52rem` mono, weight `600`, `color: rgba(200,190,250,0.48)`

**Nap badge** (only rendered when `napWindowOpen` is `true`):
- `background: rgba(0,212,170,0.1)`, `border: 1px solid rgba(0,212,170,0.22)`, `color: #00D4AA`
- `0.42rem` mono, weight `700`, `letter-spacing: 0.12em`, `border-radius: 20px`, `padding: 0.2rem 0.46rem`
- Content: dot span + `Nap Window Open · 20 min`

---

## Section 4 — HeliosGlobePanel.vue Changes

### Remove the right overlay entirely

Delete from `<template>`:
```html
<div class="globe-panel__overlay globe-panel__overlay--rail">
  <GlobeComparisonHud ... />
</div>

<button v-if="isMobile" class="globe-panel__dest-pill font-mono" ...>
  ...
</button>
```

Delete from `<script setup>`:
- `import GlobeComparisonHud from './GlobeComparisonHud.vue'`
- `const showRail = ref(false)`
- `const isMobile = ref(false)`
- `const handleResize = () => { ... }`
- `onMounted(() => { ... window.addEventListener ... })`
- `onUnmounted(() => { ... window.removeEventListener ... })`
- `function toggleRail() { ... }`
- `function onDestinationSelect(id: string) { ... }` — **delete this function entirely**

`HeliosCobeGlobe` emits `select-destination` up to `HeliosGlobePanel`. Currently this is caught by `onDestinationSelect` (which called `selectDestination` + reset `showRail`). With `showRail` gone, wire it inline directly on `<HeliosCobeGlobe>` in the template:

```html
<HeliosCobeGlobe
  class="globe-panel__globe"
  :current="currentSnapshot"
  :comparisons="comparisons"
  :selected-destination-id="selectedDestinationId"
  @select-destination="selectDestination"
/>
```

`selectDestination` is already destructured from `useCobeGlobeData()` at the top of the script — no new import needed.

Delete from `<style scoped>`:
- `.globe-panel__overlay--rail { ... }` (all breakpoints: base, 1100px, 720px, 600px)
- `.globe-panel__dest-pill { ... }`
- `.globe-panel__dest-pill-dot { ... }`
- `@media (min-width: 601px) { .globe-panel__dest-pill { display: none; } }`
- The `@media (max-width: 600px)` comment block "Comparison HUD — repositioned above pill when open"

### Add GlobeProtocolCountdown to left overlay

Import at top of `<script setup>`:
```typescript
import GlobeProtocolCountdown from './GlobeProtocolCountdown.vue'
```

In `<script setup>`, destructure `clearDestination` from `useCobeGlobeData()` alongside the existing destructured values, then add a handler:

```typescript
const {
  currentSnapshot,
  localSolar,
  comparisons,
  selectedComparison,
  selectedDestinationId,
  orbitalContext,
  selectDestination,
  clearDestination,     // ← add this
} = useCobeGlobeData()

function handleDestSelect(id: string | null) {
  if (id === null) {
    clearDestination()       // uses the composable's internal ref — no readonly violation
  } else {
    selectDestination(id)
  }
}
```

In `<template>`, inside `.globe-panel__intro-slab`, after `<GlobeOrbitalContext>`:
```html
<GlobeProtocolCountdown
  :selected-comparison="selectedComparison"
  :comparisons="comparisons"
  @select-destination="handleDestSelect"
/>
```

`selectedComparison` and `comparisons` are already destructured from `useCobeGlobeData()`.

Do **not** add `@select-destination` to `<HeliosCobeGlobe>` — the globe canvas does not emit this event and no click-to-select logic exists there. The `<HeliosCobeGlobe>` binding is otherwise unchanged.

---

## Section 5 — HomePage.vue Layout Change

In `<style scoped>`, update `.data-section`:

```css
.data-section {
  margin-top: 2.5rem;  /* was 0.5rem */
}
```

This pushes SpaceWeatherGauge, SocialJetLagScore, and EnvironmentBadge further below the globe for visual breathing room.

---

## What Does Not Change

- `GlobeOrbitalContext.vue` — untouched
- `HeliosCobeGlobe.vue` — untouched; globe marker click logic already calls `selectDestination` from `useCobeGlobeData`, setting `selectedDestinationId` reactively
- `GlobeStatStrip.vue` — untouched
- `useCobeGlobeData.ts` — only `selectedDestinationId` initial value changes; all other reactive values, `selectDestination`, `comparisons`, `selectedComparison` are unchanged
- Protocol card grid, stat strip, chat — untouched

---

## Verification

1. `npm run build` — zero TypeScript errors
2. **Default state** (no city selected, page first load): soft violet countdown card appears below solar elevation card; hero shows minutes until next protocol event; queue shows 2 upcoming events; no destinations rail visible on right
3. **Comparison mode**: click a globe marker (Tokyo/London/NYC) → countdown card swaps to destination info (city name, timezone delta, solar phase, travel readiness string)
4. Click same marker again to deselect → card reverts to countdown
5. **Nap badge**: at 13:00–15:00 with `hoursAwake >= 6 && <= 9` → teal nap badge appears; outside that window → absent
6. **Progress bar**: fills proportionally to time elapsed in current inter-event window; transitions smoothly on solar.now tick
7. **Stat strip**: sits noticeably further below the globe than before (2.5rem gap vs 0.5rem)
8. **No orphaned code**: `showRail`, `isMobile`, `handleResize`, `toggleRail` are gone from `HeliosGlobePanel.vue`; `wakeWindowTime` appears in protocol store return
9. `countdownMinutes` decrements in real time — `solar.now` ticks every 60 seconds
