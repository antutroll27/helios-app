# Mobile Globe Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the globe panel section work correctly on phones (≤ 600px) by stretching the orbital context card full-width and collapsing the comparison HUD into a floating pill toggle.

**Architecture:** Two files change. `HeliosGlobePanel.vue` gets a `isMobile` / `showRail` reactive pair, a named-method pill toggle, a floating pill button element, and a `@media (max-width: 600px)` CSS block. `GlobeOrbitalContext.vue` gets a single `@media (max-width: 600px)` block that hides the summary and tightens the gap. No new files, no new components.

**Tech Stack:** Vue 3 Composition API (`<script setup>`), TypeScript, scoped CSS (no Tailwind arbitrary bracket values — all values in `<style scoped>`), Vite 8.

---

## File Map

| File | Action | What changes |
|---|---|---|
| `helios-app/src/components/globe/HeliosGlobePanel.vue` | Modify | Script: import additions, reactive refs, named methods. Template: `v-show` on HUD, updated event handler, pill button. Style: `@media (max-width: 600px)` block for intro / rail / stage / pill. |
| `helios-app/src/components/globe/GlobeOrbitalContext.vue` | Modify | Style only: `@media (max-width: 600px)` block. |

`GlobeComparisonHud.vue` — **no changes.**

---

## Task 1: Add reactive refs and named methods to HeliosGlobePanel.vue

**Files:**
- Modify: `helios-app/src/components/globe/HeliosGlobePanel.vue` (script block only)

### Context

The current import line is:
```ts
import { computed } from 'vue'
```

The current `<script setup>` destructures from `useCobeGlobeData()`:
```ts
const {
  currentSnapshot,
  localSolar,
  comparisons,
  selectedComparison,   // ← already exists: ComputedRef<GlobeComparison | undefined>
  selectedDestinationId,
  orbitalContext,
  selectDestination,    // ← already exists: (id: string) => void
} = useCobeGlobeData()
```

Both `selectedComparison` and `selectDestination` are **already declared** in the component — they come from `useCobeGlobeData()`. Do not re-declare them. `onDestinationSelect` (added in this task) calls the existing `selectDestination` function.

- [ ] **Step 1: Update the Vue import**

Replace:
```ts
import { computed } from 'vue'
```
With:
```ts
import { computed, ref, onMounted, onUnmounted } from 'vue'
```

- [ ] **Step 2: Add mobile reactive state after the existing computed values**

After the `headerStatus` and `timingLabel` computed blocks, add:

```ts
// ── Mobile rail toggle ────────────────────────────────────────────────────
const showRail = ref(false)
const isMobile = ref(false)

const handleResize = () => {
  isMobile.value = window.innerWidth <= 600
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

function toggleRail() {
  showRail.value = !showRail.value
}

function onDestinationSelect(id: string) {
  selectDestination(id)
  showRail.value = false
}
```

`isMobile` initialises `false` — `handleResize()` inside `onMounted` sets the correct value after the component mounts, avoiding `window` access during SSR/build.

`onUnmounted` is called at the top level of `<script setup>` (not nested inside `onMounted`) — this is the correct Vue 3 pattern.

Named methods (`toggleRail`, `onDestinationSelect`) are used in the template instead of inline `.value` mutations, keeping template expressions clean and idiomatic.

- [ ] **Step 3: Verify TypeScript — run build**

```bash
cd helios-app && npm run build
```

Expected: `✓ built` with zero TypeScript errors. If `ref`/`onMounted`/`onUnmounted` are not found, check the import line added in Step 1.

---

## Task 2: Update the GlobeComparisonHud usage in the template

**Files:**
- Modify: `helios-app/src/components/globe/HeliosGlobePanel.vue` (template block)

### Context

Current template has:
```html
<div class="globe-panel__overlay globe-panel__overlay--rail">
  <GlobeComparisonHud
    :comparisons="comparisons"
    :selected-destination-id="selectedDestinationId"
    @select-destination="selectDestination"
  />
</div>
```

- [ ] **Step 1: Add v-show and swap the event handler**

Replace the `<GlobeComparisonHud ...>` element with:

```html
<div class="globe-panel__overlay globe-panel__overlay--rail">
  <GlobeComparisonHud
    v-show="!isMobile || showRail"
    :comparisons="comparisons"
    :selected-destination-id="selectedDestinationId"
    @select-destination="onDestinationSelect"
  />
</div>
```

`v-show="!isMobile || showRail"`:
- Desktop (`isMobile` is `false`): `!false` → `true` → HUD always visible
- Mobile (`isMobile` is `true`): only visible when `showRail` is `true`

`@select-destination="onDestinationSelect"` calls the named method that also resets `showRail`.

- [ ] **Step 2: Build check**

```bash
npm run build
```

Expected: `✓ built`.

---

## Task 3: Add the floating pill button to the template

**Files:**
- Modify: `helios-app/src/components/globe/HeliosGlobePanel.vue` (template block)

### Context

The pill button is a mobile-only `<button>` overlay. It sits at `bottom: 4.25rem` (above the stat strip). It uses `v-if="isMobile"` so it does not exist in the DOM on desktop. `selectedComparison` auto-unwraps in the template.

- [ ] **Step 1: Add the pill button element**

Inside `.globe-panel__hero`, after the `globe-panel__overlay--rail` div and before the `globe-panel__overlay--stats` div, add:

```html
<!-- Mobile-only destination pill toggle -->
<button
  v-if="isMobile"
  class="globe-panel__dest-pill font-mono"
  type="button"
  @click="toggleRail"
>
  <span v-if="selectedComparison" class="globe-panel__dest-pill-dot" />
  {{ selectedComparison?.label ?? 'DEST' }} ↗
</button>
```

`v-if="isMobile"` — not rendered on desktop at all (use `v-if` not `v-show` here since the pill has no hidden state on desktop).

`v-if="selectedComparison"` on the dot — auto-unwraps the computed ref in template context; dot is shown only when a destination is actively selected.

- [ ] **Step 2: Build check**

```bash
npm run build
```

Expected: `✓ built`. TypeScript will type-check the template. If `selectedComparison?.label` errors, confirm `GlobeComparison` has a `label: string` field (it does — verified in `GlobeComparisonHud.vue` line 63).

---

## Task 4: Add mobile CSS to HeliosGlobePanel.vue

**Files:**
- Modify: `helios-app/src/components/globe/HeliosGlobePanel.vue` (style block)

### Context

The existing media queries in order are: `@media (max-width: 1100px)`, `@media (max-width: 720px)`. The new `@media (max-width: 600px)` block **must be added after** the `720px` block so it takes precedence over intermediate-width rules via CSS cascade order. All font sizes and spacing values go in scoped CSS — never in Tailwind arbitrary bracket syntax.

Z-index layout:
- `.globe-panel__overlay` (base class): `z-index: 1`
- Rail on mobile: `z-index: 2` — raised above base so it renders above other overlays
- Pill: `z-index: 3` — above the open rail so it stays tappable

Position layout on a 375×667 phone:
- Stat strip: `bottom: 0.75rem`, height ~3.5rem → top edge ~4.25rem
- Pill: `bottom: 4.25rem` (clears stat strip), height ~1.5rem → top edge ~5.75rem
- Rail: `bottom: 6rem` (clears pill with ~0.25rem gap)

- [ ] **Step 1: Add the `@media (max-width: 600px)` block at the END of the `<style scoped>` section**

```css
/* ── Mobile (≤ 600px) ───────────────────────────────────────────────────── */

@media (max-width: 600px) {
  /* Orbital context card — full width strip */
  .globe-panel__overlay--intro {
    top: 0.75rem;
    left: 0.75rem;
    right: 0.75rem;
    width: auto;
  }

  /* Comparison HUD — repositioned above pill when open */
  .globe-panel__overlay--rail {
    top: auto;
    bottom: 6rem;
    right: 0.75rem;
    left: auto;
    transform: none;
    max-width: min(14rem, calc(100% - 1.5rem));
    z-index: 2;
  }

  /* Globe stage — extra top padding to clear full-width intro card */
  .globe-panel__stage {
    padding-top: 5.5rem;
  }

  /* Destination pill — mobile-only floating toggle */
  .globe-panel__dest-pill {
    position: absolute;
    z-index: 3;
    bottom: 4.25rem;
    right: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.32rem 0.6rem;
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 999px;
    background: rgba(7, 14, 27, 0.82);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    color: rgba(241, 245, 249, 0.9);
    font-size: 0.55rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    cursor: pointer;
    appearance: none;
  }

  .globe-panel__dest-pill-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: rgba(255, 189, 118, 0.9);
    flex-shrink: 0;
  }
}

/* Pill is mobile-only — explicitly hidden on desktop */
@media (min-width: 601px) {
  .globe-panel__dest-pill {
    display: none;
  }
}
```

- [ ] **Step 2: Full build check**

```bash
npm run build
```

Expected: `✓ built` with zero errors.

---

## Task 5: Add mobile CSS to GlobeOrbitalContext.vue

**Files:**
- Modify: `helios-app/src/components/globe/GlobeOrbitalContext.vue` (style block only)

### Context

On mobile the card is now full-width. Hiding the summary saves ~2 lines of height. Tightening the gap keeps the card compact enough to not push the globe down too far.

- [ ] **Step 1: Add `@media (max-width: 600px)` block at the END of `<style scoped>`**

```css
@media (max-width: 600px) {
  .orbital-card {
    gap: 0.35rem;
  }

  .orbital-summary {
    display: none;
  }
}
```

- [ ] **Step 2: Final build check**

```bash
npm run build
```

Expected: `✓ built`.

---

## Task 6: Visual verification

**No file changes — verification only.**

- [ ] **Step 1: Start dev server**

```bash
npm run dev
```

- [ ] **Step 2: Open browser DevTools → toggle device emulation → set to iPhone SE (375×667)**

- [ ] **Step 3: Verify the following at 375px**

| Check | Expected |
|---|---|
| Orbital context card | Spans full width minus 0.75rem margins, no overflow |
| Comparison HUD | Not visible on load |
| `DEST ↗` pill | Visible bottom-right, above stat strip |
| Tapping pill | Comparison HUD appears above the pill |
| Selecting Tokyo / London / NYC | HUD collapses after selection |
| Globe | Visible as hero background behind overlays |
| Stat strip | Visible at bottom, not overlapped by pill |

- [ ] **Step 4: Switch to 768px (tablet) — verify no regression**

| Check | Expected |
|---|---|
| Pill | Not visible |
| Comparison HUD | Visible in right rail, normal position |
| Orbital context card | Left-anchored at ~13rem width |

- [ ] **Step 5: Switch to 1280px (desktop) — verify no regression**

Same as tablet check above.

- [ ] **Step 6: Commit**

Commit to `dev` branch (not `master` — master is production, deployed to Vercel).

```bash
cd helios-app
git status   # verify only the two expected files are dirty
git add src/components/globe/HeliosGlobePanel.vue src/components/globe/GlobeOrbitalContext.vue
git commit -m "fix: optimise globe panel for mobile — collapsible HUD pill + full-width orbital strip"
```
