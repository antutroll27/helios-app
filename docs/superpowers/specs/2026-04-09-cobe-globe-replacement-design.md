# COBE Globe Replacement Design

Date: 2026-04-09
Status: Proposed
Owner: Codex

## Goal

Replace the current `globe.gl`-based home hero globe with a `COBE`-based interactive globe that is materially lighter, still draggable, and more explicitly useful for HELIOS users.

The replacement should keep the globe as a product surface rather than a decorative animation. It must foreground three user-relevant contexts:

- local solar elevation and solar phase
- ISS / satellite context as ambient orbital awareness
- current location versus multiple saved travel destinations, with clickable focus and comparison stats

## Why This Change

The current staged-loading pass fixed the critical-path route cost, but the `globe.gl` ecosystem still leaves a very large deferred 3D payload. That is acceptable as a short-term mitigation, but not as the long-term homepage globe strategy.

`COBE` is the preferred replacement candidate because it offers:

- a much lighter runtime footprint
- a clean, interactive, draggable globe
- enough flexibility for marker-based overlays and controlled animation
- a visual language that fits a lighter, more intentional HELIOS homepage

The tradeoff is that HELIOS must own more of the overlay logic itself. That is acceptable because the current homepage globe only needs a focused set of overlays, not a full geospatial engine.

## Product Direction

The new globe should be a `COBE + HUD-driven interaction` system.

This means:

- the canvas remains visually clean and interactive
- the globe shows markers, focus state, and subtle contextual overlays
- richer numeric interpretation lives in a compact HUD rather than as dense on-canvas labels
- selecting a destination rotates or recenters the globe and updates the comparison HUD

This avoids both extremes:

- a purely decorative globe with no real utility
- an overloaded geospatial dashboard that hurts readability and mobile performance

## User Experience

### Base state

On staged reveal, the user sees:

- a draggable, gently rotating COBE globe
- a primary marker for current location
- subtle day/night treatment or solar-oriented lighting cue
- ambient orbital context for ISS / satellites
- multiple saved destination markers
- a compact HUD framing the currently selected comparison target

If the user has no saved destinations, the globe still shows:

- current location
- local solar elevation
- ISS / orbital context
- a neutral "add destination" comparison state

### Interaction model

The user can:

- drag the globe
- let the globe idle-rotate when not interacting
- click destination markers
- see the globe refocus on the selected destination
- see comparison stats swap immediately in the HUD

The globe itself is not responsible for large text-heavy data presentation. Its job is:

- spatial orientation
- focus selection
- visual context

### Destination comparison behavior

The comparison system is `current location vs multiple saved destinations`.

Each destination marker should be clickable. When selected:

- the marker becomes visually active
- the globe camera or orientation shifts to make the destination legible
- the comparison HUD updates with current-vs-destination stats

The comparison HUD should include:

- destination name
- timezone delta
- local solar elevation for destination
- sunrise / sunset delta versus current location
- a concise circadian travel-readiness summary

This summary should be lightweight and honest. It should reflect currently available timing math, not imply a clinically validated travel prediction engine.

## Data Surfaces

### 1. Local solar elevation

This is the most personal and defensible globe stat.

The globe should expose:

- current local solar elevation
- current solar phase
- sunrise and sunset context already available in the solar store

This should be reflected through:

- HUD values
- subtle globe lighting or hemisphere treatment
- current-location emphasis

### 2. ISS / satellite context

This should be treated as contextual orbital awareness, not a fake precision feature.

Acceptable initial forms:

- a moving ISS marker if reliable live position data is wired
- a stylized orbital track or badge if only approximate or periodic data is available
- a satellite context panel that explains what the orbital layer represents

The implementation must not imply:

- live high-fidelity multi-satellite tracking unless the actual data path exists
- direct health causality from orbital position

The design intent is:

- "you are situated within a live orbital / solar system context"
- not "this satellite is directly optimizing your biology right now"

### 3. Travel destination comparison

Saved destinations should be first-class globe entities.

Each destination marker should support:

- name
- coordinates
- active / inactive visual state
- click-to-focus interaction

Comparison values should derive from existing or near-existing app data, especially:

- timezone offset
- solar timing
- relative sunrise / sunset context
- future protocol relevance for travel preparation

## Visual Direction

The new COBE globe should be slightly lighter and more graphic than the current `globe.gl` version.

Target qualities:

- still premium and atmospheric
- less photoreal texture dependence
- cleaner glow and marker language
- fewer heavy 3D effects
- stronger HELIOS identity, less generic "NASA globe demo"

Suggested treatment:

- soft atmosphere glow
- subtle shadow / day-night treatment
- current-location marker in HELIOS accent color
- destination markers with active-state scaling or halo
- restrained orbital line or moving point for ISS context

The HUD should remain crisp and mono-instrument-like, matching existing HELIOS interface language.

## Architecture

### Component map

#### `HeliosCobeGlobe.vue`

Responsibility:

- own the COBE canvas
- configure drag / idle rotation behavior
- render current location and destination markers
- expose selection events
- own only globe rendering concerns, not dense comparison logic

#### `useCobeGlobeData.ts`

Responsibility:

- transform app state into globe-ready markers and focus state
- prepare destination comparison data
- prepare local solar context for HUD use
- keep globe-facing data small and explicit

#### `GlobeComparisonHud.vue`

Responsibility:

- render current vs selected destination comparison
- show solar elevation and timing deltas
- show concise travel-readiness summary

#### `GlobeOrbitalContext.vue`

Responsibility:

- show ISS / satellite context summary
- render any small companion stat or badge outside the globe canvas

#### `HomePage.vue`

Responsibility:

- remain a composition surface
- keep async boundary ownership
- swap the current globe wrapper with the new COBE globe container

### Data flow

- stores provide geo, solar, and any saved destination state
- `useCobeGlobeData.ts` derives marker data and comparison state
- `HeliosCobeGlobe.vue` receives focused, presentation-ready marker props
- marker click emits destination selection
- parent or container-level state updates active destination
- HUD components react to selected destination state

This keeps the rendering layer thin and the comparison logic testable.

## Realism Constraints

The new globe must be explicit about what is real data versus visual context.

Allowed:

- real solar timing and solar elevation
- real location-based destination comparisons
- ISS context if backed by a real source or explicitly framed as contextual layer

Not allowed:

- unsupported satellite precision claims
- fake medical implications from orbital context
- travel-readiness summaries that pretend to be validated individualized forecasts

## Error Handling

If destination data is missing:

- render current location only
- show a neutral comparison HUD state

If ISS / orbital context is unavailable:

- degrade to a static orbital badge or hide the orbital layer gracefully
- do not block globe rendering

If COBE initialization fails:

- preserve the staged placeholder and fail to a non-interactive fallback card
- do not break the home route

## Testing Strategy

The implementation should add focused verification around:

- destination selection state
- comparison data derivation
- solar elevation / destination summary formatting
- graceful fallback when orbital data is absent

Bundle verification should compare:

- current `globe.gl`-based async chunk baseline
- new COBE globe chunk output

Success means:

- materially lower deferred globe payload
- preserved drag interaction
- preserved or improved perceived visual quality
- clearer user value through solar / orbital / travel comparison context

## Non-Goals

This pass does not attempt to build:

- a full geospatial platform
- terrain rendering
- photoreal satellite imagery layers
- complex multi-satellite analytics
- a clinically authoritative travel adaptation engine

Those belong to later product expansions if needed.

## Recommendation

Proceed with a `COBE-first replacement spike`.

The spike should:

- replace the current homepage globe implementation
- keep the HUD-driven interaction model
- support current vs multiple destinations
- include local solar elevation and honest ISS context
- prove a meaningful bundle reduction against the current deferred globe stack

If COBE proves too constrained for the interaction or overlay model, the fallback evaluation candidate should be `OpenGlobus`, not `CesiumJS`.
