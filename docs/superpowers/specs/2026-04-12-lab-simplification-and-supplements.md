# Lab Page: UI Simplification + Dynamic Supplements — Design Spec

**Date:** 2026-04-12  
**Scope:** Two cohesive improvements to the existing `/lab` Science Tools page. The floating AI chatbot is a separate spec.

---

## 1. Overview

Two changes ship together as one Lab page upgrade:

1. **Evidence section collapse** — each LabCard's evidence block hides behind a toggle by default, reducing visual density without removing the scientific detail.
2. **Dynamic supplement recommendations** — the SupplementGuideCard reads from the biometrics store and re-ranks supplements by biometric relevance, adds a "Recommended" badge to the top pick, and shows a personalized note on each sub-card.

---

## 2. Feature 1 — Evidence Section Collapse

### Problem

Each LabCard currently renders three stacked sections: inputs, output, and evidence. The evidence block (effect, population, caveat) is valuable for scientific credibility but adds significant vertical height and visual density that most users don't need on every interaction.

### Solution

Add a local toggle inside `LabCard.vue`. Evidence is hidden by default; clicking "Research basis ▸" expands it inline. State is per-card and does not persist.

### Changes

**`src/components/lab/LabCard.vue`** (only file changed for this feature):

- Add `const showEvidence = ref(false)` (local state, not a prop)
- Wrap the `#evidence` slot in `v-show="showEvidence"` with a CSS `max-height` transition (expand: 0 → auto equivalent; collapse: reverse)
- Add a toggle button immediately below the output divider:
  - Label: `▸ Research basis` when collapsed, `▾ Research basis` when expanded
  - Typography: `font-family: 'Geist Mono'`, `font-size: var(--font-size-3xs)`, `letter-spacing: var(--tracking-fine)`, color `rgba(255,246,233,0.35)`
  - On hover: color transitions to `var(--card-accent)` (the per-card CSS custom property already in use)
  - No border, no background — plain text button, `cursor: pointer`
  - Only rendered when the `#evidence` slot has content (use `useSlots()` to check)

**All other files: no changes.** The five card components (`NapCalcCard`, `AlcoholImpactCard`, `BreathworkCard`, `MealWindowCard`, `ExerciseTimingCard`) keep their `<template #evidence>` slot content exactly as-is. `LabEvidenceBlock.vue` is unchanged.

### Behaviour

- Toggle state is local to each card instance — expanding one card does not affect others
- Evidence starts collapsed on every page load (no persistence)
- The toggle button is hidden when `hasOutput` is false (no output = no divider = no toggle placement)

---

## 3. Feature 2 — Dynamic Supplement Recommendations

### Problem

`SupplementGuideCard.vue` renders a static, hardcoded array of three supplements with equal visual weight. It has no awareness of the user's biometric data.

### Solution

A new `useSupplementGuide.ts` composable reads `avgHRV`, `avgSleepScore`, and `avgTotalSleepH` from the biometrics store, scores each supplement against biometric thresholds, and returns a ranked list with personalized note strings. `SupplementGuideCard.vue` renders the ranked output.

### Architecture

Follows the existing lab composable pattern (see `useMealWindow.ts`, `useBreathwork.ts`):
- **Pure scoring function** `scoreSupplements(hrv, sleepScore, sleepHours)` — takes injected values, no store access, fully unit-testable
- **Composable wrapper** `useSupplementGuide()` — reads store, returns reactive `rankedSupplements` and `hasPersonalization`

### New File: `src/composables/lab/useSupplementGuide.ts`

**Types:**

```typescript
export interface RankedSupplement {
  key: 'magnesium' | 'ashwagandha' | 'glycine'
  name: string
  tagline: string
  grade: 'A+' | 'A' | 'B+'
  score: number          // 0–3 relevance score
  note: string           // personalized note string
  isTopPick: boolean     // true for highest-scoring supplement
}
```

**Scoring thresholds** (each supplement scored 0–3):

| Supplement | Signal | Threshold | Points | Note copy |
|---|---|---|---|---|
| Magnesium Glycinate | `avgTotalSleepH` | `< 7.0` | +2 | `"Your {X}h avg is below the 7h threshold — Mg supports slow-wave sleep depth"` |
| Magnesium Glycinate | `avgSleepScore` | `< 75` | +1 | Appended to sleep hours note if both fire; standalone if sleep hours is fine |
| Ashwagandha KSM-66 | `avgHRV` | `< 40 ms` | +2 | `"HRV {X}ms suggests elevated stress load — KSM-66 reduces cortisol ~15%"` |
| Ashwagandha KSM-66 | `avgSleepScore` | `< 80` | +1 | Appended to HRV note if both fire |
| Glycine | `avgSleepScore` | `< 72` | +1 | `"Sleep score {X} suggests onset or fragmentation — glycine lowers core body temp"` |
| Glycine | `avgTotalSleepH` | `< 6.5` | +1 | Appended if both fire |

**Fallback note** (when no threshold fires for a supplement):  
`"Your current metrics don't flag this as a priority — monitor if sleep score drops below [threshold]"`  
Every supplement always has a note; no card is ever blank.

**`hasPersonalization`** — `true` when `avgHRV != null && avgSleepScore != null`. When `false`, `SupplementGuideCard` renders the existing static layout without reordering, badges, or personalized notes (graceful degradation — covers the case where biometrics page has never been visited).

### Modified File: `src/components/lab/SupplementGuideCard.vue`

- Import `useSupplementGuide()`, replace static array with `rankedSupplements`
- Top-scored supplement (`isTopPick: true`) gets a `"Recommended ✓"` badge — same visual style as the Early TRF badge in `MealWindowCard.vue` (`color: #00D4AA`, `background: rgba(0,212,170,0.1)`, `border: 1px solid rgba(0,212,170,0.3)`)
- Each sub-card renders its `note` in a small tinted callout below the stats grid:
  - Triggered note (score ≥ 1): `#00D4AA` text, `rgba(0,212,170,0.07)` background, `rgba(0,212,170,0.35)` left border
  - Fallback note (score 0): `rgba(255,246,233,0.35)` text, no background tint
- Opacity by score: score ≥ 2 → 100%; score 1 → 85%; score 0 → 65%
- When `!hasPersonalization`: render existing static layout, no opacity scaling, no notes, no badge

### New File: `src/composables/lab/useSupplementGuide.test.ts`

Four unit tests against the pure `scoreSupplements` function:

1. Low HRV (32ms) + normal sleep → Ashwagandha ranks first, score ≥ 2
2. Short sleep (6.1h) + low score (68) → Magnesium ranks first, score ≥ 3
3. All metrics healthy (HRV 55, score 88, sleep 7.8h) → all scores 0, all notes are fallback strings
4. Exactly at threshold boundary (HRV 40, sleepScore 75, sleepHours 7.0) → no points awarded (thresholds are strict `<`)

---

## 4. What Does Not Change

- `LabPage.vue` layout and grid — no structural changes
- `LabEvidenceBlock.vue` — component unchanged
- `NapCalcCard`, `AlcoholImpactCard`, `BreathworkCard`, `MealWindowCard`, `ExerciseTimingCard` — no changes beyond inheriting the new toggle from `LabCard.vue`
- The biometrics store — no new getters or actions added; the composable reads existing computed properties
- The floating chatbot — separate spec and plan

---

## 5. File Summary

| File | Action |
|---|---|
| `src/components/lab/LabCard.vue` | Modify — add evidence toggle |
| `src/composables/lab/useSupplementGuide.ts` | Create |
| `src/composables/lab/useSupplementGuide.test.ts` | Create |
| `src/components/lab/SupplementGuideCard.vue` | Modify — wire composable, add badge + notes |

---

## 6. Out of Scope

- Persisting evidence toggle state (localStorage, store)
- Adding new supplements to the guide
- Supplement timing recommendations (separate future feature)
- The floating AI chatbot (separate spec)
