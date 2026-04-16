# COBE Globe Replacement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current `globe.gl` homepage globe with a lighter `COBE` implementation that stays draggable and exposes local solar elevation, ISS / orbital context, and current-vs-multiple-destination comparison.

**Architecture:** Keep [`HomePage.vue`](../../../../src/pages/HomePage.vue) as the composition surface and move the new globe system into a focused globe feature set. Use a pure data composable for destination/solar/orbital derivation, a COBE rendering component for canvas interaction only, and lightweight HUD components for user-facing stats. Preserve the staged-loading route boundary already built in the homepage.

**Tech Stack:** Vue 3 + Composition API + TypeScript, Pinia, COBE, Vitest, Vite.

---

## File Map

### Feature files

- Create: `src/composables/useCobeGlobeData.ts`
- Create: `src/composables/useCobeGlobeData.test.ts`
- Create: `src/components/globe/HeliosCobeGlobe.vue`
- Create: `src/components/globe/GlobeComparisonHud.vue`
- Create: `src/components/globe/GlobeOrbitalContext.vue`
- Create: `src/components/globe/HeliosGlobePanel.vue`

### Integration files

- Modify: `src/pages/HomePage.vue`
- Modify: `src/components/home/HomeGlobePlaceholder.vue`
- Modify: `package.json`
- Modify: `vite.config.ts`
- Delete: `src/components/HeliosGlobe.vue`

### Responsibility split

- `useCobeGlobeData.ts` owns globe-ready data derivation only: current location marker, selected destination, comparison stats, and honest orbital context.
- `HeliosCobeGlobe.vue` owns the COBE canvas, pointer interaction, idle rotation, marker hit areas, and selection emits.
- `GlobeComparisonHud.vue` owns destination comparison presentation.
- `GlobeOrbitalContext.vue` owns ISS / orbital context presentation and truthful fallback copy.
- `HeliosGlobePanel.vue` composes the globe canvas plus the two HUD surfaces.
- `HomePage.vue` stays a route-level composition surface and swaps the old globe async import to the new panel.

---

### Task 1: Build and Test the Globe Data Composable

**Files:**
- Create: `src/composables/useCobeGlobeData.ts`
- Create: `src/composables/useCobeGlobeData.test.ts`
- Read: `src/stores/geo.ts`
- Read: `src/stores/solar.ts`
- Read: `src/stores/jetlag.ts`

- [ ] **Step 1: Write the failing tests**

Create `src/composables/useCobeGlobeData.test.ts`:

```ts
import { describe, expect, it } from 'vitest'

import {
  buildDestinationComparisons,
  buildLocalSolarSnapshot,
  getInitialSelectedDestinationId,
} from './useCobeGlobeData'

describe('buildLocalSolarSnapshot', () => {
  it('returns the local solar elevation and phase payload used by the HUD', () => {
    const result = buildLocalSolarSnapshot({
      elevationDeg: 17.4,
      solarPhase: 'Day',
      sunrise: new Date('2026-04-10T06:12:00Z'),
      sunset: new Date('2026-04-10T18:21:00Z'),
    })

    expect(result.elevationDeg).toBe(17.4)
    expect(result.phase).toBe('Day')
    expect(result.sunriseLabel).toMatch(/\d{2}:\d{2}/)
    expect(result.sunsetLabel).toMatch(/\d{2}:\d{2}/)
  })
})

describe('buildDestinationComparisons', () => {
  it('derives timezone and solar deltas for multiple destinations', () => {
    const comparisons = buildDestinationComparisons({
      current: {
        id: 'current',
        label: 'Bangkok',
        lat: 13.7563,
        lng: 100.5018,
        timezone: 'Asia/Bangkok',
        elevationDeg: 52.1,
        sunrise: new Date('2026-04-10T23:11:00Z'),
        sunset: new Date('2026-04-10T11:36:00Z'),
      },
      destinations: [
        {
          id: 'tokyo',
          label: 'Tokyo',
          lat: 35.6762,
          lng: 139.6503,
          timezone: 'Asia/Tokyo',
          elevationDeg: 34.2,
          sunrise: new Date('2026-04-10T20:19:00Z'),
          sunset: new Date('2026-04-10T09:11:00Z'),
        },
        {
          id: 'london',
          label: 'London',
          lat: 51.5074,
          lng: -0.1278,
          timezone: 'Europe/London',
          elevationDeg: 11.6,
          sunrise: new Date('2026-04-10T05:18:00Z'),
          sunset: new Date('2026-04-10T18:42:00Z'),
        },
      ],
    })

    expect(comparisons).toHaveLength(2)
    expect(comparisons[0]?.timezoneDeltaHours).toBe(2)
    expect(comparisons[1]?.travelReadiness).toMatch(/shift|travel/i)
  })
})

describe('getInitialSelectedDestinationId', () => {
  it('defaults to the first destination when destinations are available', () => {
    expect(
      getInitialSelectedDestinationId([
        { id: 'tokyo', label: 'Tokyo' },
        { id: 'london', label: 'London' },
      ]),
    ).toBe('tokyo')
  })

  it('returns null when there are no destinations', () => {
    expect(getInitialSelectedDestinationId([])).toBeNull()
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
npm run test -- src/composables/useCobeGlobeData.test.ts
```

Expected:

- Vitest fails because `useCobeGlobeData.ts` does not exist yet.

- [ ] **Step 3: Write the minimal composable implementation**

Create `src/composables/useCobeGlobeData.ts`:

```ts
import { computed, readonly, shallowRef } from 'vue'
import SunCalc from 'suncalc'

import { TIMEZONE_CITIES } from '@/stores/jetlag'

export interface GlobeDestination {
  id: string
  label: string
  lat: number
  lng: number
  timezone: string
}

export interface GlobeSolarSnapshotInput {
  elevationDeg: number
  solarPhase: string
  sunrise: Date
  sunset: Date
}

export interface GlobeSolarSnapshot {
  elevationDeg: number
  phase: string
  sunriseLabel: string
  sunsetLabel: string
}

export interface GlobeDestinationSnapshot extends GlobeDestination {
  elevationDeg: number
  sunrise: Date
  sunset: Date
}

export interface GlobeComparison {
  id: string
  label: string
  lat: number
  lng: number
  timezone: string
  timezoneDeltaHours: number
  destinationElevationDeg: number
  sunriseDeltaMinutes: number
  sunsetDeltaMinutes: number
  travelReadiness: string
}

function formatTimeLabel(date: Date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function getTimezoneOffsetHours(timezone: string, date: Date) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(date)

  const pick = (type: string) => Number(parts.find((part) => part.type === type)?.value ?? 0)
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

function getTravelReadiness(timezoneDeltaHours: number) {
  const abs = Math.abs(timezoneDeltaHours)
  if (abs === 0) return 'Aligned with your current schedule.'
  if (abs <= 2) return 'Light shift. Low travel strain expected.'
  if (abs <= 5) return 'Moderate shift. Plan light timing deliberately.'
  return 'Large shift. Expect meaningful circadian strain.'
}

export function buildLocalSolarSnapshot(input: GlobeSolarSnapshotInput): GlobeSolarSnapshot {
  return {
    elevationDeg: input.elevationDeg,
    phase: input.solarPhase,
    sunriseLabel: formatTimeLabel(input.sunrise),
    sunsetLabel: formatTimeLabel(input.sunset),
  }
}

export function buildDestinationComparisons(input: {
  current: GlobeDestinationSnapshot
  destinations: GlobeDestinationSnapshot[]
}): GlobeComparison[] {
  const anchor = new Date()
  const currentOffset = getTimezoneOffsetHours(input.current.timezone, anchor)

  return input.destinations.map((destination) => {
    const destinationOffset = getTimezoneOffsetHours(destination.timezone, anchor)
    return {
      id: destination.id,
      label: destination.label,
      lat: destination.lat,
      lng: destination.lng,
      timezone: destination.timezone,
      timezoneDeltaHours: Math.round((destinationOffset - currentOffset) * 10) / 10,
      destinationElevationDeg: destination.elevationDeg,
      sunriseDeltaMinutes: Math.round((destination.sunrise.getTime() - input.current.sunrise.getTime()) / 60000),
      sunsetDeltaMinutes: Math.round((destination.sunset.getTime() - input.current.sunset.getTime()) / 60000),
      travelReadiness: getTravelReadiness(destinationOffset - currentOffset),
    }
  })
}

export function getInitialSelectedDestinationId(destinations: Array<{ id: string }>) {
  return destinations[0]?.id ?? null
}

export function useCobeGlobeData() {
  const now = new Date()
  const seededDestinations = [
    'Asia/Tokyo',
    'Europe/London',
    'America/New_York',
  ]
    .map((timezone, index) => {
      const city = TIMEZONE_CITIES[timezone]
      if (!city) return null
      return {
        id: `destination-${index + 1}`,
        label: city.label,
        lat: city.lat,
        lng: city.lng,
        timezone,
      }
    })
    .filter((value): value is GlobeDestination => value !== null)

  const destinations = shallowRef<GlobeDestination[]>(seededDestinations)
  const selectedDestinationId = shallowRef<string | null>(getInitialSelectedDestinationId(destinations.value))

  const currentLocation = computed<GlobeDestinationSnapshot>(() => {
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
    const lat = 13.7563
    const lng = 100.5018
    const times = SunCalc.getTimes(now, lat, lng)
    const position = SunCalc.getPosition(now, lat, lng)
    return {
      id: 'current-location',
      label: 'Current Location',
      lat,
      lng,
      timezone,
      elevationDeg: Number(((position.altitude * 180) / Math.PI).toFixed(1)),
      sunrise: times.sunrise,
      sunset: times.sunset,
    }
  })

  const localSolar = computed(() =>
    buildLocalSolarSnapshot({
      elevationDeg: currentLocation.value.elevationDeg,
      solarPhase: currentLocation.value.elevationDeg > 0 ? 'Day' : 'Night',
      sunrise: currentLocation.value.sunrise,
      sunset: currentLocation.value.sunset,
    }),
  )

  const destinationSnapshots = computed<GlobeDestinationSnapshot[]>(() =>
    destinations.value.map((destination) => {
      const times = SunCalc.getTimes(now, destination.lat, destination.lng)
      const position = SunCalc.getPosition(now, destination.lat, destination.lng)
      return {
        ...destination,
        elevationDeg: Number(((position.altitude * 180) / Math.PI).toFixed(1)),
        sunrise: times.sunrise,
        sunset: times.sunset,
      }
    }),
  )

  const comparisons = computed(() =>
    buildDestinationComparisons({
      current: currentLocation.value,
      destinations: destinationSnapshots.value,
    }),
  )

  const selectedComparison = computed(() =>
    comparisons.value.find((comparison) => comparison.id === selectedDestinationId.value) ?? null,
  )

  const orbitalContext = computed(() => ({
    mode: 'contextual' as const,
    label: 'Orbital context only',
    summary: 'ISS context is visual unless a live orbital data source is wired.',
  }))

  function selectDestination(destinationId: string) {
    selectedDestinationId.value = destinationId
  }

  return {
    destinations: readonly(destinations),
    localSolar,
    comparisons,
    selectedDestinationId: readonly(selectedDestinationId),
    selectedComparison,
    orbitalContext,
    selectDestination,
  }
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```powershell
npm run test -- src/composables/useCobeGlobeData.test.ts
```

Expected:

- Vitest reports `4 passed`.

- [ ] **Step 5: Commit**

```powershell
git add src/composables/useCobeGlobeData.ts src/composables/useCobeGlobeData.test.ts
git commit -m "Add COBE globe data composable"
```

---

### Task 2: Build the Globe HUD Components

**Files:**
- Create: `src/components/globe/GlobeComparisonHud.vue`
- Create: `src/components/globe/GlobeOrbitalContext.vue`
- Create: `src/components/globe/HeliosGlobePanel.vue`

- [ ] **Step 1: Create the comparison HUD component**

Create `src/components/globe/GlobeComparisonHud.vue`:

```vue
<script setup lang="ts">
interface GlobeComparisonHudModel {
  label: string
  timezoneDeltaHours: number
  destinationElevationDeg: number
  sunriseDeltaMinutes: number
  sunsetDeltaMinutes: number
  travelReadiness: string
}

defineProps<{
  comparison: GlobeComparisonHudModel | null
}>()

function formatDeltaHours(hours: number) {
  if (hours === 0) return 'Same timezone'
  return `${hours > 0 ? '+' : ''}${hours}h`
}

function formatDeltaMinutes(minutes: number) {
  if (minutes === 0) return 'Aligned'
  return `${minutes > 0 ? '+' : ''}${minutes} min`
}
</script>

<template>
  <section class="comparison-hud">
    <template v-if="comparison">
      <div class="comparison-hud__meta">
        <span class="comparison-hud__kicker">DESTINATION</span>
        <span class="comparison-hud__title">{{ comparison.label }}</span>
      </div>
      <div class="comparison-hud__grid">
        <div class="comparison-hud__stat">
          <span class="comparison-hud__label">TZ DELTA</span>
          <span class="comparison-hud__value">{{ formatDeltaHours(comparison.timezoneDeltaHours) }}</span>
        </div>
        <div class="comparison-hud__stat">
          <span class="comparison-hud__label">SOLAR ELEVATION</span>
          <span class="comparison-hud__value">{{ comparison.destinationElevationDeg.toFixed(1) }}°</span>
        </div>
        <div class="comparison-hud__stat">
          <span class="comparison-hud__label">SUNRISE DELTA</span>
          <span class="comparison-hud__value">{{ formatDeltaMinutes(comparison.sunriseDeltaMinutes) }}</span>
        </div>
        <div class="comparison-hud__stat">
          <span class="comparison-hud__label">SUNSET DELTA</span>
          <span class="comparison-hud__value">{{ formatDeltaMinutes(comparison.sunsetDeltaMinutes) }}</span>
        </div>
      </div>
      <p class="comparison-hud__summary">{{ comparison.travelReadiness }}</p>
    </template>

    <template v-else>
      <span class="comparison-hud__kicker">DESTINATION</span>
      <p class="comparison-hud__summary">Add or select a destination to compare solar timing and travel strain.</p>
    </template>
  </section>
</template>
```

- [ ] **Step 2: Create the orbital context component**

Create `src/components/globe/GlobeOrbitalContext.vue`:

```vue
<script setup lang="ts">
defineProps<{
  label: string
  summary: string
}>()
</script>

<template>
  <section class="orbital-context">
    <span class="orbital-context__kicker">ISS / ORBITAL CONTEXT</span>
    <span class="orbital-context__label">{{ label }}</span>
    <p class="orbital-context__summary">{{ summary }}</p>
  </section>
</template>
```

- [ ] **Step 3: Create the panel composition component**

Create `src/components/globe/HeliosGlobePanel.vue`:

```vue
<script setup lang="ts">
import GlobeComparisonHud from './GlobeComparisonHud.vue'
import GlobeOrbitalContext from './GlobeOrbitalContext.vue'
import HeliosCobeGlobe from './HeliosCobeGlobe.vue'
import { useCobeGlobeData } from '@/composables/useCobeGlobeData'

const globe = useCobeGlobeData()
</script>

<template>
  <div class="helios-globe-panel">
    <HeliosCobeGlobe
      :destinations="globe.comparisons"
      :selected-destination-id="globe.selectedDestinationId ?? undefined"
      @select-destination="globe.selectDestination"
    />
    <div class="helios-globe-panel__hud">
      <GlobeComparisonHud :comparison="globe.selectedComparison" />
      <GlobeOrbitalContext
        :label="globe.orbitalContext.label"
        :summary="globe.orbitalContext.summary"
      />
    </div>
  </div>
</template>
```

- [ ] **Step 4: Run the build to verify the HUD components type-check**

Run:

```powershell
npm run build
```

Expected:

- The build may still fail because `HeliosCobeGlobe.vue` does not exist yet, but the new HUD component files should type-check once the next task lands.

- [ ] **Step 5: Commit**

```powershell
git add src/components/globe/GlobeComparisonHud.vue src/components/globe/GlobeOrbitalContext.vue src/components/globe/HeliosGlobePanel.vue
git commit -m "Add COBE globe HUD components"
```

---

### Task 3: Implement the COBE Globe Renderer

**Files:**
- Create: `src/components/globe/HeliosCobeGlobe.vue`
- Modify: `package.json`

- [ ] **Step 1: Add the new dependency**

Update `package.json` dependencies:

```json
{
  "dependencies": {
    "@vueuse/core": "^14.2.1",
    "cobe": "^0.6.4",
    "date-fns": "^4.1.0",
    "lucide-vue-next": "^1.0.0",
    "pinia": "^3.0.4",
    "suncalc": "^1.9.0",
    "vue": "^3.5.30",
    "vue-router": "^4.6.4"
  }
}
```

- [ ] **Step 2: Install dependencies**

Run:

```powershell
npm install
```

Expected:

- `cobe` is added to `package-lock.json`.

- [ ] **Step 3: Create the COBE renderer**

Create `src/components/globe/HeliosCobeGlobe.vue`:

```vue
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import createGlobe from 'cobe'

interface GlobeMarker {
  id: string
  label: string
  lat: number
  lng: number
}

const props = defineProps<{
  destinations: GlobeMarker[]
  selectedDestinationId?: string
}>()

const emit = defineEmits<{
  selectDestination: [destinationId: string]
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const width = ref(0)
const phi = ref(0)
const theta = ref(0.25)
let globe: ReturnType<typeof createGlobe> | null = null
let animationFrame = 0
let pointerDown = false

const markers = computed(() =>
  props.destinations.map((destination) => ({
    id: destination.id,
    location: [destination.lat, destination.lng] as [number, number],
    size: destination.id === props.selectedDestinationId ? 0.08 : 0.055,
  })),
)

function mountGlobe() {
  if (!canvasRef.value || width.value === 0) return

  globe?.destroy()
  globe = createGlobe(canvasRef.value, {
    devicePixelRatio: 2,
    width: width.value * 2,
    height: width.value * 2,
    phi: phi.value,
    theta: theta.value,
    dark: 1,
    diffuse: 1.15,
    mapSamples: 12000,
    mapBrightness: 2.8,
    baseColor: [0.06, 0.11, 0.15],
    markerColor: [1, 0.74, 0.46],
    glowColor: [0.05, 0.39, 0.42],
    markers: markers.value,
    onRender: (state) => {
      state.phi = phi.value
      state.theta = theta.value
      if (!pointerDown) {
        phi.value += 0.0025
      }
    },
  })
}

function handlePointerDown() {
  pointerDown = true
}

function handlePointerUp() {
  pointerDown = false
}

function handlePointerMove(event: PointerEvent) {
  if (!pointerDown) return
  phi.value += event.movementX * 0.005
  theta.value = Math.max(-0.55, Math.min(0.55, theta.value - event.movementY * 0.003))
}

function handleClick() {
  const next = props.destinations.find((destination) => destination.id !== props.selectedDestinationId)
  if (next) {
    emit('selectDestination', next.id)
  }
}

onMounted(() => {
  if (!canvasRef.value) return
  width.value = canvasRef.value.clientWidth
  mountGlobe()
  canvasRef.value.addEventListener('pointerdown', handlePointerDown)
  window.addEventListener('pointerup', handlePointerUp)
  window.addEventListener('pointermove', handlePointerMove)
  canvasRef.value.addEventListener('click', handleClick)
})

watch(markers, mountGlobe)

onBeforeUnmount(() => {
  globe?.destroy()
  globe = null
  cancelAnimationFrame(animationFrame)
  canvasRef.value?.removeEventListener('pointerdown', handlePointerDown)
  canvasRef.value?.removeEventListener('click', handleClick)
  window.removeEventListener('pointerup', handlePointerUp)
  window.removeEventListener('pointermove', handlePointerMove)
})
</script>

<template>
  <div class="helios-cobe-globe">
    <canvas ref="canvasRef" class="helios-cobe-globe__canvas" />
  </div>
</template>
```

- [ ] **Step 4: Run the build**

Run:

```powershell
npm run build
```

Expected:

- Build passes with the new globe renderer in place, though HomePage still points at the old globe until Task 4.

- [ ] **Step 5: Commit**

```powershell
git add package.json package-lock.json src/components/globe/HeliosCobeGlobe.vue
git commit -m "Add COBE globe renderer"
```

---

### Task 4: Integrate the COBE Globe and Verify Bundle Reduction

**Files:**
- Modify: `src/pages/HomePage.vue`
- Modify: `src/components/home/HomeGlobePlaceholder.vue`
- Modify: `vite.config.ts`
- Delete: `src/components/HeliosGlobe.vue`

- [ ] **Step 1: Point the home page at the new globe panel**

Modify `src/pages/HomePage.vue`:

```ts
const HeliosGlobe = defineAsyncComponent({
  loader: () => import('@/components/globe/HeliosGlobePanel.vue'),
  loadingComponent: HomeGlobePlaceholder,
  delay: 0,
})
```

No other route sections should change.

- [ ] **Step 2: Update the placeholder copy for the new globe direction**

Modify `src/components/home/HomeGlobePlaceholder.vue` copy:

```vue
<div class="home-globe-placeholder__badge">
  <span class="home-globe-placeholder__dot" />
  <span>Loading solar, orbital, and travel context...</span>
</div>
```

- [ ] **Step 3: Remove the old globe dependency path from chunking**

Modify `vite.config.ts`:

```ts
const LOCAL_CHUNK_GROUPS = {
  'home-globe': [
    '/src/components/globe/HeliosGlobePanel.vue',
    '/src/components/globe/HeliosCobeGlobe.vue',
    '/src/components/globe/GlobeComparisonHud.vue',
    '/src/components/globe/GlobeOrbitalContext.vue',
    '/src/composables/useCobeGlobeData.ts'
  ],
  'home-chat': [
    '/src/components/ChatInterface.vue',
    '/src/components/ChatMessage.vue',
    '/src/composables/useAI.ts',
    '/src/stores/chat.ts'
  ]
} as const

const VENDOR_CHUNK_GROUPS = {
  'home-globe-vendor': ['cobe'],
} as const
```

Delete the old `globe.gl` / `three` chunk rules.

- [ ] **Step 4: Delete the old globe file**

Delete:

```text
src/components/HeliosGlobe.vue
```

- [ ] **Step 5: Run the full verification set**

Run:

```powershell
npm run test -- src/composables/useStagedReveal.test.ts
npm run test -- src/composables/useCobeGlobeData.test.ts
npm run build
```

Expected:

- Both Vitest commands pass.
- The build passes.
- The emitted `HomePage` route remains small.
- The deferred globe vendor chunk is materially smaller than the old `globe.gl` / `three` stack.

- [ ] **Step 6: Capture the bundle comparison**

Run:

```powershell
npm run build | Select-String "HomePage|home-globe|home-globe-vendor|three|globe"
```

Expected:

- No `three` or `globe.gl`-driven mega chunk remains in the output.
- `home-globe-vendor` is materially smaller than the prior multi-hundred-kilobyte or megabyte deferred globe payload.

- [ ] **Step 7: Commit**

```powershell
git add src/pages/HomePage.vue src/components/home/HomeGlobePlaceholder.vue src/components/globe/HeliosGlobePanel.vue src/components/globe/GlobeComparisonHud.vue src/components/globe/GlobeOrbitalContext.vue src/components/globe/HeliosCobeGlobe.vue src/composables/useCobeGlobeData.ts src/composables/useCobeGlobeData.test.ts package.json package-lock.json vite.config.ts
git commit -m "Replace homepage globe with COBE"
```

---

## Self-Review

### Spec coverage

- COBE replacement is covered in Tasks 3 and 4.
- Local solar elevation is covered in Task 1 data derivation and Task 2 HUD rendering.
- ISS / orbital context is covered in Task 1 contextual model and Task 2 orbital HUD.
- Current vs multiple destinations is covered in Task 1 data derivation and Task 3/4 globe selection wiring.
- Bundle reduction verification is covered in Task 4.

### Placeholder scan

- No `TODO`, `TBD`, or “similar to above” placeholders remain.
- Each code-changing task names exact files.
- Each verification step includes explicit commands.

### Type consistency

- `useCobeGlobeData.ts` defines the comparison shape used by the HUD and the destination marker shape used by the COBE renderer.
- `HeliosGlobePanel.vue` is the only component composing the data and presentation layers.
- `HomePage.vue` remains a composition surface importing the panel through the existing staged boundary.
