# Home Bundle Staged Loading Design

## Goal

Reduce the initial `HomePage` bundle cost without flattening the current visual identity. The home route should paint quickly with useful protocol/data content first, then reveal the heavier globe and chat experiences in a deliberate staged sequence.

## Problem

The current production build keeps the home route too heavy:

- `HomePage` is roughly `1.25 MB`
- `three.module` is roughly `587 kB`

The main cause is that [`HomePage.vue`](../../../../src/pages/HomePage.vue) eagerly imports both [`HeliosGlobe.vue`](../../../../src/components/HeliosGlobe.vue) and [`ChatInterface.vue`](../../../../src/components/ChatInterface.vue). `HeliosGlobe` then pulls `globe.gl` and `three` into the route path immediately.

## Desired Outcome

- The route shell renders immediately.
- Protocol cards and compact data widgets stay available on first paint.
- The globe appears shortly after initial paint as a staged reveal with a designed placeholder.
- Chat loads later than the globe and only when needed or near viewport.
- `globe.gl` / `three` move out of the main route chunk.
- The page still feels premium rather than obviously deferred.

## Approach

### 1. Keep the route shell light

[`HomePage.vue`](../../../../src/pages/HomePage.vue) becomes a composition surface only.

It should synchronously render:

- onboarding modal
- section framing
- protocol timeline
- compact metrics cards
- wearable section
- attribution

It should not synchronously import:

- `HeliosGlobe`
- `ChatInterface`

### 2. Use async boundaries for heavy components

Use `defineAsyncComponent` in [`HomePage.vue`](../../../../src/pages/HomePage.vue) for:

- globe experience
- chat experience

The async boundary should include:

- lightweight loading component or inline fallback markup
- a short timeout / idle-style staged mount for the globe
- later mount for chat than globe

The fallback should be intentional, not generic. It should preserve the mission-control feeling with:

- a gradient or atmospheric shell in the globe slot
- HUD-style placeholder labels
- a subtle loading state for chat

### 3. Stage the reveal

Recommended sequence:

1. Render page shell immediately.
2. Render globe placeholder immediately.
3. Mount globe async after a short delay once first paint is complete.
4. Keep chat placeholder collapsed or lightweight.
5. Mount chat only when:
   - the section nears viewport, or
   - the user expands/interacts with it.

This keeps the above-the-fold experience dramatic while moving real cost out of the critical path.

### 4. Split chunks deliberately

Update [`vite.config.ts`](../../../../vite.config.ts) so bundle output separates:

- vendor core
- `globe.gl`
- `three`
- home async UI where useful

This should stop `three` from sitting inside the main home route payload and make the staged reveal actually pay off at the network level.

### 5. Preserve component boundaries

Component map:

- `HomePage.vue`: route composition, staged mount orchestration
- new globe placeholder component or inline loading block: visual fallback only
- new chat placeholder component or inline loading block: visual fallback only
- `HeliosGlobe.vue`: real globe implementation only
- `ChatInterface.vue`: real chat implementation only

No feature logic should be moved into the placeholders beyond loading display and mount signaling.

## Files In Scope

- Modify: `src/pages/HomePage.vue`
- Optional create: `src/components/home/HomeGlobePlaceholder.vue`
- Optional create: `src/components/home/HomeChatPlaceholder.vue`
- Optional create: `src/composables/useStagedReveal.ts`
- Modify: `vite.config.ts`

## Behavior Details

### Globe

- Replace static import with async component.
- Show placeholder immediately.
- Mount after a short post-paint delay.
- Keep the final rendered globe visually identical once loaded.

### Chat

- Replace static import with async component.
- Keep the header area visible quickly.
- Load the full chat implementation later than the globe.
- Prefer loading on expand or near-viewport instead of immediately.

### Metrics / Protocol

- Keep these synchronous because they are comparatively cheap and provide immediate value.
- Do not degrade their interactivity.

## Error Handling

- If async globe import fails, keep the placeholder visible and show a concise fallback note instead of breaking the page.
- If async chat import fails, keep the lightweight shell and present a retry affordance or simple unavailable state.

## Verification

Minimum verification for this pass:

- `npm run build`
- Compare build output before/after
- Confirm the home chunk shrinks materially
- Confirm `three` and globe-related code are no longer part of the initial home chunk path in the same way

Success is not "no warnings at all." Success is a real reduction in the initial route cost while preserving the intended visual experience.

## Tradeoffs

### Pros

- Strong initial performance win
- Preserves current product feel
- Natural use of lazy loading where it matters most
- Low conceptual risk

### Cons

- Slightly more orchestration in `HomePage.vue`
- Requires thoughtful fallback UI so loading does not feel broken
- Build may still warn if globe chunks remain large, even after moving them off the critical path

## Non-Goals

- Rebuilding the globe implementation itself
- Removing `three` or `globe.gl` from the project
- Redesigning the home page layout
- Refactoring unrelated pages or stores

## Acceptance Criteria

- `HomePage.vue` no longer eagerly imports `HeliosGlobe.vue` and `ChatInterface.vue`.
- The page renders meaningful content before the globe/chat code loads.
- The globe reveal feels intentional, not delayed by accident.
- Chat is lazy-loaded.
- Build remains green.
- The initial home-route bundle is materially smaller than the current baseline.
