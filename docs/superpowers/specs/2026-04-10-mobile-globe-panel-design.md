# Mobile Globe Panel — Streamlined Overlays

**Date:** 2026-04-10
**Scope:** `HeliosGlobePanel.vue`, `GlobeOrbitalContext.vue`
**Status:** Approved

---

## Problem

At ≤ 720px the globe panel has two absolute-positioned overlays competing for space:
- Orbital context card (top-left, `~13rem` wide)
- Comparison HUD rail (top-right, `~13rem` wide)

On a 375px phone viewport both cards overlap, the globe is barely visible, and the layout is broken.

## Decision

**Option B — Streamlined Overlays:** keep the globe as a full-bleed hero background. Collapse the comparison HUD to a floating pill. The orbital context card stretches full-width at the top as a slim instrument strip.

---

## Design

### New Breakpoint

Add `≤ 600px` as the phone-specific breakpoint. Existing `720px` and `1100px` breakpoints remain.

---

### 1. Orbital Context Card (top strip)

**In `HeliosGlobePanel.vue`** — add to the `@media (max-width: 600px)` block:
```css
.globe-panel__overlay--intro {
  left: 0.75rem;
  right: 0.75rem;
  width: auto;
  top: 0.75rem;
}
```

**In `GlobeOrbitalContext.vue`** — add a `@media (max-width: 600px)` block:
```css
@media (max-width: 600px) {
  .orbital-summary { display: none; }
  .orbital-card { gap: 0.35rem; }
}
```

---

### 2. Comparison HUD (collapsible)

#### Reactive flags in `<script setup>`

Add `ref` to the existing Vue import. Add after existing refs:

```ts
// Mobile rail toggle
const showRail = ref(false)
const isMobile = ref(false)  // initialized false; set correctly in onMounted (avoids SSR/window hazard)

const handleResize = () => { isMobile.value = window.innerWidth <= 600 }

onMounted(() => {
  handleResize()                                   // set correct value after mount
  window.addEventListener('resize', handleResize)
})
onUnmounted(() => window.removeEventListener('resize', handleResize))
// onUnmounted is at top level of <script setup>, not nested inside onMounted
```

#### Apply `v-show` to HUD

Replace the existing `<GlobeComparisonHud ...>` element with:

```html
<!-- All attributes/props unchanged; add v-show and updated @select-destination -->
<GlobeComparisonHud
  v-show="!isMobile || showRail"
  class="..."
  :comparisons="comparisons"
  :selected-destination-id="selectedDestinationId"
  @select-destination="(id) => { selectDestination(id); showRail.value = false }"
/>
```

- `v-show="!isMobile || showRail"` — on desktop (`isMobile.value` false) the HUD is always visible via existing CSS; on mobile it is visible only when `showRail.value` is true.
- `@select-destination` handler also resets `showRail.value = false` to auto-collapse after city selection.
- `selectDestination` accepts a plain `string` (existing function signature unchanged).

#### HUD mobile CSS

In `HeliosGlobePanel.vue` at `@media (max-width: 600px)`:

```css
.globe-panel__overlay--rail {
  top: auto;
  bottom: 5.5rem;
  right: 0.75rem;
  left: auto;
  transform: none;
  max-width: min(14rem, calc(100% - 1.5rem));
  z-index: 1;   /* below pill (z-index: 2) so pill stays tappable when HUD is open */
}
```

---

### 3. Floating Pill Button

Add as a sibling overlay in `HeliosGlobePanel.vue` template (after the rail overlay div). All expressions are **template context** — Vue auto-unwraps `selectedComparison` (a computed ref) so `.value` is not written explicitly.

```html
<button
  v-if="isMobile"
  class="globe-panel__dest-pill font-mono"
  type="button"
  @click="showRail.value = !showRail.value"
>
  <span v-if="selectedComparison" class="globe-panel__dest-pill-dot" />
  {{ selectedComparison?.label ?? 'DEST' }} ↗
</button>
```

Scoped CSS — note `font-size` is in scoped CSS (not a Tailwind arbitrary bracket value):

```css
.globe-panel__dest-pill {
  position: absolute;
  z-index: 2;            /* above rail (z-index: 1) so pill remains tappable */
  bottom: 5rem;
  right: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.32rem 0.6rem;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  background: rgba(7, 14, 27, 0.82);
  backdrop-filter: blur(12px);
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

/* Pill is mobile-only — hidden at desktop */
@media (min-width: 601px) {
  .globe-panel__dest-pill { display: none; }
}
```

---

### 4. Globe Stage

In `HeliosGlobePanel.vue` at `@media (max-width: 600px)`:
```css
.globe-panel__stage {
  padding-top: 5.5rem;
}
```

---

### 5. Stat Strip

No changes. Already flex-wraps at 720px and sits at `bottom: 0.75rem`. The pill at `bottom: 5rem` provides ~4rem clearance above it.

---

## Files Changed

| File | Change |
|---|---|
| `HeliosGlobePanel.vue` | Add `ref` to Vue import; add `showRail`, `isMobile`, `handleResize`, `onMounted`/`onUnmounted`; update HUD `v-show` + `@select-destination`; add pill button HTML; add `≤ 600px` CSS for intro, rail, stage, pill |
| `GlobeOrbitalContext.vue` | Add `@media (max-width: 600px)` — hide summary, tighten gap |

`GlobeComparisonHud.vue` — **no changes.**

---

## Success Criteria

1. At 375px: orbital context card spans full width at top, no overlap with any element
2. Comparison HUD hidden on load; `DEST ↗` pill visible bottom-right
3. Tapping pill toggles HUD open/closed; selecting a city auto-collapses HUD
4. At > 600px: pill hidden, rail HUD visible via existing positioning (no regression)
5. Globe visible as hero background on mobile
6. `npm run build` passes with zero TypeScript errors
