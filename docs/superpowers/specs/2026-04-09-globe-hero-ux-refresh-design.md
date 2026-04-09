# Globe Hero UX Refresh Design

> Date: 2026-04-09
> Owner: Codex
> Status: Approved for spec drafting

## Goal

Rework the COBE homepage globe section from a broken three-column dashboard into a globe-dominant hero surface that feels cinematic, intentional, and readable.

The globe must become the primary visual object. Supporting data should move into a small number of floating overlays that feel curated rather than exhaustive. The result should read as a planetary control surface, not an admin panel.

## Problem Statement

The current globe area fails at both hierarchy and composition:

- the globe does not dominate the scene
- the center copy competes with the renderer instead of supporting it
- the left and right panels feel like detached cards bolted onto the hero
- the data is too dense in the wrong places and too weak in the right ones
- the section reads as a dashboard grid instead of a hero surface
- mobile and desktop both inherit the same structural heaviness

This makes the globe experience feel improvised and visually incoherent despite the stronger COBE rendering stack underneath it.

## Design Direction

Chosen direction: `Cinematic command deck`

This direction preserves useful live data while making the globe visually dominant.

Key principles:

- one clear hero object: the globe
- floating overlays instead of structural sidebars
- fewer panels, better placement
- very little center copy
- data surfaces should support the globe, not divide the screen into equal columns
- desktop should feel dramatic, mobile should stay compact and legible

## Layout Architecture

The globe section should stop behaving like a three-column dashboard.

Replace the current structure with one stage:

- a single dominant central globe
- a compact top-left orbital card
- a narrow right-side destination rail
- a slim bottom stat strip

The globe should occupy roughly 65-75% of the perceived visual weight of the section.

The hero title should no longer sit in a large top-right block fighting for attention. Any headline or section label should become much smaller and more restrained.

## Overlay Zones

### Top-left orbital card

Purpose: provide current context without overpowering the hero.

Contents:

- current city
- solar phase
- solar elevation
- one short orbital-context sentence

Behavior:

- small footprint
- dense but calm
- no long explanatory paragraphs
- should read as a status module, not a feature panel

This replaces the current oversized orbital panel.

### Right-side destination rail

Purpose: keep destination comparison selection visible without becoming a full dashboard column.

Contents per card:

- city name
- timezone delta
- one short travel-readiness line

Rules:

- show a maximum of 3 destinations in the hero section
- use a narrow floating stack on desktop
- selected destination expands slightly and becomes visually dominant
- selecting a destination recenters the globe

This replaces the current full-width, full-detail comparison panel.

### Bottom stat strip

Purpose: provide just enough context at the lower edge of the hero.

Contents:

- anchor location
- selected destination
- sunrise/sunset delta or solar timing delta

Rules:

- one slim translucent band
- float across the lower edge of the globe
- no debug-style fields like selection id
- no dense explanatory copy

This replaces the current center-stage meta block.

## Globe Behavior

The COBE globe remains draggable and visually central.

Interaction rules:

- drag rotation remains the primary direct interaction
- destination selection should come from the destination rail and optional small selector chips inside the renderer
- do not rely on fake-precise on-globe clicking
- the selected destination should visually influence the renderer and recentering behavior
- when nothing is selected, the globe should stay in a clean neutral orientation

The globe should look cleaner than the current implementation:

- bigger in scale
- less visual clutter around it
- the glow and horizon should be the brightest objects in the hero

## Content Strategy

The center of the hero must stop carrying long explanatory copy.

Rules:

- no large paragraph block beside the globe
- at most one tiny label near the globe stage
- short system labels are acceptable
- longer interpretation belongs outside the hero, not inside it

Typography rules:

- keep mono labels for system feel
- reduce excessive uppercase density
- make city names and key stats more readable at a glance
- use shorter copy blocks everywhere in the hero

## Visual Language

Maintain the HELIOS atmospheric dark style, but reduce the amount of chrome.

Target look:

- fewer visible boxes
- softer borders
- more glass-like overlays
- stronger negative space
- clearer layering hierarchy

The section should feel intentional and cinematic, not like three separate cards inside a large container.

## Responsive Behavior

### Desktop

- globe stays centered and dominant
- orbital card pins top-left
- destination rail sits right-center
- bottom stat strip overlaps the lower globe boundary slightly

### Mobile

- globe still leads the section
- orbital card compresses into a small card or chip group above the globe
- destination rail becomes a horizontal row below or partly over the lower edge
- bottom stat strip collapses into 2-3 compact pills
- no three-column dashboard layout

## Component Boundaries

Keep the route and feature boundaries focused.

Expected responsibilities:

- `HeliosGlobePanel.vue`
  - overall stage composition
  - overlay placement
  - minimal hero copy
- `HeliosCobeGlobe.vue`
  - globe renderer only
  - drag behavior
  - optional internal compact selector chips
- `GlobeOrbitalContext.vue`
  - compact top-left orbital card
- `GlobeComparisonHud.vue`
  - destination rail presentation
- likely new small hero subcomponents if useful
  - bottom stat strip
  - compact status pills

The panel should become a composition surface, not a place where all hero logic and all hero presentation are mixed together.

## Non-Goals

This redesign does not change:

- the scientific logic behind the data
- the current COBE renderer technology choice
- the staged-loading architecture
- backend data sources
- wearable roadmap behavior

This is a UI and UX composition redesign of the hero section only.

## Success Criteria

The redesign is successful if:

- the globe is the first thing the eye lands on
- the hero reads as a planetary interface rather than a dashboard
- the data feels curated and intentional
- the side overlays support the globe instead of competing with it
- desktop feels dramatic without becoming noisy
- mobile stays readable and compact
- the section feels designed, not assembled

## Implementation Notes

Expected implementation shape:

- reduce or remove the current large center copy block
- restructure the hero into absolute or layered overlay zones around the globe
- simplify the destination cards
- compress the orbital card substantially
- add a dedicated bottom strip or pill row for the most important context
- preserve the current performance wins from the COBE replacement

## Self-Review

Placeholder scan:

- no TODO or TBD markers remain

Internal consistency:

- layout, interaction, and responsive behavior all follow the same globe-dominant direction

Scope check:

- focused on the hero UX only
- does not expand into data-model or backend work

Ambiguity check:

- the overlay zones, priority hierarchy, and component responsibilities are explicit enough to plan implementation work
