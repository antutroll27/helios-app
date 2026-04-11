# Globe Protocol Countdown HUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the static DESTINATIONS comparison rail with a dual-mode Protocol Countdown card that shows the next circadian event by default, and swaps to destination comparison when a globe marker is clicked.

**Architecture:** Five targeted file edits — export one missing store value, change one composable initialiser and add a mutation function, create the new card component, refactor the globe panel to remove dead code and wire the new card, then bump one CSS margin. No new stores, no new API calls, no routing changes.

**Tech Stack:** Vue 3 `<script setup>` + TypeScript, Pinia stores, scoped CSS (no arbitrary Tailwind bracket values), SunCalc (via existing composable), `color-mix()` for tinted backgrounds.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/stores/protocol.ts` | Modify (line 270–282) | Export `wakeWindowTime` computed so card can read wake time |
| `src/composables/useCobeGlobeData.ts` | Modify (lines 189–191, 238–254) | Null initial selection; add `clearDestination()` mutation |
| `src/components/globe/GlobeProtocolCountdown.vue` | **Create** | Dual-mode card — countdown default, comparison on city select |
| `src/components/globe/HeliosGlobePanel.vue` | Modify (full file) | Remove right overlay + mobile pill dead code; add new card |
| `src/pages/HomePage.vue` | Modify (line 141) | Push stat strip further below globe (margin-top 0.5rem → 2.5rem) |

---

## Task 1: Export `wakeWindowTime` from protocol store

**Files:**
- Modify: `src/stores/protocol.ts:270-282`

`wakeWindowTime` is already computed at line 68 of `protocol.ts` but is missing from the `return` block (lines 270–282). The new card needs it to calculate `hoursAwake`.

- [ ] **Step 1: Add `wakeWindowTime` to the return block**

Open `src/stores/protocol.ts`. The current return block (lines 270–282) reads:

```typescript
  return {
    caffeineHalfLifeHours,
    sleepTime,
    melatoninOnset,
    caffeineCutoff,
    peakFocusStart,
    peakFocusEnd,
    windDownStart,
    solarAlignmentGapMinutes,
    morningLightDurationMin,
    dailyProtocol,
  }
```

Replace with:

```typescript
  return {
    caffeineHalfLifeHours,
    sleepTime,
    melatoninOnset,
    wakeWindowTime,
    caffeineCutoff,
    peakFocusStart,
    peakFocusEnd,
    windDownStart,
    solarAlignmentGapMinutes,
    morningLightDurationMin,
    dailyProtocol,
  }
```

- [ ] **Step 2: Verify build succeeds**

```bash
cd helios-app && npm run build
```

Expected: zero TypeScript errors. If you see `Property 'wakeWindowTime' does not exist`, re-check the edit landed in the `return` block, not inside a computed.

- [ ] **Step 3: Commit**

```bash
git add src/stores/protocol.ts
git commit -m "feat(protocol): export wakeWindowTime from store return block"
```

---

## Task 2: Update `useCobeGlobeData.ts` — null initial selection + `clearDestination`

**Files:**
- Modify: `src/composables/useCobeGlobeData.ts:189-191` (initial value)
- Modify: `src/composables/useCobeGlobeData.ts:238-254` (add function + export)

Currently `selectedDestinationId` initialises to `destinations[0]?.id` (Tokyo), which means the panel opens in comparison mode instead of countdown mode. Also, `selectedDestinationId` is exposed as `readonly` — external code cannot set `.value` directly, so we need an internal mutation function.

- [ ] **Step 1: Change the initial value to `null`**

In `src/composables/useCobeGlobeData.ts`, find lines 189–191:

```typescript
  const selectedDestinationId = shallowRef<string | null>(
    getInitialSelectedDestinationId(destinations.value),
  )
```

Replace with:

```typescript
  const selectedDestinationId = shallowRef<string | null>(null)
```

Leave `getInitialSelectedDestinationId` in place — it is exported and may be used in tests.

- [ ] **Step 2: Add `clearDestination` function**

In the same file, the existing `selectDestination` function is at lines 238–242:

```typescript
  function selectDestination(destinationId: string) {
    if (destinations.value.some((destination) => destination.id === destinationId)) {
      selectedDestinationId.value = destinationId
    }
  }
```

Add `clearDestination` immediately after it:

```typescript
  function clearDestination() {
    selectedDestinationId.value = null
  }
```

- [ ] **Step 3: Export `clearDestination` from the return object**

The current return block starts at line 244 and ends at line 254:

```typescript
  return {
    currentSnapshot,
    destinations: readonly(destinations),
    localSolar,
    comparisons,
    selectedDestinationId: readonly(selectedDestinationId),
    selectedDestination,
    selectedComparison,
    orbitalContext,
    selectDestination,
  }
```

Add `clearDestination` to the return:

```typescript
  return {
    currentSnapshot,
    destinations: readonly(destinations),
    localSolar,
    comparisons,
    selectedDestinationId: readonly(selectedDestinationId),
    selectedDestination,
    selectedComparison,
    orbitalContext,
    selectDestination,
    clearDestination,
  }
```

- [ ] **Step 4: Verify build succeeds**

```bash
npm run build
```

Expected: zero TypeScript errors. If you see a readonly assignment error, confirm the `clearDestination` function is inside `useCobeGlobeData` (before the `return`), not outside it.

- [ ] **Step 5: Commit**

```bash
git add src/composables/useCobeGlobeData.ts
git commit -m "feat(globe): null initial destination selection + add clearDestination()"
```

---

## Task 3: Create `GlobeProtocolCountdown.vue`

**Files:**
- Create: `src/components/globe/GlobeProtocolCountdown.vue`

This is the core new component. It has two modes controlled by a single prop:
- **Default (countdown):** shows the next circadian protocol event with hero countdown, progress bar, 2-item event queue, conditional nap badge, and destination chip row
- **Comparison:** shows the selected city's timezone delta, derived solar phase, and travel readiness string, plus a dismiss button

**Important constraints (do not break these):**
- `dailyProtocol` is a `DailyProtocol` keyed object — use `Object.values()` before array methods
- `solar.now` ticks every 60 s — all time computeds depend on it reactively
- `GlobeComparison` has no `destinationSolarPhase` field — derive it from `destinationElevationDeg`
- No arbitrary Tailwind bracket values — use only scoped CSS for component-specific values

- [ ] **Step 1: Create the file with imports, props, and stores**

Create `src/components/globe/GlobeProtocolCountdown.vue` with this `<script setup>` block:

```typescript
<script setup lang="ts">
import { computed } from 'vue'
import type { GlobeComparison } from '@/composables/useCobeGlobeData'
import { useProtocolStore } from '@/stores/protocol'
import { useSolarStore } from '@/stores/solar'

interface Props {
  selectedComparison?: GlobeComparison | null
  comparisons: GlobeComparison[]
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'select-destination': [id: string | null] }>()

const protocol = useProtocolStore()
const solar = useSolarStore()
</script>
```

- [ ] **Step 2: Add the protocol computeds**

Append inside `<script setup>`, after the store assignments:

```typescript
// Convert DailyProtocol keyed object to sorted array — .find()/.filter() require an array
const protocolItems = computed(() =>
  Object.values(protocol.dailyProtocol).sort((a, b) => a.time.getTime() - b.time.getTime())
)

// First upcoming protocol event
const nextEvent = computed(() => {
  const now = solar.now.getTime()
  return protocolItems.value.find(item => item.time.getTime() > now) ?? null
})

// Next 2 events after nextEvent (shown in queue)
const eventQueue = computed(() => {
  if (!nextEvent.value) return []
  const now = solar.now.getTime()
  return protocolItems.value
    .filter(item => item.time.getTime() > now && item !== nextEvent.value)
    .slice(0, 2)
})

// Minutes until next event, floored, minimum 0
const countdownMinutes = computed(() => {
  if (!nextEvent.value) return 0
  return Math.max(0, Math.floor((nextEvent.value.time.getTime() - solar.now.getTime()) / 60000))
})

// Split into value + unit for mixed-weight typography
const countdownDisplay = computed(() => {
  const m = countdownMinutes.value
  if (m < 60) return { value: String(m), unit: 'min' }
  const h = Math.floor(m / 60)
  const rem = m % 60
  return { value: `${h}h`, unit: rem > 0 ? `${rem}m` : '' }
})

// Percentage of current inter-event window elapsed, drives bar fill
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

// Hours elapsed since wake — drives nap window logic
const hoursAwake = computed(() => {
  const wakeMs = protocol.wakeWindowTime.getTime()
  const nowMs = solar.now.getTime()
  return Math.max(0, (nowMs - wakeMs) / 3600000)
})

// Nap window: 6–9 h after wake AND between 12:00–15:00 local time
const napWindowOpen = computed(() => {
  const h = solar.now.getHours()
  return hoursAwake.value >= 6 && hoursAwake.value <= 9 && h >= 12 && h < 15
})

// Format timezone delta with sign (e.g. "+5.5h" or "-3h")
const tzDeltaLabel = computed(() => {
  const delta = props.selectedComparison?.timezoneDeltaHours ?? 0
  const sign = delta >= 0 ? '+' : ''
  return `${sign}${delta}h`
})

// Queue item countdown label (hours+minutes until that event)
function queueMinLabel(item: { time: Date }): string {
  const m = Math.max(0, Math.floor((item.time.getTime() - solar.now.getTime()) / 60000))
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  const rem = m % 60
  return rem > 0 ? `${h}h ${rem}m` : `${h}h`
}

// Derive solar phase from elevation — GlobeComparison has no destinationSolarPhase field
const destSolarPhase = computed(() => {
  const deg = props.selectedComparison?.destinationElevationDeg ?? 0
  if (deg > 20) return 'Day — High Sun'
  if (deg > 6) return 'Day — Low Angle'
  if (deg > 0) return 'Civil Twilight'
  return 'Night'
})
```

- [ ] **Step 3: Add the template**

Add after `</script>`:

```html
<template>
  <div class="pcd-card">

    <!-- ── COMPARISON MODE ──────────────────────────────────────── -->
    <template v-if="props.selectedComparison">
      <div class="pcd-row pcd-row--space">
        <span class="pcd-chip">DESTINATION</span>
        <span class="pcd-active-pill">● ACTIVE</span>
      </div>

      <div class="pcd-city-row">
        <span class="pcd-city-name">{{ props.selectedComparison.label }}</span>
        <span class="pcd-tz-delta">{{ tzDeltaLabel }}</span>
      </div>

      <div class="pcd-hairline" />

      <p class="pcd-solar-phase">{{ destSolarPhase }}</p>
      <p class="pcd-travel-readiness">{{ props.selectedComparison.travelReadiness }}</p>

      <button
        class="pcd-dismiss"
        type="button"
        aria-label="Return to countdown"
        @click="emit('select-destination', null)"
      >✕</button>
    </template>

    <!-- ── COUNTDOWN MODE (default) ────────────────────────────── -->
    <template v-else>
      <div class="pcd-row pcd-row--space">
        <span class="pcd-chip">NEXT EVENT</span>
        <span class="pcd-live">
          <span class="pcd-live-dot" aria-hidden="true" />
          LIVE
        </span>
      </div>

      <template v-if="nextEvent">
        <p class="pcd-coming-up">Coming up</p>
        <p class="pcd-event-name">{{ nextEvent.title }}</p>

        <div class="pcd-hero">
          <span class="cd-num">{{ countdownDisplay.value }}</span>
          <span class="cd-unit">{{ countdownDisplay.unit }}</span>
        </div>

        <!-- Progress bar -->
        <div class="pcd-bar-track">
          <div class="pcd-bar-fill" :style="{ width: progressPct + '%' }" />
        </div>
      </template>
      <p v-else class="pcd-event-name">All events passed</p>

      <div class="pcd-hairline" />

      <!-- Event queue -->
      <div v-if="eventQueue.length" class="pcd-queue">
        <div v-for="item in eventQueue" :key="item.key" class="pcd-queue-row">
          <span class="pcd-queue-name">{{ item.title }}</span>
          <span class="pcd-queue-time">{{ queueMinLabel(item) }}</span>
        </div>
      </div>

      <!-- Nap badge (conditional) -->
      <div v-if="napWindowOpen" class="pcd-nap-badge">
        <span class="pcd-nap-dot" aria-hidden="true" />
        Nap Window Open · 20 min
      </div>

      <div class="pcd-hairline" />

      <!-- Destination chips -->
      <div class="pcd-chips">
        <button
          v-for="comp in props.comparisons"
          :key="comp.id"
          class="pcd-dest-chip"
          type="button"
          @click="emit('select-destination', comp.id)"
        >
          {{ comp.label }}
        </button>
      </div>
    </template>

  </div>
</template>
```

- [ ] **Step 4: Add scoped styles**

Add after `</template>`:

```html
<style scoped>
/* Card shell */
.pcd-card {
  position: relative;
  background: color-mix(in srgb, #9B8BFA 18%, #07111a);
  border-radius: 1rem;
  padding: 1rem 1rem 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Header row */
.pcd-row {
  display: flex;
  align-items: center;
  margin-bottom: 0.52rem;
}
.pcd-row--space {
  justify-content: space-between;
}

/* Label chip */
.pcd-chip {
  font-family: var(--font-mono);
  font-size: 0.46rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(200, 190, 250, 0.62);
}

/* Live indicator */
.pcd-live {
  display: flex;
  align-items: center;
  gap: 0.28rem;
  font-family: var(--font-mono);
  font-size: 0.42rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: #00D4AA;
}
.pcd-live-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #00D4AA;
  box-shadow: 0 0 5px #00D4AA;
  flex-shrink: 0;
}

/* Active pill (comparison mode) */
.pcd-active-pill {
  font-family: var(--font-mono);
  font-size: 0.4rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #00D4AA;
  background: rgba(0, 212, 170, 0.12);
  border: 1px solid rgba(0, 212, 170, 0.22);
  border-radius: 20px;
  padding: 0.18rem 0.4rem;
}

/* Sub-label above event name */
.pcd-coming-up {
  margin: 0 0 0.1rem;
  font-family: var(--font-mono);
  font-size: 0.42rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: rgba(200, 190, 250, 0.45);
  text-transform: uppercase;
}

/* Event name */
.pcd-event-name {
  margin: 0 0 0.3rem;
  font-size: 1.02rem;
  font-weight: 700;
  color: rgba(255, 245, 225, 0.95);
  line-height: 1.15;
}

/* Hero countdown */
.pcd-hero {
  display: flex;
  align-items: flex-end;
  gap: 0.22rem;
  margin-bottom: 0.48rem;
  line-height: 1;
}
.cd-num {
  font-family: var(--font-mono);
  font-size: 2.4rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: rgba(255, 245, 225, 0.97);
}
.cd-unit {
  font-family: var(--font-mono);
  font-size: 0.88rem;
  font-weight: 600;
  color: rgba(200, 190, 250, 0.55);
  padding-bottom: 0.2rem;
}

/* Progress bar */
.pcd-bar-track {
  height: 4px;
  border-radius: 2px;
  background: rgba(155, 139, 250, 0.1);
  margin-bottom: 0.58rem;
  overflow: hidden;
}
.pcd-bar-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, rgba(155, 139, 250, 0.4), #9B8BFA);
  transition: width 1.2s ease;
}

/* Hairline */
.pcd-hairline {
  height: 1px;
  background: rgba(155, 139, 250, 0.12);
  margin-bottom: 0.52rem;
}

/* Event queue */
.pcd-queue {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.48rem;
}
.pcd-queue-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.pcd-queue-name {
  font-family: var(--font-mono);
  font-size: 0.55rem;
  font-weight: 600;
  color: rgba(255, 245, 225, 0.68);
}
.pcd-queue-time {
  font-family: var(--font-mono);
  font-size: 0.52rem;
  font-weight: 600;
  color: rgba(200, 190, 250, 0.48);
}

/* Nap badge */
.pcd-nap-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  background: rgba(0, 212, 170, 0.1);
  border: 1px solid rgba(0, 212, 170, 0.22);
  color: #00D4AA;
  font-family: var(--font-mono);
  font-size: 0.42rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  border-radius: 20px;
  padding: 0.2rem 0.46rem;
  margin-bottom: 0.48rem;
  align-self: flex-start;
}
.pcd-nap-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #00D4AA;
  flex-shrink: 0;
}

/* Destination chips */
.pcd-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}
.pcd-dest-chip {
  font-family: var(--font-mono);
  font-size: 0.38rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 0.16rem 0.38rem;
  border-radius: 20px;
  background: rgba(155, 139, 250, 0.1);
  border: 1px solid rgba(155, 139, 250, 0.18);
  color: rgba(200, 190, 250, 0.65);
  cursor: pointer;
  appearance: none;
  transition: background 0.15s, border-color 0.15s;
}
.pcd-dest-chip:hover {
  background: rgba(155, 139, 250, 0.18);
  border-color: rgba(155, 139, 250, 0.32);
}

/* ── Comparison mode ──────────────────────────────────────────── */
.pcd-city-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.42rem;
}
.pcd-city-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: rgba(255, 245, 225, 0.95);
}
.pcd-tz-delta {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 700;
  color: #FFBD76;
}
.pcd-solar-phase {
  margin: 0 0 0.2rem;
  font-family: var(--font-mono);
  font-size: 0.52rem;
  font-weight: 600;
  color: rgba(200, 190, 250, 0.72);
  letter-spacing: 0.06em;
}
.pcd-travel-readiness {
  margin: 0;
  font-size: 0.46rem;
  color: rgba(200, 190, 250, 0.5);
  line-height: 1.4;
  font-family: var(--font-mono);
}
.pcd-dismiss {
  position: absolute;
  top: 0.6rem;
  right: 0.7rem;
  font-size: 0.65rem;
  color: rgba(200, 190, 250, 0.4);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.1rem 0.2rem;
  line-height: 1;
  appearance: none;
}
.pcd-dismiss:hover {
  color: rgba(200, 190, 250, 0.75);
}
</style>
```

- [ ] **Step 5: Verify the file builds without errors**

```bash
npm run build
```

Expected: zero TypeScript errors. Common issues to check:
- `protocol.wakeWindowTime` not found → Task 1 must be complete first
- `GlobeComparison` type not found → check the import path `@/composables/useCobeGlobeData`
- `Object.values(protocol.dailyProtocol)` type error → `dailyProtocol` is `DailyProtocol` (keyed object), `Object.values()` returns `ProtocolItem[]`, `.sort()` returns `ProtocolItem[]` — this is correct

- [ ] **Step 6: Commit**

```bash
git add src/components/globe/GlobeProtocolCountdown.vue
git commit -m "feat(globe): add GlobeProtocolCountdown dual-mode card"
```

---

## Task 4: Refactor `HeliosGlobePanel.vue`

**Files:**
- Modify: `src/components/globe/HeliosGlobePanel.vue`

Three changes in one file: (1) remove the right overlay, mobile pill, and all dead code; (2) add `GlobeProtocolCountdown` and `handleDestSelect`; (3) wire `@select-destination` inline on `HeliosCobeGlobe`.

**Code to delete — script block (lines 1–71):**
- `import { computed, ref, onMounted, onUnmounted } from 'vue'` → change to `import { computed } from 'vue'`
- `import GlobeComparisonHud from './GlobeComparisonHud.vue'` → delete
- `const showRail = ref(false)` → delete
- `const isMobile = ref(false)` → delete
- The entire `handleResize`, `onMounted`, `onUnmounted`, `toggleRail`, `onDestinationSelect` blocks → delete

**Code to delete — template (lines 104–122):**
- The `<div class="globe-panel__overlay globe-panel__overlay--rail">` block (contains `<GlobeComparisonHud>`)
- The `<button v-if="isMobile" class="globe-panel__dest-pill ...">` block

**Code to delete — scoped styles:**
- `.globe-panel__overlay--rail { ... }` and all its `@media` overrides (at 1100px, 720px, 600px, 601px)
- `.globe-panel__dest-pill { ... }`
- `.globe-panel__dest-pill-dot { ... }`
- The `/* ── Mobile (≤ 600px) ── */` comment block and the `@media (max-width: 600px)` block that contains `globe-panel__overlay--rail` and `globe-panel__dest-pill` styles
- `@media (min-width: 601px) { .globe-panel__dest-pill { display: none; } }`

- [ ] **Step 1: Rewrite `<script setup>`**

Replace the entire `<script setup>` block (lines 1–71) with:

```typescript
<script setup lang="ts">
import { computed } from 'vue'
import GlobeOrbitalContext from './GlobeOrbitalContext.vue'
import GlobeProtocolCountdown from './GlobeProtocolCountdown.vue'
import GlobeStatStrip from './GlobeStatStrip.vue'
import HeliosCobeGlobe from './HeliosCobeGlobe.vue'
import { useCobeGlobeData } from '@/composables/useCobeGlobeData'

const {
  currentSnapshot,
  localSolar,
  comparisons,
  selectedComparison,
  selectedDestinationId,
  orbitalContext,
  selectDestination,
  clearDestination,
} = useCobeGlobeData()

const headerStatus = computed(() => {
  if (!selectedComparison.value) {
    return `${currentSnapshot.value.label} | ${localSolar.value.phase}`
  }
  return `${currentSnapshot.value.label} to ${selectedComparison.value.label}`
})

const timingLabel = computed(() => {
  const comparison = selectedComparison.value
  if (!comparison) {
    return `Sunrise ${localSolar.value.sunriseLabel} | Sunset ${localSolar.value.sunsetLabel}`
  }
  const sunriseDelta = formatSignedMinutes(comparison.sunriseDeltaMinutes)
  const sunsetDelta = formatSignedMinutes(comparison.sunsetDeltaMinutes)
  return `Sunrise ${sunriseDelta} | Sunset ${sunsetDelta}`
})

function formatSignedMinutes(value: number) {
  if (value === 0) return 'aligned'
  const direction = value > 0 ? '+' : '-'
  return `${direction}${Math.abs(value)}m`
}

function handleDestSelect(id: string | null) {
  if (id === null) {
    clearDestination()
  } else {
    selectDestination(id)
  }
}
</script>
```

- [ ] **Step 2: Rewrite `<template>`**

Replace the entire `<template>` block with:

```html
<template>
  <section class="globe-panel" aria-label="HELIOS COBE globe panel">
    <div class="globe-panel__hero">
      <div class="globe-panel__backdrop" aria-hidden="true" />

      <div class="globe-panel__overlay globe-panel__overlay--intro">
        <section class="globe-panel__intro-slab" aria-label="Orbital intro panel">
          <header class="globe-panel__header">
            <p class="globe-panel__eyebrow">HELIOS / COBE</p>
            <h2 class="globe-panel__title">Orbital View</h2>
            <p class="globe-panel__status">{{ headerStatus }}</p>
          </header>

          <GlobeOrbitalContext
            :context="orbitalContext"
            :current="currentSnapshot"
            :solar="localSolar"
            :route-label="selectedComparison?.label"
          />

          <GlobeProtocolCountdown
            :selected-comparison="selectedComparison"
            :comparisons="comparisons"
            @select-destination="handleDestSelect"
          />
        </section>
      </div>

      <div class="globe-panel__stage">
        <HeliosCobeGlobe
          class="globe-panel__globe"
          :current="currentSnapshot"
          :comparisons="comparisons"
          :selected-destination-id="selectedDestinationId"
          @select-destination="selectDestination"
        />
      </div>

      <div class="globe-panel__overlay globe-panel__overlay--stats">
        <GlobeStatStrip
          :anchor-label="currentSnapshot.label"
          :destination-label="selectedComparison?.label ?? 'Baseline view'"
          :timing-label="timingLabel"
        />
      </div>
    </div>
  </section>
</template>
```

**Note:** `@select-destination="selectDestination"` on `<HeliosCobeGlobe>` replaces the old `onDestinationSelect` handler. `HeliosCobeGlobe` emits `select-destination` with a destination `id: string` — `selectDestination(id)` signature matches exactly.

- [ ] **Step 3: Rewrite `<style scoped>`**

Remove the rail and pill CSS. Keep everything else. The final `<style scoped>` should contain only:

```css
<style scoped>
.globe-panel {
  display: grid;
  width: 100%;
  color: rgba(241, 245, 249, 0.96);
}

.globe-panel__header {
  display: grid;
  gap: 0.32rem;
}

.globe-panel__eyebrow {
  margin: 0;
  font-size: 0.64rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.78);
  white-space: nowrap;
  font-weight: 600;
}

.globe-panel__title {
  margin: 0;
  font-size: clamp(0.98rem, 1.2vw, 1.1rem);
  line-height: 1.1;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(241, 245, 249, 0.92);
  font-weight: 600;
}

.globe-panel__status {
  margin: 0;
  padding-top: 0.42rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  color: rgba(226, 232, 240, 0.7);
  font-size: 0.62rem;
  letter-spacing: 0.14em;
  line-height: 1.2;
  text-transform: uppercase;
}

.globe-panel__status::before {
  content: 'ROUTE / ';
  color: rgba(148, 163, 184, 0.82);
}

.globe-panel__hero {
  position: relative;
  min-height: clamp(34rem, 72vh, 52rem);
  overflow: hidden;
  border-radius: 2rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background:
    radial-gradient(circle at 50% 44%, rgba(73, 193, 255, 0.09), transparent 24%),
    radial-gradient(circle at 48% 58%, rgba(10, 132, 255, 0.06), transparent 30%),
    radial-gradient(circle at 18% 18%, rgba(0, 212, 170, 0.05), transparent 20%),
    radial-gradient(circle at 84% 24%, rgba(56, 189, 248, 0.05), transparent 18%),
    linear-gradient(180deg, rgba(5, 10, 22, 0.94), rgba(2, 6, 18, 0.98));
  box-shadow:
    0 28px 72px rgba(2, 8, 20, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.globe-panel__backdrop {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 50% 42%, rgba(6, 13, 28, 0), rgba(2, 6, 18, 0.2) 58%, rgba(2, 6, 18, 0.76) 100%),
    radial-gradient(circle at 50% 30%, rgba(111, 216, 255, 0.08), transparent 18%),
    radial-gradient(circle at 44% 22%, rgba(16, 185, 129, 0.04), transparent 16%),
    radial-gradient(circle at 31% 18%, rgba(255, 255, 255, 0.82) 0 0.09rem, transparent 0.11rem),
    radial-gradient(circle at 41% 27%, rgba(255, 255, 255, 0.58) 0 0.06rem, transparent 0.08rem),
    radial-gradient(circle at 49% 17%, rgba(148, 223, 255, 0.74) 0 0.08rem, transparent 0.1rem),
    radial-gradient(circle at 57% 21%, rgba(255, 255, 255, 0.64) 0 0.07rem, transparent 0.09rem),
    radial-gradient(circle at 65% 29%, rgba(111, 216, 255, 0.7) 0 0.07rem, transparent 0.09rem),
    radial-gradient(circle at 74% 22%, rgba(255, 255, 255, 0.6) 0 0.07rem, transparent 0.09rem),
    radial-gradient(circle at 79% 33%, rgba(177, 232, 255, 0.62) 0 0.06rem, transparent 0.08rem),
    radial-gradient(circle at 24% 40%, rgba(255, 255, 255, 0.42) 0 0.05rem, transparent 0.07rem),
    radial-gradient(circle at 36% 48%, rgba(167, 231, 255, 0.48) 0 0.06rem, transparent 0.08rem),
    radial-gradient(circle at 61% 39%, rgba(255, 255, 255, 0.4) 0 0.05rem, transparent 0.07rem),
    radial-gradient(circle at 72% 46%, rgba(167, 231, 255, 0.44) 0 0.06rem, transparent 0.08rem),
    radial-gradient(circle at 84% 18%, rgba(73, 193, 255, 0.05), transparent 13%),
    radial-gradient(circle at 16% 24%, rgba(32, 196, 255, 0.05), transparent 14%);
  pointer-events: none;
  opacity: 0.9;
}

.globe-panel__stage {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: clamp(3.8rem, 6vw, 4.8rem) clamp(1rem, 3vw, 2rem) clamp(7rem, 11vw, 8.5rem);
}

.globe-panel__globe {
  width: min(78vw, 63rem);
  max-width: 100%;
  transform: translateY(-0.5rem);
}

.globe-panel__overlay {
  position: absolute;
  z-index: 1;
}

.globe-panel__overlay--intro {
  top: 1.25rem;
  left: 1.25rem;
  width: min(16rem, 28vw);
}

.globe-panel__intro-slab {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.globe-panel__overlay--stats {
  left: 50%;
  right: auto;
  bottom: 1.2rem;
  width: min(42rem, calc(100% - 2.4rem));
  transform: translateX(-50%);
}

@media (max-width: 1100px) {
  .globe-panel__hero {
    min-height: clamp(34rem, 92vw, 48rem);
  }

  .globe-panel__stage {
    padding: clamp(3.8rem, 8vw, 4.8rem) 0.85rem clamp(5rem, 10vw, 7rem);
  }

  .globe-panel__overlay--intro {
    top: 1rem;
    left: 1rem;
    width: min(14rem, calc(100% - 5.4rem));
  }

  .globe-panel__overlay--stats {
    bottom: 0.9rem;
    width: min(38rem, calc(100% - 1.8rem));
  }

  .globe-panel__globe {
    width: min(100%, 50rem);
    transform: translateY(-0.5rem);
  }
}

@media (max-width: 720px) {
  .globe-panel__hero {
    border-radius: 1.45rem;
    min-height: clamp(34rem, 150vw, 43rem);
  }

  .globe-panel__header {
    gap: 0.28rem;
  }

  .globe-panel__title {
    font-size: 0.82rem;
    letter-spacing: 0.16em;
  }

  .globe-panel__status {
    padding-top: 0.36rem;
    font-size: 0.6rem;
    letter-spacing: 0.09em;
  }

  .globe-panel__stage {
    padding: 4.5rem 0.4rem 5.5rem;
  }

  .globe-panel__globe {
    width: min(110vw, 32.5rem);
    margin-left: -6vw;
    transform: translateY(-0.5rem);
  }

  .globe-panel__overlay--intro {
    top: 0.75rem;
    left: 0.75rem;
    width: min(13rem, calc(100% - 5.5rem));
  }

  .globe-panel__overlay--stats {
    left: 50%;
    right: auto;
    bottom: 0.75rem;
    width: min(31rem, calc(100% - 1.5rem));
    transform: translateX(-50%);
  }
}

@media (max-width: 600px) {
  .globe-panel__overlay--intro {
    top: 0.75rem;
    left: 0.75rem;
    right: 0.75rem;
    width: auto;
  }

  .globe-panel__stage {
    padding-top: 5.5rem;
  }
}
</style>
```

**Key deletions vs the original:**
- Removed: `.globe-panel__overlay--rail` (all breakpoints)
- Removed: `.globe-panel__dest-pill`, `.globe-panel__dest-pill-dot`
- Removed: `@media (min-width: 601px) { .globe-panel__dest-pill { display: none; } }`
- Removed: The 600px rail positioning block
- Kept: All intro, stage, globe, stats, and backdrop styles unchanged

- [ ] **Step 4: Verify build succeeds**

```bash
npm run build
```

Expected: zero TypeScript errors. Common issues to watch for:
- `clearDestination is not a function` → confirm Task 2 exported it in the composable return
- `Property 'select-destination' does not exist` → check `HeliosCobeGlobe` emits; if the error appears on the countdown card, check `defineEmits` in `GlobeProtocolCountdown.vue`
- `GlobeComparisonHud` import error → the import was deleted; if it persists, search the file for any remaining reference

- [ ] **Step 5: Visual check in dev server**

```bash
npm run dev
```

Open `http://localhost:5173`. Confirm:
- Soft violet countdown card appears below the solar elevation card in the left overlay
- No DESTINATIONS rail on the right
- Hero shows a number of minutes (or hours) until the next protocol event
- Queue shows 2 upcoming events with names and times

- [ ] **Step 6: Commit**

```bash
git add src/components/globe/HeliosGlobePanel.vue
git commit -m "feat(globe): replace comparison HUD with protocol countdown card"
```

---

## Task 5: Push `.data-section` further below the globe

**Files:**
- Modify: `src/pages/HomePage.vue:141`

One line change in scoped CSS. The `.data-section` margin-top is currently `0.5rem` (line 141). Increase to `2.5rem` to give the stat strip more breathing room below the globe.

- [ ] **Step 1: Update the margin**

In `src/pages/HomePage.vue`, find (around line 140–142):

```css
.data-section {
  margin-top: 0.5rem;
}
```

Change to:

```css
.data-section {
  margin-top: 2.5rem;
}
```

- [ ] **Step 2: Verify build**

```bash
npm run build
```

Expected: zero TypeScript errors (this is a CSS-only change; TypeScript won't flag it, but verify build completes cleanly).

- [ ] **Step 3: Visual check**

In the dev server, verify SpaceWeatherGauge, SocialJetLagScore, and EnvironmentBadge sit visibly further below the globe than before.

- [ ] **Step 4: Commit**

```bash
git add src/pages/HomePage.vue
git commit -m "style(home): increase data-section margin-top for globe breathing room"
```

---

## Verification Checklist

Run through these manually after all tasks are complete:

- [ ] `npm run build` — zero TypeScript errors across all 5 modified files
- [ ] **Default state**: page loads, soft violet countdown card shows below solar card; right rail absent
- [ ] **Countdown hero**: shows minutes (or hours+minutes) to next protocol event; decrements each minute
- [ ] **Event queue**: 2 upcoming events listed with names and remaining time
- [ ] **Progress bar**: fills proportionally; smooth 1.2s CSS transition on each solar.now tick
- [ ] **Nap badge**: visible between 12:00–15:00 when `hoursAwake >= 6 && <= 9`; absent otherwise
- [ ] **Destination chips**: 3 chips (Tokyo, London, NYC) visible in countdown mode
- [ ] **Comparison mode**: click a chip → card swaps to city name, timezone delta, solar phase, travel readiness
- [ ] **Dismiss button**: `✕` in comparison mode → returns to countdown
- [ ] **Globe marker click**: clicking a globe marker still triggers `selectDestination` and swaps the card
- [ ] **Stat strip**: visibly lower than before (2.5rem gap vs 0.5rem)
- [ ] **No orphaned refs**: `showRail`, `isMobile`, `handleResize`, `toggleRail` absent from `HeliosGlobePanel.vue`
- [ ] **`wakeWindowTime` in store**: `protocol.wakeWindowTime` returns a `Date` (not undefined)
