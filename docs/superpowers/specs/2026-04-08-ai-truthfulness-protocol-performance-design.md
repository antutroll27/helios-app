# HELIOS AI Truthfulness, Protocol Consistency, and Home Route Performance Design

**Date**: 2026-04-08
**Scope**: `src/composables/useAI.ts`, `src/stores/protocol.ts`, home-route component loading, aligned user-facing copy

## Context

HELIOS currently has three related quality problems:

1. The AI prompt claims access to US State Department travel advisories even though no such integration exists.
2. The prompt says peak cognition should not be framed as a fixed 2-3 hour pre-sleep window, while the protocol store computes exactly that window.
3. The app builds successfully, but the `/` route is too heavy because the 3D globe and other non-critical surfaces are eagerly bundled and mounted.

These issues hurt trust more than they hurt functionality. HELIOS is a science-forward product, so unsupported claims and internally inconsistent logic are product risks, not just code smells.

## Goals

- Remove unsupported AI-access claims so the model only speaks from real inputs.
- Make protocol timing logic and AI guidance agree on the same scientific framing.
- Reduce initial home-route JavaScript cost without changing the visible product direction.
- Keep the fix set small, local, and safe to ship.

## Non-Goals

- Adding a real travel advisory integration.
- Rewriting the full AI architecture or introducing retrieval/citation validation.
- Deep refactoring of the home page layout.
- Reworking the broader product and marketing docs in this pass.

## Design

### 1. AI Truthfulness

The AI layer will stop claiming access to any source that is not actually wired into the app state at runtime.

Changes:

- Remove the travel-advisory capability claim from the frontend prompt builder.
- Remove the matching travel-advisory claim from the backend prompt builder so the system remains consistent across client and server paths.
- Update chat welcome text to describe the live inputs the app actually has: local solar conditions, NOAA space weather, weather/environment signals, and the user profile.
- Rephrase any wording that implies "live NASA satellite data" if the prompt itself is not populated from a NASA-backed store at that moment.
- Add explicit missing-data language in the prompt so the model says data is unavailable or approximate when stores are empty, defaulted, or stale.

Result:

- The model will no longer be instructed to hallucinate an advisory level or pretend to have a source it cannot query.
- The product copy becomes narrower but materially more defensible.

### 2. Protocol Consistency

The product will stop modeling peak focus as a universal pre-sleep window.

Current problem:

- `protocol.ts` computes peak focus as `sleepTime - 3h` to `sleepTime - 1h`.
- `useAI.ts` instructs the model not to describe peak cognition that way.

New rule:

- Peak focus becomes a chronotype-based daytime window rather than a pre-sleep window.
- The window is broad, simple, and defensible:
  - `early`: earlier afternoon
  - `intermediate`: mid-to-late afternoon
  - `late`: late afternoon to early evening

Implementation shape:

- Replace the current peak-focus timing math in `protocol.ts` with chronotype-driven windows derived from the current day.
- Update protocol card subtitle/citation text to describe it as a recommended deep-work window that varies by chronotype.
- Keep pre-sleep alertness separate conceptually; do not label the wake-maintenance zone as the best focus window.
- Update `useAI.ts` prompt text so the "current protocol" block and the scientific guidance describe the same logic.

Result:

- The AI and the visible protocol card will agree.
- HELIOS will stop making a stronger claim than the app can defend.

### 3. Home Route Performance

The home route should remain visually the same, but the heaviest pieces will no longer be part of the initial critical path.

Changes:

- Async-load `HeliosGlobe` from `HomePage.vue`.
- Async-load `ChatInterface` from `HomePage.vue`.
- Async-load `OnboardingModal` from `HomePage.vue` so returning users do not pay for it on first route load.
- Keep protocol and lightweight data cards in the main route chunk for immediate usefulness.
- Use simple loading placeholders for deferred components where needed so the page does not feel broken during lazy hydration.

Why this approach:

- The bundle analysis showed the globe path is the dominant weight source.
- The chat path is meaningful but secondary.
- This gives a high-value reduction without redesigning the page or changing the product narrative.

Expected tradeoff:

- The globe and chat may appear a fraction later on initial load.
- In exchange, parse/execute cost drops and mobile/PWA behavior should improve.

## Files

Primary implementation files:

- `src/composables/useAI.ts`
- `src/stores/protocol.ts`
- `src/pages/HomePage.vue`
- `src/components/ChatInterface.vue`
- `backend/chat/prompt_builder.py`

Possible secondary touchpoints:

- `src/components/HeliosGlobe.vue`
- `src/pages/SettingsPage.vue`

## Error Handling and Fallbacks

- If live data is missing, the prompt should explicitly say the app is working from partial inputs rather than present defaults as confirmed truth.
- Async-loaded UI components should fail soft: the rest of the home page remains usable even if a deferred surface fails to mount.
- Peak-focus logic should use stable fallback windows if the stored chronotype is missing or invalid.

## Verification

- Build frontend with `npm run build`.
- Confirm the home route still renders and the deferred components load correctly.
- Confirm the AI prompt no longer contains travel-advisory language.
- Confirm the protocol card and AI prompt use the same peak-focus framing.
- Compare bundle output before and after to verify reduction in the `HomePage` route cost.

## Risks

- If the prompt wording is softened too much, the assistant may become less distinctive. The fix should reduce overclaiming without stripping the brand voice.
- If the new peak-focus windows are too simplistic, the model may still embellish. That is acceptable for this pass as long as the explicit contradiction is removed.
- Lazy loading can create visible loading gaps if placeholders are not deliberate.

## Acceptance Criteria

- No prompt path claims access to State Department advisories.
- No prompt path requires the model to produce unsupported travel-safety levels.
- The `Peak Focus` card is no longer computed as a generic sleep-minus-3h-to-1h window.
- The frontend prompt and visible protocol agree on the new peak-focus framing.
- `HeliosGlobe`, `ChatInterface`, and `OnboardingModal` are no longer eagerly bundled into the initial home route path.
- The app still builds successfully after the changes.
