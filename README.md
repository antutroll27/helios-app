# HELIOS

HELIOS is a consumer sleep optimizer and circadian operating system. It combines chronotype inference, light timing, caffeine timing, travel context, environmental inputs, and selected wellness tools into one decision surface.

## Evidence Language

- Tier A: validated foundations used for primary timing guidance
- Tier B: citation-informed heuristics translated into consumer calculators
- Tier C: exploratory or observational context that should never be treated as a deterministic personal forecast

## What Is Strong Today

- chronotype inference from sleep timing and schedule regularity
- circadian light and timing guidance
- caffeine timing and bedtime burden estimation
- live location, solar, environmental, and space-weather context in chat and protocol surfaces

## What Is Heuristic Today

- alcohol, nap, breathwork, supplement, meal-timing, and exercise-timing guidance
- wearable-informed refinement beyond basic sleep-timing chronotype inputs
- investor-demo research modules that still simplify the underlying literature

## What Is Exploratory Today

- space-weather biological context
- any cross-domain inference that relies on observational population findings rather than validated individual prediction

## Architecture Snapshot

- Vue 3 frontend with Vite
- FastAPI backend for authenticated chat, memory, and proxy flows
- Hermes background learner for per-user markdown memory
- Supabase for auth, structured data, chat sessions, and memory rows

## Development

```bash
npm install
npm run build
npm run test -- src/composables/useStagedReveal.test.ts
python -m pytest backend/tests/test_prompt_builder_truthfulness.py -q
```

## Product Boundary

HELIOS is wellness software, not a medical device. Supplement and recovery guidance should be framed as educational support. Users with symptoms, conditions, medications, or any second thoughts should consult a clinician.
