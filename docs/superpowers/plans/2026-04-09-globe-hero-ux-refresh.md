# Globe Hero UX Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the homepage globe hero into a globe-dominant cinematic command deck with floating overlays and cleaner responsive behavior.

**Architecture:** Keep [`HomePage.vue`](../../../../src/pages/HomePage.vue) as the route composition surface and keep the COBE renderer isolated in [`HeliosCobeGlobe.vue`](../../../../src/components/globe/HeliosCobeGlobe.vue). Concentrate the redesign inside the globe feature set by slimming the orbital and destination components, introducing a dedicated bottom stat strip, and restructuring [`HeliosGlobePanel.vue`](../../../../src/components/globe/HeliosGlobePanel.vue) into a layered hero stage instead of a three-column grid.

**Tech Stack:** Vue 3, `<script setup lang="ts">`, Vite, Pinia, COBE, scoped CSS.

---

## File Map

### Feature files

- Modify: `src/components/globe/HeliosGlobePanel.vue`
- Modify: `src/components/globe/HeliosCobeGlobe.vue`
- Modify: `src/components/globe/GlobeOrbitalContext.vue`
- Modify: `src/components/globe/GlobeComparisonHud.vue`
- Create: `src/components/globe/GlobeStatStrip.vue`

### Supporting files

- Optional modify: `src/components/home/HomeGlobePlaceholder.vue`

### Responsibility split

- `HeliosGlobePanel.vue`
  - composition surface for the hero
  - overlay placement
  - minimal section copy
- `HeliosCobeGlobe.vue`
  - renderer only
  - drag behavior
  - small selector chips if still useful
- `GlobeOrbitalContext.vue`
  - compact top-left card
- `GlobeComparisonHud.vue`
  - right-side destination rail
- `GlobeStatStrip.vue`
  - floating bottom context strip

---

### Task 1: Build the Bottom Stat Strip

**Files:**
- Create: `src/components/globe/GlobeStatStrip.vue`
- Read: `src/components/globe/HeliosGlobePanel.vue`

- [ ] **Step 1: Create the strip component**

Create `src/components/globe/GlobeStatStrip.vue`:

```vue
<script setup lang="ts">
interface StatStripProps {
  anchorLabel: string
  destinationLabel: string
  timingLabel: string
}

defineProps<StatStripProps>()
</script>

<template>
  <div class="globe-stat-strip" aria-label="Globe context strip">
    <div class="globe-stat-strip__item">
      <span class="globe-stat-strip__label">Anchor</span>
      <strong class="globe-stat-strip__value">{{ anchorLabel }}</strong>
    </div>
    <div class="globe-stat-strip__item">
      <span class="globe-stat-strip__label">Destination</span>
      <strong class="globe-stat-strip__value">{{ destinationLabel }}</strong>
    </div>
    <div class="globe-stat-strip__item">
      <span class="globe-stat-strip__label">Solar delta</span>
      <strong class="globe-stat-strip__value">{{ timingLabel }}</strong>
    </div>
  </div>
</template>

<style scoped>
.globe-stat-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(6, 14, 28, 0.68);
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 36px rgba(2, 8, 20, 0.24);
}

.globe-stat-strip__item {
  display: grid;
  gap: 0.18rem;
}

.globe-stat-strip__label {
  font-size: 0.58rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.74);
}

.globe-stat-strip__value {
  font-size: 0.82rem;
  line-height: 1.3;
  color: rgba(241, 245, 249, 0.96);
}

@media (max-width: 720px) {
  .globe-stat-strip {
    grid-template-columns: 1fr;
    border-radius: 1.1rem;
  }
}
</style>
```

- [ ] **Step 2: Run the build to verify the new component type-checks**

Run:

```powershell
npm run build
```

Expected:

- Build passes.

- [ ] **Step 3: Commit**

```powershell
git add src/components/globe/GlobeStatStrip.vue
git commit -m "Add globe hero stat strip"
```

---

### Task 2: Compress the Overlay Components

**Files:**
- Modify: `src/components/globe/GlobeOrbitalContext.vue`
- Modify: `src/components/globe/GlobeComparisonHud.vue`

- [ ] **Step 1: Slim the orbital card structure**

Update `src/components/globe/GlobeOrbitalContext.vue` so the template becomes a compact top-left card:

```vue
<template>
  <section class="orbital-card" aria-label="Orbital context HUD">
    <p class="orbital-card__eyebrow">Orbital context</p>
    <h3 class="orbital-card__title">{{ current.label }}</h3>
    <div class="orbital-card__metrics">
      <span>{{ solar.phase }}</span>
      <span>{{ solar.elevationDeg.toFixed(1) }}&deg;</span>
      <span>{{ current.timezone }}</span>
    </div>
    <p class="orbital-card__summary">{{ context.summary }}</p>
  </section>
</template>
```

Use compact styles:

```css
.orbital-card {
  max-width: 18rem;
  padding: 0.95rem 1rem;
  border-radius: 1.15rem;
  background: rgba(6, 15, 28, 0.58);
  border: 1px solid rgba(148, 163, 184, 0.14);
  backdrop-filter: blur(18px);
}
```

- [ ] **Step 2: Simplify the destination rail**

Update `src/components/globe/GlobeComparisonHud.vue`:

```vue
<template>
  <section class="comparison-rail" aria-label="Destination comparison HUD">
    <p class="comparison-rail__eyebrow">Destinations</p>
    <div class="comparison-rail__list">
      <button
        v-for="comparison in props.comparisons.slice(0, 3)"
        :key="comparison.id"
        type="button"
        class="comparison-rail__card"
        :class="{ 'comparison-rail__card--active': comparison.id === props.selectedDestinationId }"
        :aria-pressed="comparison.id === props.selectedDestinationId"
        @click="handleSelect(comparison.id)"
      >
        <div class="comparison-rail__row">
          <strong>{{ comparison.label }}</strong>
          <span>{{ formatSignedHours(comparison.timezoneDeltaHours) }}</span>
        </div>
        <p class="comparison-rail__status">{{ comparison.travelReadiness }}</p>
      </button>
    </div>
  </section>
</template>
```

- [ ] **Step 3: Run the build**

Run:

```powershell
npm run build
```

Expected:

- Build passes with slimmer overlay components.

- [ ] **Step 4: Commit**

```powershell
git add src/components/globe/GlobeOrbitalContext.vue src/components/globe/GlobeComparisonHud.vue
git commit -m "Slim globe hero overlay cards"
```

---

### Task 3: Recompose the Hero Stage

**Files:**
- Modify: `src/components/globe/HeliosGlobePanel.vue`
- Modify: `src/components/globe/HeliosCobeGlobe.vue`
- Read: `src/composables/useCobeGlobeData.ts`
- Read: `src/components/globe/GlobeStatStrip.vue`

- [ ] **Step 1: Replace the grid dashboard with a single layered stage**

Update `src/components/globe/HeliosGlobePanel.vue` so it composes overlays around one dominant globe:

```vue
<template>
  <section class="globe-hero" aria-label="HELIOS globe hero">
    <header class="globe-hero__header">
      <p class="globe-hero__eyebrow">HELIOS / COBE</p>
    </header>

    <div class="globe-hero__stage">
      <GlobeOrbitalContext
        class="globe-hero__orbital"
        :context="orbitalContext"
        :current="currentSnapshot"
        :solar="localSolar"
      />

      <div class="globe-hero__core">
        <HeliosCobeGlobe
          :current="currentSnapshot"
          :comparisons="comparisons"
          :selected-destination-id="selectedDestinationId"
          @select-destination="selectDestination"
        />
      </div>

      <GlobeComparisonHud
        class="globe-hero__rail"
        :comparisons="comparisons"
        :selected-destination-id="selectedDestinationId"
        @select-destination="selectDestination"
      />

      <GlobeStatStrip
        class="globe-hero__strip"
        :anchor-label="currentSnapshot.label"
        :destination-label="selectedComparison?.label ?? 'None selected'"
        :timing-label="selectedComparison ? `${selectedComparison.sunriseDeltaMinutes}m sunrise` : 'Awaiting destination'"
      />
    </div>
  </section>
</template>
```

- [ ] **Step 2: Rework the stage styles**

Use a layered stage rather than a three-column grid:

```css
.globe-hero__stage {
  position: relative;
  min-height: 42rem;
  display: grid;
  place-items: center;
}

.globe-hero__core {
  width: min(72vw, 58rem);
  z-index: 1;
}

.globe-hero__orbital {
  position: absolute;
  top: 1.5rem;
  left: 0;
  z-index: 2;
}

.globe-hero__rail {
  position: absolute;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  width: min(19rem, 100%);
  z-index: 2;
}

.globe-hero__strip {
  position: absolute;
  left: 50%;
  bottom: 1.2rem;
  transform: translateX(-50%);
  width: min(44rem, calc(100% - 2rem));
  z-index: 3;
}
```

- [ ] **Step 3: Make the globe visually dominate**

Update `src/components/globe/HeliosCobeGlobe.vue` styles so the globe can carry the section:

```css
.cobe-globe {
  min-height: 30rem;
  width: 100%;
}

.cobe-globe__canvas {
  filter: drop-shadow(0 0 42px rgba(87, 213, 255, 0.14));
}

.cobe-globe__controls {
  left: 50%;
  bottom: 4rem;
  width: max-content;
  max-width: calc(100% - 2rem);
  transform: translateX(-50%);
}
```

- [ ] **Step 4: Run the build**

Run:

```powershell
npm run build
```

Expected:

- Build passes.
- The hero no longer renders as a three-column dashboard.

- [ ] **Step 5: Commit**

```powershell
git add src/components/globe/HeliosGlobePanel.vue src/components/globe/HeliosCobeGlobe.vue src/components/globe/GlobeStatStrip.vue
git commit -m "Recompose globe into hero stage"
```

---

### Task 4: Mobile and Polish Pass

**Files:**
- Modify: `src/components/globe/HeliosGlobePanel.vue`
- Modify: `src/components/globe/HeliosCobeGlobe.vue`
- Optional modify: `src/components/home/HomeGlobePlaceholder.vue`

- [ ] **Step 1: Collapse the desktop overlay layout for mobile**

Add responsive rules in `src/components/globe/HeliosGlobePanel.vue`:

```css
@media (max-width: 960px) {
  .globe-hero__stage {
    min-height: auto;
    gap: 1rem;
    padding-top: 0.5rem;
  }

  .globe-hero__orbital,
  .globe-hero__rail,
  .globe-hero__strip {
    position: static;
    transform: none;
    width: 100%;
  }

  .globe-hero__core {
    width: 100%;
  }
}
```

- [ ] **Step 2: Reduce selector clutter inside the globe on small screens**

Add a mobile rule in `src/components/globe/HeliosCobeGlobe.vue`:

```css
@media (max-width: 720px) {
  .cobe-globe {
    min-height: 22rem;
  }

  .cobe-globe__selector-strip {
    justify-content: center;
  }

  .cobe-globe__selector {
    min-width: 7rem;
  }
}
```

- [ ] **Step 3: Run the final verification set**

Run:

```powershell
npm run test -- src/composables/useStagedReveal.test.ts
npm run test -- src/composables/useCobeGlobeData.test.ts
npm run build
```

Expected:

- Both tests pass.
- Build passes.
- The existing `src/composables/useCobeGlobeData.test.ts` warning from `solar.ts` may still appear, but there should be no failing tests.

- [ ] **Step 4: Commit**

```powershell
git add src/components/globe/HeliosGlobePanel.vue src/components/globe/HeliosCobeGlobe.vue src/components/globe/GlobeOrbitalContext.vue src/components/globe/GlobeComparisonHud.vue src/components/globe/GlobeStatStrip.vue
git commit -m "Polish globe hero overlays and mobile layout"
```

---

## Self-Review

### Spec coverage

- globe dominance is implemented in Task 3
- top-left orbital card is handled in Task 2
- right-side destination rail is handled in Task 2 and Task 3
- bottom stat strip is handled in Task 1 and Task 3
- reduced center copy is handled in Task 3
- responsive behavior is handled in Task 4

### Placeholder scan

- no TODO or TBD placeholders remain
- each task names exact files and commands

### Type consistency

- `selectedDestinationId`, `selectedComparison`, `currentSnapshot`, and `comparisons` match the existing globe feature API
- new strip props use strings only to keep the presentation boundary simple
