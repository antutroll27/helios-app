# Orbital Card Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the glassmorphism globe overlay card with a solid nectarine-tinted instrument panel — elevation angle as the hero number, no left accent bar, warm internal colours throughout.

**Architecture:** Two files change. `HeliosGlobePanel.vue` strips its outer slab of all card styling (border, background, backdrop-filter) so the header text floats freely. `GlobeOrbitalContext.vue` is fully rewritten to become the solid nectarine card with a new `routeLabel` prop threaded from the parent.

**Tech Stack:** Vue 3 `<script setup>` + TypeScript, scoped CSS (no Tailwind in these components), no new dependencies.

---

## File Map

| File | Role |
|---|---|
| `src/components/globe/HeliosGlobePanel.vue` | Outer container — strips card styling, removes intro-rule, threads `routeLabel` |
| `src/components/globe/GlobeOrbitalContext.vue` | The data card — full rewrite (props, script, template, style) |

---

## Task 1: Update HeliosGlobePanel.vue

**Files:**
- Modify: `src/components/globe/HeliosGlobePanel.vue`

**Background:** The `.globe-panel__intro-slab` currently acts as a glassmorphism card wrapping both the floating header and `GlobeOrbitalContext`. We need to strip it down to a bare flex column, remove the hairline rule element, and pass the selected destination label to `GlobeOrbitalContext` as a new `routeLabel` prop. `selectedComparison` is already available in this component from `useCobeGlobeData()`.

- [ ] **Step 1: Strip card styles from `.globe-panel__intro-slab`**

  In the `<style scoped>` block, find the `.globe-panel__intro-slab` rule (currently has `display: grid`, `gap`, `padding`, `border-radius`, `border`, `background`, `box-shadow`, `backdrop-filter`). Replace it entirely with:

  ```css
  .globe-panel__intro-slab {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }
  ```

- [ ] **Step 2: Remove the 720px responsive override for `.globe-panel__intro-slab`**

  Inside the `@media (max-width: 720px)` block, find and delete **only** the `.globe-panel__intro-slab` rule (it currently sets `gap: 0.82rem`, `padding: 0.92rem 0.92rem 0.98rem`, `border-radius: 1.08rem`). Leave all other rules in that media query intact (`.globe-panel__hero`, `.globe-panel__title`, etc.).

- [ ] **Step 3: Remove `.globe-panel__intro-rule` from the template**

  In `<template>`, find:
  ```html
  <div class="globe-panel__intro-rule" aria-hidden="true" />
  ```
  Delete that line entirely.

- [ ] **Step 4: Remove `.globe-panel__intro-rule` CSS rule**

  In `<style scoped>`, find and delete the `.globe-panel__intro-rule` rule:
  ```css
  .globe-panel__intro-rule {
    height: 1px;
    background: linear-gradient(90deg, rgba(148, 163, 184, 0.28), transparent);
  }
  ```

- [ ] **Step 5: Thread `routeLabel` to `GlobeOrbitalContext`**

  In the template, find the `<GlobeOrbitalContext>` component binding and add the new prop:

  ```html
  <GlobeOrbitalContext
    :context="orbitalContext"
    :current="currentSnapshot"
    :solar="localSolar"
    :route-label="selectedComparison?.label"
  />
  ```

  `selectedComparison` is already destructured from `useCobeGlobeData()` at the top of the script — no import changes needed.

- [ ] **Step 6: Verify build passes**

  ```bash
  cd helios-app && npm run build
  ```

  Expected: zero TypeScript errors. If `selectedComparison` type doesn't have `?.label`, check `useCobeGlobeData.ts` — `selectedComparison` is typed as a `GlobeComparison | null` ref and `.label` is a `string` field on `GlobeComparison`. The optional chaining `?.` handles the null case.

- [ ] **Step 7: Commit**

  ```bash
  git add src/components/globe/HeliosGlobePanel.vue
  git commit -m "feat: strip intro-slab card styles and thread routeLabel to GlobeOrbitalContext"
  ```

---

## Task 2: Rewrite GlobeOrbitalContext.vue

**Files:**
- Modify: `src/components/globe/GlobeOrbitalContext.vue`

**Background:** Full component rewrite — new props, new script computeds for the hero number split, new template layout, new scoped CSS. The entire `<style scoped>` block is replaced. `isBelowHorizon` and `elevationPct` are kept (both drive the bar). Three new computeds are added for splitting the elevation string into integer/decimal parts.

- [ ] **Step 1: Replace the entire component with the new implementation**

  Overwrite `src/components/globe/GlobeOrbitalContext.vue` with:

  ```vue
  <script setup lang="ts">
  import { computed } from 'vue'

  interface OrbitalContext {
    label: string
    summary: string
  }

  interface CurrentAnchor {
    label: string
  }

  interface SolarAnchor {
    phase: string
    elevationDeg: number
  }

  interface Props {
    context: OrbitalContext
    current: CurrentAnchor
    solar: SolarAnchor
    routeLabel?: string
  }

  const props = defineProps<Props>()

  // Solar elevation as % of zenith (90°), clamped 0–100
  const elevationPct = computed(() => {
    if (props.solar.elevationDeg <= 0) return 0
    return Math.min((props.solar.elevationDeg / 90) * 100, 100)
  })

  const isBelowHorizon = computed(() => props.solar.elevationDeg < 0)

  // Split elevation string for mixed-weight hero number
  const elevStr = computed(() => props.solar.elevationDeg.toFixed(1))
  const intPart = computed(() => elevStr.value.split('.')[0])
  const decPart = computed(() => elevStr.value.split('.')[1] ?? '0')
  </script>

  <template>
    <section class="orbital-card" aria-label="Orbital context HUD">

      <!-- Top row: chip + solar phase pill -->
      <div class="card-top">
        <span class="card-chip">Solar Context</span>
        <span class="pill">
          <span class="pill-dot" aria-hidden="true" />
          {{ solar.phase }}
        </span>
      </div>

      <!-- Hero: elevation angle split into int/sep/dec/sym -->
      <div class="elev-hero" :aria-label="`Solar elevation ${solar.elevationDeg.toFixed(1)} degrees`">
        <span class="h-int">{{ intPart }}</span>
        <span class="h-sep" aria-hidden="true">.</span>
        <span class="h-dec">{{ decPart }}</span>
        <span class="h-sym" aria-hidden="true">°</span>
      </div>

      <!-- Sublabel -->
      <p class="elev-sub">Solar Elevation · {{ current.label }}</p>

      <!-- Hairline -->
      <div class="hairline" aria-hidden="true" />

      <!-- Elevation bar -->
      <div
        class="bar-track"
        :aria-label="`Solar elevation: ${solar.elevationDeg.toFixed(1)}°`"
      >
        <div
          class="bar-fill"
          :style="{ width: elevationPct + '%', opacity: isBelowHorizon ? 0.25 : 1 }"
        />
      </div>

      <!-- Stats -->
      <div class="stats">
        <div class="stat">
          <span class="stat-label">Solar Phase</span>
          <span class="stat-value">{{ solar.phase }}</span>
        </div>
        <div class="stat stat--right">
          <template v-if="props.routeLabel">
            <span class="stat-label">Route</span>
            <span class="stat-value">→ {{ props.routeLabel }}</span>
          </template>
          <template v-else>
            <span class="stat-label">Elevation</span>
            <span class="stat-value">{{ solar.elevationDeg.toFixed(1) }}°</span>
          </template>
        </div>
      </div>

      <!-- Summary -->
      <p class="orbital-summary">{{ context.summary }}</p>

    </section>
  </template>

  <style scoped>
  /* ── Card shell ─────────────────────────────────── */
  .orbital-card {
    display: flex;
    flex-direction: column;
    gap: 0;
    background: color-mix(in srgb, #FFBD76 26%, #07111a);
    border-radius: 1rem;
    padding: 0.9rem 0.9rem 0.8rem 1rem;
  }

  /* ── Top row ────────────────────────────────────── */
  .card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.6rem;
  }

  .card-chip {
    font-family: var(--font-mono);
    font-size: 0.41rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: rgba(255, 220, 160, 0.7);
  }

  .pill {
    display: flex;
    align-items: center;
    gap: 0.28rem;
    padding: 0.16rem 0.42rem;
    border-radius: 20px;
    background: rgba(255, 189, 118, 0.18);
    color: #FFBD76;
    font-family: var(--font-mono);
    font-size: 0.39rem;
    font-weight: 600;
    letter-spacing: 0.11em;
    text-transform: uppercase;
  }

  .pill-dot {
    display: inline-block;
    width: 3.5px;
    height: 3.5px;
    border-radius: 50%;
    background: currentColor;
    flex-shrink: 0;
  }

  /* ── Hero elevation number ──────────────────────── */
  .elev-hero {
    display: flex;
    align-items: baseline;
    gap: 0.08rem;
    margin-bottom: 0.26rem;
  }

  .h-int,
  .h-dec {
    font-family: var(--font-mono);
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    color: rgba(255, 245, 225, 0.97);
  }

  .h-sep {
    font-family: var(--font-mono);
    font-size: 2.2rem;
    font-weight: 300;
    opacity: 0.22;
    color: rgba(255, 245, 225, 0.97);
  }

  .h-sym {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    font-weight: 600;
    color: rgba(255, 220, 160, 0.65);
    align-self: flex-end;
    padding-bottom: 0.2rem;
  }

  /* ── Sublabel ───────────────────────────────────── */
  .elev-sub {
    margin: 0 0 0.62rem;
    font-family: var(--font-mono);
    font-size: 0.4rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255, 220, 160, 0.55);
  }

  /* ── Hairline ───────────────────────────────────── */
  .hairline {
    height: 1px;
    background: rgba(255, 189, 118, 0.15);
    margin-bottom: 0.62rem;
  }

  /* ── Elevation bar ──────────────────────────────── */
  .bar-track {
    height: 4px;
    border-radius: 2px;
    background: rgba(255, 189, 118, 0.12);
    margin-bottom: 0.68rem;
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, rgba(255, 189, 118, 0.5), #FFBD76);
    transition: width 1.2s ease, opacity 0.6s ease;
  }

  /* ── Stats ──────────────────────────────────────── */
  .stats {
    display: flex;
    margin-bottom: 0.55rem;
  }

  .stat {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.14rem;
  }

  .stat--right {
    border-left: 1px solid rgba(255, 189, 118, 0.12);
    padding-left: 0.6rem;
  }

  .stat-label {
    font-family: var(--font-mono);
    font-size: 0.37rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(255, 220, 160, 0.52);
  }

  .stat-value {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: rgba(255, 245, 225, 0.92);
  }

  /* ── Summary ────────────────────────────────────── */
  .orbital-summary {
    margin: 0;
    font-size: 0.58rem;
    line-height: 1.45;
    color: rgba(255, 220, 160, 0.38);
  }

  /* ── Responsive ─────────────────────────────────── */
  @media (max-width: 640px) {
    .stats {
      flex-direction: column;
      gap: 0.375rem;
    }
    .stat--right {
      border-left: none;
      padding-left: 0;
    }
  }

  @media (max-width: 600px) {
    .orbital-summary {
      display: none;
    }
  }
  </style>
  ```

- [ ] **Step 2: Verify build passes**

  ```bash
  cd helios-app && npm run build
  ```

  Expected: zero TypeScript errors. Common issues to watch for:
  - If `color-mix()` causes a PostCSS warning — it's fine for this project's target browsers (Chrome 111+)
  - `:aria-label` with a template literal (e.g. `` :aria-label="`Solar elevation ${solar.elevationDeg.toFixed(1)} degrees`" ``) is valid Vue 3 syntax — no workaround needed

- [ ] **Step 3: Visual inspection — start dev server**

  ```bash
  cd helios-app && npm run dev
  ```

  Open `http://localhost:5173`. Check on the globe panel:

  - [ ] Card has solid warm nectarine background — no frosted glass / blur effect visible
  - [ ] No left accent bar
  - [ ] Header (HELIOS / COBE, Orbital View, route) floats above the card with no enclosing box around it
  - [ ] Elevation angle renders as large mono number with faint decimal separator
  - [ ] Sublabel shows `SOLAR ELEVATION · {CITY NAME}` in small caps
  - [ ] Nectarine progress bar is visible and filled proportionally to elevation
  - [ ] Without a destination selected: right stat shows `ELEVATION` with the angle value
  - [ ] Select Tokyo (or any destination) from the comparison rail: right stat switches to `ROUTE → Tokyo`

- [ ] **Step 4: Night mode spot check**

  In `src/composables/useCobeGlobeData.ts`, find where `localSolar` is computed and temporarily hardcode `elevationDeg: -10`. Reload the dev server:

  - [ ] Bar fill dims to low opacity (0.25)
  - [ ] `elevationPct` returns 0, bar fill width is 0%

  - [ ] Revert the hardcoded `elevationDeg` value to the original computed before continuing.

- [ ] **Step 5: Responsive check**

  In browser devtools, drag viewport width to 640px — stats should stack vertically. At 600px — summary text should disappear.

- [ ] **Step 6: Commit**

  ```bash
  git add src/components/globe/GlobeOrbitalContext.vue
  git commit -m "feat: restyle GlobeOrbitalContext as solid nectarine instrument card"
  ```

---

## Final Verification

- [ ] Run `npm run build` one last time — zero errors
- [ ] Both cards (Task 1 + Task 2) look correct together on the live dev server
- [ ] No regressions to the globe, stat strip, or comparison HUD
