# Orbital Instrument UI Refresh Design

Date: 2026-04-10
Status: Approved for spec review

## Goal

Refine the homepage globe experience so the supporting UI no longer feels like generic dashboard chrome. The globe remains the hero, but the surrounding modules should feel like a specialized orbital instrument panel with stronger authorship, cleaner hierarchy, and a more distinctive loading state.

## Why This Pass Exists

The current globe scene is directionally better than the original dashboard, but several areas still read as default product UI:

- the left orbital cluster still feels like a normal card dropped beside the hero
- the destination rail still behaves like a standard selection list
- the bottom widgets still read as three generic dashboard boxes
- the loading state for the orbital globe feels like a placeholder rather than part of the product language

This pass fixes those issues without changing the underlying data model or homepage architecture.

## Design Direction

Use a mixed visual language drawn from the references:

- dark engineered surfaces
- thin technical linework
- compact rounded modules
- strong hierarchy between labels and values
- cyan/teal as the main systems color
- warm orange as a restrained signal color for high-importance timing/alignment emphasis

The result should feel:

- more premium than playful
- more instrument-like than dashboard-like
- more authored than generic

## Non-Goals

This pass does not:

- redesign the app shell outside the homepage globe area
- redesign chat, settings, or onboarding
- change the scientific logic or data contracts
- change the globe rendering architecture again

## Target Areas

### 1. Orbital Intro Cluster

The left-side header and orbital card should become one composed slab instead of two stacked pieces.

Changes:

- merge `HELIOS / COBE`, `Orbital View`, route chip, and current-frame information into one unified module cluster
- reduce the feeling of separate header plus card by using tighter spacing and shared surface language
- replace broad rounded-card softness with flatter surfaces, tighter radii, and finer dividers
- shorten or compress low-value explanatory copy
- preserve current information hierarchy:
  - section identity
  - selected route
  - current city
  - solar phase
  - elevation
  - one short orbital-context statement

Desired impression:

- tactical
- calm
- premium
- specific to HELIOS

### 2. Destination Rail

The destination selector should feel like a control column, not a generic card list.

Changes:

- tighten vertical rhythm and internal padding
- make the active card feel more deliberate through accent placement, not just border glow
- use cyan/teal for live selection state
- introduce a restrained warm accent only if one timing-related sub-detail needs emphasis
- reduce low-contrast filler text and give city names stronger weight

Desired impression:

- flight-console selector
- compact and intentional
- clearly interactive without looking like consumer SaaS UI

### 3. Bottom Widgets

The three homepage widgets under the globe should become instrument modules rather than plain dashboard cards.

Modules in scope:

- geomagnetic
- solar alignment
- environment

Changes:

- unify their surface language with the globe cluster
- tighten label/value hierarchy
- use one accent family per module rather than broad mixed styling
- use warm orange primarily for timing/alignment emphasis
- keep the content model intact while making presentation more technical and less generic

Desired impression:

- telemetry readouts
- compact control modules
- less “widget”, more “system panel”

### 4. Orbital Globe Loading State

The loading experience must stop feeling like a generic skeleton.

Replace the current placeholder with a boot-sequence / calibration panel aesthetic:

- contour, radar, or grid-inspired linework
- small system labels and microcopy
- a restrained progress or calibration indicator
- loading layout that feels like HELIOS is initializing a planetary model

This placeholder should share the same visual language as the final UI so the transition feels intentional.

## Surface Language Rules

### Panels

- prefer flatter monolithic surfaces over soft app cards
- use tighter radii
- use thin borders and subtle inset seams
- keep shadows restrained and directional

### Typography

- mono labels stay small and technical
- display text is reserved for city names, module names, and high-signal values
- body copy should be shorter, denser, and less conversational
- avoid generic dashboard wording where possible

### Color

- cyan/teal remains the systems color
- warm orange is used narrowly for timing, alignment, or calibration emphasis
- do not over-distribute the warm accent across all modules

### Motion

- do not add broad animation clutter
- if any motion is used in the placeholder, it should feel like quiet calibration rather than skeleton shimmer

## File Scope

Primary files:

- `src/components/globe/HeliosGlobePanel.vue`
- `src/components/globe/GlobeOrbitalContext.vue`
- `src/components/globe/GlobeComparisonHud.vue`
- `src/components/home/HomeGlobePlaceholder.vue`

Secondary files likely in scope:

- `src/components/SpaceWeatherGauge.vue`
- `src/components/SocialJetLagScore.vue`
- `src/components/EnvironmentBadge.vue`

Possible support file:

- `src/pages/HomePage.vue` only if spacing/composition around these modules needs minor alignment changes

## Component Boundaries

- `HeliosGlobePanel.vue`
  - remains the composition surface for the hero scene
  - owns cluster placement and overall orchestration

- `GlobeOrbitalContext.vue`
  - owns the left current-frame module presentation

- `GlobeComparisonHud.vue`
  - owns the destination rail presentation

- `HomeGlobePlaceholder.vue`
  - owns the loading-state redesign

- bottom widgets
  - each keeps its current data responsibility
  - only presentation language changes in this pass

## Risks

- over-stylizing the modules could fight the globe rather than support it
- too much warm accent would break the HELIOS systems identity
- too much contour/technical styling could become gimmicky if applied literally

Mitigation:

- keep the globe as the visual dominant element
- use the references as tone, not as templates to copy
- constrain the warm accent to a few specific states

## Verification Expectations

Implementation should verify:

- homepage build still passes
- globe loading still stages correctly
- visual hierarchy is stronger on both desktop and mobile
- the left cluster and bottom widgets no longer read as generic dashboard cards

## Success Criteria

The pass is successful if:

- the left cluster feels like one authored orbital instrument panel
- the destination rail feels like a control surface, not a list of app cards
- the three bottom widgets feel like telemetry modules
- the loading state feels product-specific instead of placeholder-generic
- the homepage still feels coherent with the globe as the center of gravity
