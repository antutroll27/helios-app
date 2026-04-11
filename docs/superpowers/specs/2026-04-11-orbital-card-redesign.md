# Orbital Card Redesign — Spec

## Goal

Replace the glassmorphism overlay card on the HELIOS globe panel with a solid, nectarine-tinted instrument card that matches the visual language of the new protocol cards — rich warm background, elevation angle as the hero number, no left accent bar.

## Context

The globe panel (`HeliosGlobePanel.vue`) renders an overlay in the top-left corner of the COBE globe. It currently has two visual layers:

1. **`globe-panel__intro-slab`** — a glassmorphism card (dark bg + backdrop-filter blur + border) wrapping:
   - A floating header (HELIOS · COBE, Orbital View title, route status)
   - `GlobeOrbitalContext.vue` — the data section (location, solar phase, elevation, bar, summary)

2. The new design splits these: the header becomes bare floating text (no card), and `GlobeOrbitalContext` becomes the solid card.

> **`color-mix()` browser support note:** `color-mix(in srgb, ...)` requires Chrome 111+, Firefox 113+, Safari 16.2+. This is acceptable for HELIOS's modern PWA audience. No fallback needed.

## Files to Modify

| File | Change |
|---|---|
| `src/components/globe/HeliosGlobePanel.vue` | Strip `.globe-panel__intro-slab` card styles; remove intro-rule; thread `routeLabel` prop; remove 720px responsive overrides for slab |
| `src/components/globe/GlobeOrbitalContext.vue` | Full restyle — becomes the solid nectarine card; add `routeLabel` prop |

---

## Section 1 — HeliosGlobePanel.vue

### `.globe-panel__intro-slab` — remove card styles

Replace the current card styling (border, background gradient, backdrop-filter, box-shadow, border-radius, padding) with a bare flex column:

```css
.globe-panel__intro-slab {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
```

The header elements (`.globe-panel__eyebrow`, `.globe-panel__title`, `.globe-panel__status`) retain their existing typography styles — no changes needed there.

### Remove the 720px responsive override for `.globe-panel__intro-slab`

Inside the `@media (max-width: 720px)` block, delete the entire `.globe-panel__intro-slab` rule (currently sets `gap`, `padding`, `border-radius`). These were card properties — they are no longer relevant on a bare flex column.

### Remove `.globe-panel__intro-rule`

Remove the `<div class="globe-panel__intro-rule" aria-hidden="true">` from the template and its CSS rule. The hairline separator is no longer needed once the slab has no card background.

### Thread `routeLabel` to `GlobeOrbitalContext`

`selectedComparison` is already destructured in this component from `useCobeGlobeData()`. Pass its label as a new prop:

```html
<GlobeOrbitalContext
  :context="orbitalContext"
  :current="currentSnapshot"
  :solar="localSolar"
  :route-label="selectedComparison?.label"
/>
```

---

## Section 2 — GlobeOrbitalContext.vue

### Props — add `routeLabel`

Replace the existing `interface Props` block in its entirety with the one below (`defineProps<Props>()` requires no other change):

```typescript
interface Props {
  context: OrbitalContext   // label (mode tag), summary
  current: CurrentAnchor    // label (location name)
  solar: SolarAnchor        // phase, elevationDeg
  routeLabel?: string       // destination name e.g. "Tokyo" — undefined in baseline view
}
```

### Script changes

- **Keep `isBelowHorizon` computed** — it drives bar fill opacity (text dimming is removed; this computed is still needed for the bar)
- **Keep `elevationPct` computed** — unchanged, drives bar width

### Template restructure

New layout (top to bottom):

```
┌──────────────────────────────────────┐
│ SOLAR CONTEXT          ● HIGH SUN    │  top row: chip + solar phase pill
│                                      │
│ 67 . 8 °                             │  hero: elevation angle (large mono, split spans)
│ SOLAR ELEVATION · KOLKATA, INDIA     │  sublabel: context line
│ ────────────────────────────────     │  hairline (warm tint)
│ [████████████░░░░░░░░░░░░░░░░░░░░]  │  4px elevation bar (warm fill)
│                                      │
│ SOLAR PHASE       ROUTE              │  two-col stats
│ High Sun          → Tokyo            │  (ROUTE shows only when routeLabel defined)
│                                      │
│ ISS orbital context. Observational…  │  summary (0.58rem, muted warm)
└──────────────────────────────────────┘
Padding: 0.9rem 0.9rem 0.8rem 1rem
Border-radius: 1rem
```

**Hero number template structure:**

`props.solar.elevationDeg.toFixed(1)` returns a string such as `"67.8"`. Split on `"."` and wrap each segment in a `<span>`:

```html
<div class="elev-hero">
  <span class="h-int">{{ intPart }}</span>
  <span class="h-sep">.</span>
  <span class="h-dec">{{ decPart }}</span>
  <span class="h-sym">°</span>
</div>
```

Where in `<script setup>`:
```typescript
const elevStr = computed(() => props.solar.elevationDeg.toFixed(1))
const intPart = computed(() => elevStr.value.split('.')[0])
const decPart = computed(() => elevStr.value.split('.')[1] ?? '0')
```

**Stats right column — `routeLabel` vs fallback:**

```html
<div class="stat">
  <template v-if="props.routeLabel">
    <span class="stat-label">Route</span>
    <span class="stat-value">→ {{ props.routeLabel }}</span>
  </template>
  <template v-else>
    <span class="stat-label">Elevation</span>
    <span class="stat-value">{{ solar.elevationDeg.toFixed(1) }}°</span>
  </template>
</div>
```

### Visual Design

Replace the entire `<style scoped>` block. All existing class rules are superseded by the rules below.

**Chip text change:** The top-left label changes from `ORBITAL VIEW` to `SOLAR CONTEXT` — this is a template content change, not caught by TypeScript.

**Card shell:**
- `background: color-mix(in srgb, #FFBD76 26%, #07111a)` — rich nectarine tint, fully opaque
- `border-radius: 1rem`
- `padding: 0.9rem 0.9rem 0.8rem 1rem`
- `gap: 0` — all internal spacing is driven by per-element `margin-bottom`; no flex/grid gap on the card shell
- No `border-left` bar, no `::before` pseudo-element
- No `backdrop-filter`

**Top row:**
- Left: `SOLAR CONTEXT` chip — `0.41rem` JetBrains Mono, weight `700`, `letter-spacing: 0.18em`, `color: rgba(255,220,160,0.7)`
- Right: solar phase pill — `background: rgba(255,189,118,0.18)`, `color: #FFBD76`, `0.39rem` mono, `padding: 0.16rem 0.42rem`, `border-radius: 20px`
  - Dot indicator: inline `<span class="pill-dot">` — `display: inline-block`, `width: 3.5px`, `height: 3.5px`, `border-radius: 50%`, `background: currentColor` (inherits `#FFBD76`), positioned to the left of the phase label text

**Hero number:**

```css
.elev-hero {
  display: flex;
  align-items: baseline;
  gap: 0.08rem;
  margin-bottom: 0.26rem;
}
.h-int, .h-dec {
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
```

**Sublabel:**
- `SOLAR ELEVATION · {location}` — `0.4rem` JetBrains Mono, weight `500`, `letter-spacing: 0.12em`, `color: rgba(255,220,160,0.55)`, `margin-bottom: 0.62rem`
- Location is `props.current.label` — apply `text-transform: uppercase` via CSS

**Hairline:**
- `height: 1px`, `background: rgba(255,189,118,0.15)`, `margin-bottom: 0.62rem`

**Elevation bar:**
- Track: `height: 4px`, `border-radius: 2px`, `background: rgba(255,189,118,0.12)`, `margin-bottom: 0.68rem`, `overflow: hidden`
- Fill: `background: linear-gradient(90deg, rgba(255,189,118,0.5), #FFBD76)`, `width: elevationPct + '%'`, `transition: width 1.2s ease, opacity 0.6s ease`
- When `isBelowHorizon` is true: apply `:style="{ opacity: isBelowHorizon ? 0.25 : 1 }"` to the fill element

**Stats — two columns:**
- Container: `display: flex`, no gap (divider is a border)
- Each stat: `flex: 1`, `display: flex`, `flex-direction: column`, `gap: 0.14rem`
- Divider between stats: `border-left: 1px solid rgba(255,189,118,0.12)`, `padding-left: 0.6rem` on right stat
- Label: `0.37rem` mono, weight `700`, `letter-spacing: 0.14em`, `color: rgba(255,220,160,0.52)`
- Value: `0.68rem` mono, weight `700`, `letter-spacing: -0.02em`, `color: rgba(255,245,225,0.92)`
- Left stat: always `SOLAR PHASE` → `props.solar.phase`
- Right stat: `ROUTE → routeLabel` when `routeLabel` is defined; `ELEVATION → elevationDeg.toFixed(1)°` otherwise

**Summary:**
- `font-size: 0.58rem`, `line-height: 1.45`, `color: rgba(255,220,160,0.38)`, `margin: 0`
- Content: `props.context.summary`

### Responsive

Keep existing breakpoints, updated for new warm colours:

```css
@media (max-width: 640px) {
  .orbital-facts {
    flex-direction: column;
    gap: 0.375rem;
  }
  .orbital-fact-divider { display: none; }
}
@media (max-width: 600px) {
  .orbital-summary { display: none; }
}
```

---

## What Does Not Change

- `elevationPct` computed logic — unchanged
- Responsive breakpoints for the overlay position (`.globe-panel__overlay--intro`) — unchanged
- The globe, stat strip, comparison HUD — untouched
- Existing typography styles on `.globe-panel__eyebrow`, `.globe-panel__title`, `.globe-panel__status`

## Verification

1. `npm run build` — zero TypeScript errors
2. Card renders with solid nectarine background (no glassmorphism), no left border bar, no backdrop blur visible
3. Header text (HELIOS / COBE, Orbital View, route) floats freely above the card with no enclosing box
4. Elevation bar width tracks `elevationPct` at runtime
5. Night mode test: temporarily set `elevationDeg` to `-10` in `useCobeGlobeData.ts` (or via browser devtools overriding the computed) — bar fill should dim to `opacity: 0.25`
6. With a destination selected (e.g. Tokyo): right stat shows `ROUTE → Tokyo`; in baseline view (no destination): right stat shows `ELEVATION → 67.8°`
7. Responsive: at 640px viewport width → stats stack vertically; at 600px → summary text hidden
8. All existing overlay positioning breakpoints (`.globe-panel__overlay--intro`) remain intact
