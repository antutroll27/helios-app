# Orbital Instrument UI Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine the homepage globe support UI into a more authored orbital instrument system without changing the globe data model or page architecture.

**Architecture:** Keep [`HeliosGlobePanel.vue`](../../../../src/components/globe/HeliosGlobePanel.vue) as the composition surface and keep the COBE renderer isolated in [`HeliosCobeGlobe.vue`](../../../../src/components/globe/HeliosCobeGlobe.vue). Concentrate the redesign inside the left intro cluster, destination rail, bottom telemetry widgets, and globe loading state so the hero keeps the globe as the visual anchor while the supporting modules adopt a tighter engineered surface language.

**Tech Stack:** Vue 3, `<script setup lang="ts">`, Vite, scoped CSS, existing Pinia-backed homepage stores.

---

## File Map

### Primary files

- Modify: `src/components/globe/HeliosGlobePanel.vue`
- Modify: `src/components/globe/GlobeOrbitalContext.vue`
- Modify: `src/components/globe/GlobeComparisonHud.vue`
- Modify: `src/components/home/HomeGlobePlaceholder.vue`

### Secondary files

- Modify: `src/components/SpaceWeatherGauge.vue`
- Modify: `src/components/SocialJetLagScore.vue`
- Modify: `src/components/EnvironmentBadge.vue`
- Optional modify: `src/pages/HomePage.vue`

### Responsibility split

- `src/components/globe/HeliosGlobePanel.vue`
  - unified hero composition
  - intro slab placement
  - route chip placement
  - backdrop spacing for the refined modules
- `src/components/globe/GlobeOrbitalContext.vue`
  - current frame instrument module
  - compact facts, stronger hierarchy, shorter support copy
- `src/components/globe/GlobeComparisonHud.vue`
  - destination control column
  - active state treatment
  - tighter internal geometry
- `src/components/SpaceWeatherGauge.vue`
  - geomagnetic telemetry presentation only
- `src/components/SocialJetLagScore.vue`
  - alignment telemetry presentation only
- `src/components/EnvironmentBadge.vue`
  - environment telemetry presentation only
- `src/components/home/HomeGlobePlaceholder.vue`
  - boot-sequence / calibration loading surface
- `src/pages/HomePage.vue`
  - wrapper card shells only if the redesigned widgets need the outer `data-card` framing reduced or removed

---

### Task 1: Recompose the Orbital Intro Cluster

**Files:**
- Modify: `src/components/globe/HeliosGlobePanel.vue`
- Modify: `src/components/globe/GlobeOrbitalContext.vue`

- [ ] **Step 1: Restructure the panel header so the route chip lives inside the left intro cluster**

Update `src/components/globe/HeliosGlobePanel.vue` so the intro overlay becomes one cluster instead of a title block plus a detached status pill:

```vue
<div class="globe-panel__overlay globe-panel__overlay--intro">
  <section class="globe-panel__intro-slab" aria-label="Orbital intro panel">
    <header class="globe-panel__header">
      <p class="globe-panel__eyebrow">HELIOS / COBE</p>
      <h2 class="globe-panel__title">Orbital View</h2>
      <p class="globe-panel__status">{{ headerStatus }}</p>
    </header>

    <div class="globe-panel__intro-rule" aria-hidden="true" />

    <GlobeOrbitalContext
      :context="orbitalContext"
      :current="currentSnapshot"
      :solar="localSolar"
    />
  </section>
</div>
```

- [ ] **Step 2: Replace the current soft intro styles with a single engineered slab**

Update the `src/components/globe/HeliosGlobePanel.vue` styles around the intro cluster:

```css
.globe-panel__overlay--intro {
  top: 1.25rem;
  left: 1.25rem;
  width: min(21rem, 36vw);
}

.globe-panel__intro-slab {
  display: grid;
  gap: 0.9rem;
  padding: 1rem 1rem 1.05rem;
  border-radius: 1.2rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    linear-gradient(180deg, rgba(7, 14, 27, 0.92), rgba(7, 14, 27, 0.72)),
    radial-gradient(circle at top left, rgba(99, 228, 255, 0.08), transparent 42%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 22px 46px rgba(2, 8, 20, 0.26);
  backdrop-filter: blur(18px);
}

.globe-panel__header {
  gap: 0.32rem;
}

.globe-panel__status {
  justify-self: start;
  padding: 0.34rem 0.72rem;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(4, 10, 21, 0.72);
  font-size: 0.62rem;
  letter-spacing: 0.16em;
}

.globe-panel__intro-rule {
  height: 1px;
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.28), transparent);
}
```

- [ ] **Step 3: Redesign the current-frame module to feel like an instrument face**

Update `src/components/globe/GlobeOrbitalContext.vue`:

```vue
<template>
  <section class="orbital-card" aria-label="Orbital context HUD">
    <div class="orbital-card__header">
      <div class="orbital-card__meta">
        <p class="orbital-card__eyebrow">Current frame</p>
        <span class="orbital-card__badge">{{ context.label }}</span>
      </div>
      <h3 class="orbital-card__title">{{ current.label }}</h3>
    </div>

    <dl class="orbital-card__facts">
      <div class="orbital-card__fact">
        <dt>Solar phase</dt>
        <dd>{{ solar.phase }}</dd>
      </div>
      <div class="orbital-card__fact">
        <dt>Elevation</dt>
        <dd>{{ solar.elevationDeg.toFixed(1) }}&deg;</dd>
      </div>
    </dl>

    <p class="orbital-card__summary">{{ context.summary }}</p>
  </section>
</template>
```

Use a flatter module treatment:

```css
.orbital-card {
  gap: 0.82rem;
  padding: 0;
  max-width: none;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.orbital-card__fact {
  border-radius: 0.85rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(3, 10, 22, 0.42);
}

.orbital-card__summary {
  max-width: 16rem;
  font-size: 0.74rem;
  color: rgba(226, 232, 240, 0.68);
}
```

- [ ] **Step 4: Run the build to verify the new cluster compiles**

Run:

```powershell
npm run build
```

Expected:

- Build passes.
- The left intro area renders as one visual cluster.

- [ ] **Step 5: Commit**

```powershell
git add src/components/globe/HeliosGlobePanel.vue src/components/globe/GlobeOrbitalContext.vue
git commit -m "Refine globe orbital intro cluster"
```

---

### Task 2: Turn the Destination Rail into a Control Column

**Files:**
- Modify: `src/components/globe/GlobeComparisonHud.vue`
- Modify: `src/components/globe/HeliosGlobePanel.vue`

- [ ] **Step 1: Tighten the destination rail structure**

Update `src/components/globe/GlobeComparisonHud.vue`:

```vue
<template>
  <section class="comparison-rail" aria-label="Destination comparison HUD">
    <div class="comparison-rail__heading">
      <p class="comparison-rail__eyebrow">Destinations</p>
      <h3 class="comparison-rail__title">Choose a city</h3>
    </div>

    <div v-if="displayedComparisons.length" class="comparison-rail__list">
      <button
        v-for="comparison in displayedComparisons"
        :key="comparison.id"
        type="button"
        class="comparison-rail__item"
        :class="{ 'comparison-rail__item--active': comparison.id === props.selectedDestinationId }"
        :aria-pressed="comparison.id === props.selectedDestinationId"
        @click="handleSelect(comparison.id)"
      >
        <div class="comparison-rail__row">
          <strong class="comparison-rail__label">{{ comparison.label }}</strong>
          <span class="comparison-rail__delta">{{ formatSignedHours(comparison.timezoneDeltaHours) }}</span>
        </div>
        <p class="comparison-rail__status">{{ comparison.travelReadiness }}</p>
        <span v-if="comparison.id === props.selectedDestinationId" class="comparison-rail__selected">Active</span>
      </button>
    </div>
  </section>
</template>
```

- [ ] **Step 2: Restyle the rail as a monolithic selector column**

Replace the main styles in `src/components/globe/GlobeComparisonHud.vue` with a more technical treatment:

```css
.comparison-rail {
  gap: 0.85rem;
  padding: 0.92rem 0.92rem 0.96rem;
  max-width: 15rem;
  border-radius: 1.15rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    linear-gradient(180deg, rgba(7, 14, 27, 0.9), rgba(7, 14, 27, 0.72)),
    radial-gradient(circle at top right, rgba(94, 234, 212, 0.08), transparent 46%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 20px 42px rgba(2, 8, 20, 0.22);
}

.comparison-rail__item {
  gap: 0.44rem;
  border-radius: 0.95rem;
  padding: 0.78rem 0.8rem;
  background: rgba(4, 10, 21, 0.56);
}

.comparison-rail__item--active {
  border-color: rgba(0, 212, 170, 0.52);
  background:
    linear-gradient(180deg, rgba(4, 10, 21, 0.82), rgba(4, 10, 21, 0.64)),
    linear-gradient(90deg, rgba(0, 212, 170, 0.08), transparent 48%);
  box-shadow:
    inset 0 0 0 1px rgba(0, 212, 170, 0.08),
    0 16px 28px rgba(0, 212, 170, 0.08);
}

.comparison-rail__delta {
  color: rgba(94, 234, 212, 0.96);
}
```

- [ ] **Step 3: Nudge the rail placement so it reads as a vertical control column**

Update `src/components/globe/HeliosGlobePanel.vue`:

```css
.globe-panel__overlay--rail {
  top: 50%;
  right: 1.25rem;
  transform: translateY(-52%);
  max-width: min(15rem, 24vw);
}
```

- [ ] **Step 4: Run the build**

Run:

```powershell
npm run build
```

Expected:

- Build passes.
- Active destination state is legible without looking like a generic app card.

- [ ] **Step 5: Commit**

```powershell
git add src/components/globe/GlobeComparisonHud.vue src/components/globe/HeliosGlobePanel.vue
git commit -m "Refine globe destination control rail"
```

---

### Task 3: Recast the Bottom Widgets as Telemetry Modules

**Files:**
- Modify: `src/components/SpaceWeatherGauge.vue`
- Modify: `src/components/SocialJetLagScore.vue`
- Modify: `src/components/EnvironmentBadge.vue`
- Optional modify: `src/pages/HomePage.vue`

- [ ] **Step 1: Rebuild the geomagnetic card into a tighter telemetry face**

Update `src/components/SpaceWeatherGauge.vue` so the structure emphasizes system labels, one signal color, and a restrained info grid:

```vue
<template>
  <div class="sw">
    <div class="sw__header">
      <span class="sw__label font-mono">GEOMAGNETIC</span>
      <span class="sw__live font-mono">LIVE</span>
    </div>

    <div class="sw__body">
      <div class="sw__signal" :style="{ color: scoreColor }">
        <component :is="scoreIcon" :size="16" :color="scoreColor" :stroke-width="2.1" />
        <span class="sw__status font-display">{{ sw.disruptionLabel }}</span>
      </div>
      <p class="sw__message">{{ friendlyMessage }}</p>
      <dl class="sw__metrics font-mono">
        <div><dt>Kp</dt><dd>{{ sw.kpIndex.toFixed(1) }}</dd></div>
        <div><dt>Wind</dt><dd>{{ sw.solarWindSpeed }} km/s</dd></div>
      </dl>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Turn the alignment widget into a warm-accent timing instrument**

Update `src/components/SocialJetLagScore.vue`:

```vue
<template>
  <div class="sjl">
    <div class="sjl__header">
      <span class="sjl__label font-mono">{{ copy.label }}</span>
      <span class="sjl__status font-mono" :style="{ color }">{{ status }}</span>
    </div>

    <div class="sjl__body">
      <div class="sjl__readout">
        <span class="sjl__num font-mono" :style="{ color }">{{ minutes }}</span>
        <span class="sjl__unit font-mono">MIN</span>
      </div>
      <p class="sjl__desc">{{ copy.description }}</p>
    </div>
  </div>
</template>
```

Use the warm accent selectively in the styles:

```css
.sjl__readout {
  display: inline-flex;
  align-items: baseline;
  gap: 0.35rem;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 189, 118, 0.24);
  background: rgba(19, 10, 8, 0.42);
}
```

- [ ] **Step 3: Rebuild the environment widget into a compact sensor matrix**

Update `src/components/EnvironmentBadge.vue`:

```vue
<template>
  <div class="env">
    <div class="env__header">
      <span class="env__label font-mono">ENVIRONMENT</span>
      <span class="env__stamp font-mono">LOCAL</span>
    </div>

    <div class="env__grid">
      <div class="env__item">
        <span class="env__k font-mono">UV</span>
        <span class="env__val font-mono" :style="{ color: uvColor }">{{ env.uvIndexNow }}</span>
      </div>
      <div class="env__item">
        <span class="env__k font-mono">TEMP</span>
        <span class="env__val font-mono">{{ Math.round(env.temperatureNow) }}&deg;</span>
      </div>
      <div class="env__item">
        <span class="env__k font-mono">AQI</span>
        <span class="env__val font-mono" :style="{ color: aqiColor }">{{ env.aqiLevel }}</span>
      </div>
      <div class="env__item">
        <span class="env__k font-mono">HUMID</span>
        <span class="env__val font-mono">{{ env.humidity }}%</span>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 4: Remove any now-redundant generic outer card framing**

If the redesigned components already render with their own module shell, simplify `src/pages/HomePage.vue`:

```vue
<div class="data-grid">
  <SpaceWeatherGauge />
  <SocialJetLagScore />
  <EnvironmentBadge />
</div>
```

And trim the outer wrapper styles:

```css
.data-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.85rem;
}
```

If removing the wrappers makes the row feel too loose, keep the wrapper divs and instead restyle `.data-card` into a flatter module shell with tighter radii and finer borders.

- [ ] **Step 5: Run the build**

Run:

```powershell
npm run build
```

Expected:

- Build passes.
- The three widgets read as telemetry modules instead of generic cards.

- [ ] **Step 6: Commit**

```powershell
git add src/components/SpaceWeatherGauge.vue src/components/SocialJetLagScore.vue src/components/EnvironmentBadge.vue src/pages/HomePage.vue
git commit -m "Refine homepage telemetry modules"
```

---

### Task 4: Replace the Globe Loader with a Calibration Surface

**Files:**
- Modify: `src/components/home/HomeGlobePlaceholder.vue`

- [ ] **Step 1: Replace the generic orbit rings with a boot-sequence layout**

Update `src/components/home/HomeGlobePlaceholder.vue`:

```vue
<template>
  <div class="globe-placeholder" aria-label="Helios globe loading">
    <div class="globe-placeholder__panel">
      <div class="globe-placeholder__topline">
        <span>HELIOS / CALIBRATION</span>
        <span>COBE INIT</span>
      </div>

      <div class="globe-placeholder__scope" aria-hidden="true">
        <div class="globe-placeholder__grid" />
        <div class="globe-placeholder__arc globe-placeholder__arc--outer" />
        <div class="globe-placeholder__arc globe-placeholder__arc--inner" />
        <div class="globe-placeholder__trace" />
      </div>

      <div class="globe-placeholder__copy">
        <p class="globe-placeholder__eyebrow">Planetary model boot</p>
        <h1 class="globe-placeholder__title">Loading orbital frame</h1>
        <p class="globe-placeholder__body">Calibrating destination offsets, solar timing, and local space-weather context.</p>
      </div>

      <div class="globe-placeholder__progress" aria-hidden="true">
        <span class="globe-placeholder__progress-label">SYNC</span>
        <div class="globe-placeholder__progress-bar"><span /></div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Apply the calibration-panel styling**

Use this style direction in `src/components/home/HomeGlobePlaceholder.vue`:

```css
.globe-placeholder__panel {
  display: grid;
  gap: 1rem;
  width: min(48rem, calc(100% - 2rem));
  padding: 1rem 1rem 1.1rem;
  border-radius: 1.35rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    linear-gradient(180deg, rgba(7, 14, 27, 0.92), rgba(7, 14, 27, 0.76)),
    radial-gradient(circle at top right, rgba(94, 234, 212, 0.08), transparent 42%);
}

.globe-placeholder__scope {
  position: relative;
  min-height: 18rem;
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(3, 10, 22, 0.66);
}

.globe-placeholder__progress-bar > span {
  display: block;
  width: 42%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(255, 189, 118, 0.92), rgba(94, 234, 212, 0.82));
}
```

- [ ] **Step 3: Run the staged-load verification**

Run:

```powershell
npm run test -- src/composables/useStagedReveal.test.ts
npm run build
```

Expected:

- The staged reveal test passes.
- Build passes.
- The loader still renders while the async globe chunk is resolving.

- [ ] **Step 4: Commit**

```powershell
git add src/components/home/HomeGlobePlaceholder.vue
git commit -m "Refine orbital globe loading surface"
```

---

### Task 5: Final Alignment and Verification Pass

**Files:**
- Modify: `src/components/globe/HeliosGlobePanel.vue`
- Optional modify: `src/pages/HomePage.vue`

- [ ] **Step 1: Normalize spacing after the module redesign**

Do the final spacing pass in `src/components/globe/HeliosGlobePanel.vue` so the refined modules do not crowd the globe:

```css
.globe-panel__stage {
  padding: clamp(3.8rem, 6vw, 4.8rem) clamp(1rem, 3vw, 2rem) clamp(9.6rem, 14vw, 11rem);
}

.globe-panel__globe {
  width: min(78vw, 63rem);
}

@media (max-width: 720px) {
  .globe-panel__overlay--intro {
    width: min(15.5rem, calc(100% - 5.5rem));
  }

  .globe-panel__overlay--rail {
    max-width: min(13rem, calc(100% - 5rem));
  }
}
```

- [ ] **Step 2: Run the full verification set**

Run:

```powershell
npm run test -- src/composables/useStagedReveal.test.ts
npm run test -- src/composables/useCobeGlobeData.test.ts
npm run build
```

Expected:

- Both tests pass.
- Build passes.
- The homepage still lazy-loads the globe successfully.

- [ ] **Step 3: Commit**

```powershell
git add src/components/globe/HeliosGlobePanel.vue src/components/globe/GlobeOrbitalContext.vue src/components/globe/GlobeComparisonHud.vue src/components/SpaceWeatherGauge.vue src/components/SocialJetLagScore.vue src/components/EnvironmentBadge.vue src/components/home/HomeGlobePlaceholder.vue src/pages/HomePage.vue
git commit -m "Refresh orbital instrument UI surfaces"
```

---

## Self-Review

### Spec coverage

- orbital intro cluster is covered by Task 1
- destination rail is covered by Task 2
- bottom widget redesign is covered by Task 3
- loading-state redesign is covered by Task 4
- overall hierarchy and responsive alignment are covered by Task 5

### Placeholder scan

- no TODO or TBD placeholders remain
- every task names exact files and exact commands
- code-changing steps include concrete Vue or CSS snippets rather than abstract instructions

### Type consistency

- `headerStatus`, `currentSnapshot`, `localSolar`, `comparisons`, and `selectedDestinationId` remain the same `HeliosGlobePanel.vue` API surface
- `GlobeOrbitalContext.vue` keeps the existing `context`, `current`, and `solar` prop contract
- `GlobeComparisonHud.vue` keeps the existing `comparisons`, `selectedDestinationId`, and `select-destination` event contract
- bottom widget plan changes stay presentation-only and do not introduce new store APIs
