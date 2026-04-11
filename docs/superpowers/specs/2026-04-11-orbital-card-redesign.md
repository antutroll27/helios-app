# Orbital Card Redesign — Spec

## Goal

Replace the glassmorphism overlay card on the HELIOS globe panel with a solid, nectarine-tinted instrument card that matches the visual language of the new protocol cards — rich warm background, elevation angle as the hero number, no left accent bar.

## Context

The globe panel (`HeliosGlobePanel.vue`) renders an overlay in the top-left corner of the COBE globe. It currently has two visual layers:

1. **`globe-panel__intro-slab`** — a glassmorphism card (dark bg + backdrop-filter blur + border) wrapping:
   - A floating header (HELIOS · COBE, Orbital View title, route status)
   - `GlobeOrbitalContext.vue` — the data section (location, solar phase, elevation, bar, summary)

2. The new design splits these: the header becomes bare floating text (no card), and `GlobeOrbitalContext` becomes the solid card.

## Files to Modify

| File | Change |
|---|---|
| `src/components/globe/HeliosGlobePanel.vue` | Strip `.globe-panel__intro-slab` of all card styles — becomes a bare flex column |
| `src/components/globe/GlobeOrbitalContext.vue` | Full restyle — becomes the solid nectarine card |

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

### Remove `.globe-panel__intro-rule`

The horizontal rule between header and orbital context is no longer needed once the slab has no card background. Remove the `<div class="globe-panel__intro-rule">` from the template and its CSS rule.

---

## Section 2 — GlobeOrbitalContext.vue

### Template restructure

New layout (top to bottom):

```
┌──────────────────────────────────────┐
│ SOLAR CONTEXT          ● HIGH SUN    │  top row: chip + solar phase pill
│                                      │
│ 67.8°                                │  hero: elevation angle (large mono)
│ SOLAR ELEVATION · KOLKATA, INDIA     │  sublabel: context line
│ ────────────────────────────────     │  hairline (warm tint)
│ [████████████░░░░░░░░░░░░░░░░░░░░]  │  4px elevation bar (warm fill)
│                                      │
│ SOLAR PHASE       ROUTE              │  two-col stats
│ High Sun          → Tokyo            │
│                                      │
│ ISS orbital context. Observational…  │  summary (0.58rem, muted warm)
└──────────────────────────────────────┘
Padding: 0.9rem 0.9rem 0.8rem 1rem
Border-radius: 1rem
```

### Script changes

- Remove `isBelowHorizon` computed (no longer dims text — handled by `elevationPct` bar opacity)
- Keep `elevationPct` computed (unchanged — drives bar width)
- Add `isBelowHorizon` back only if needed for the `--dim` stat class on the elevation value

### Props — unchanged

```typescript
interface Props {
  context: OrbitalContext   // label, summary
  current: CurrentAnchor    // label (location name)
  solar: SolarAnchor        // phase, elevationDeg
}
```

### Visual Design

**Card shell:**
- `background: color-mix(in srgb, #FFBD76 26%, #07111a)` — rich nectarine tint, fully opaque
- `border-radius: 1rem`
- `padding: 0.9rem 0.9rem 0.8rem 1rem`
- No `border-left` bar, no `::before` pseudo-element
- No `backdrop-filter`

**Top row:**
- Left: `SOLAR CONTEXT` chip — `0.41rem` JetBrains Mono, weight `700`, `letter-spacing: 0.18em`, `color: rgba(255,220,160,0.7)`
- Right: solar phase pill — `background: rgba(255,189,118,0.18)`, `color: #FFBD76`, `0.39rem` mono, `padding: 0.16rem 0.42rem`, `border-radius: 20px`, with a `3.5px` filled dot indicator

**Hero number:**
- Integer part + decimal part: `2.2rem`, weight `800`, `letter-spacing: -0.04em`, `color: rgba(255,245,225,0.97)`
- Decimal separator `.`: same size, weight `300`, `opacity: 0.22`
- Degree symbol `°`: `0.8rem`, weight `600`, `color: rgba(255,220,160,0.65)`, aligned to baseline

**Sublabel:**
- `SOLAR ELEVATION · {location}` — `0.4rem` JetBrains Mono, weight `500`, `letter-spacing: 0.12em`, `color: rgba(255,220,160,0.55)`, `margin-bottom: 0.62rem`
- Location is `props.current.label` uppercased via CSS `text-transform: uppercase`

**Hairline:**
- `height: 1px`, `background: rgba(255,189,118,0.15)`, `margin-bottom: 0.62rem`

**Elevation bar:**
- Track: `height: 4px`, `border-radius: 2px`, `background: rgba(255,189,118,0.12)`, `margin-bottom: 0.68rem`
- Fill: `background: linear-gradient(90deg, rgba(255,189,118,0.5), #FFBD76)`, `width: elevationPct + '%'`, `transition: width 1.2s ease`
- When `isBelowHorizon`: fill `opacity: 0.25`

**Stats — two columns:**
- Divider: `border-left: 1px solid rgba(255,189,118,0.12)`
- Label: `0.37rem` mono, weight `700`, `letter-spacing: 0.14em`, `color: rgba(255,220,160,0.52)`
- Value: `0.68rem` mono, weight `700`, `letter-spacing: -0.02em`, `color: rgba(255,245,225,0.92)`
- Left stat: `SOLAR PHASE` → `props.solar.phase`
- Right stat: `ROUTE` → `props.context.label` (which carries the destination label e.g. `"→ Tokyo"`) — falls back to `ELEVATION` → `props.solar.elevationDeg.toFixed(1) + '°'` when context label is the default mode tag

**Summary:**
- `0.58rem`, `line-height: 1.45`, `color: rgba(255,220,160,0.38)`
- Content: `props.context.summary`

### Responsive

Keep existing breakpoints:

```css
@media (max-width: 640px) {
  /* stats stack vertically, divider hidden */
}
@media (max-width: 600px) {
  /* summary hidden */
}
```

---

## What Does Not Change

- Props interface — no additions or removals
- `elevationPct` computed logic — unchanged
- Parent data flow in `HeliosGlobePanel.vue` — `:context`, `:current`, `:solar` bindings unchanged
- Responsive breakpoints for the overlay position (`.globe-panel__overlay--intro`)
- The globe, stat strip, comparison HUD — untouched

## Verification

1. `npm run build` — zero TypeScript errors
2. Card renders with solid nectarine background (no glassmorphism), no left border bar
3. Elevation bar fills correctly at runtime (tracks solar elevation 0–90°)
4. At night (`elevationDeg < 0`): bar fill dims to opacity 0.25
5. Header text (HELIOS · COBE, Orbital View, route) floats freely above card with no enclosing box
6. Responsive: 640px → stats stack; 600px → summary hides
7. All existing breakpoints for overlay positioning remain intact
