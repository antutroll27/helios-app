# Lab Page: UI Simplification + Dynamic Supplements — Design Spec

**Date:** 2026-04-12  
**Scope:** Two cohesive improvements to the existing `/lab` Science Tools page. The floating AI chatbot is a separate spec.

---

## 1. Overview

Two changes ship together as one Lab page upgrade:

1. **Evidence section collapse** — each LabCard's evidence block hides behind a toggle by default, reducing visual density without removing the scientific detail.
2. **Dynamic supplement recommendations** — the SupplementGuideCard replaces its static supplement array with three new supplements (Melatonin removed; Ashwagandha KSM-66 added), reads from the biometrics store, re-ranks by biometric relevance, adds a "Recommended" badge to the top pick, and shows a personalized note on each sub-card.

---

## 2. Feature 1 — Evidence Section Collapse

### Problem

Each LabCard currently renders three stacked sections: inputs, output, and evidence. The evidence block (effect, population, caveat) is valuable for scientific credibility but adds significant vertical height and visual density that most users don't need on every interaction.

### Solution

Add a local toggle inside `LabCard.vue`. Evidence is hidden by default; clicking "Research basis ▸" expands it inline. State is per-card and does not persist.

### Changes

**`src/components/lab/LabCard.vue`** (only file changed for this feature):

Add to `<script setup>`:
```typescript
import { ref, useSlots } from 'vue'   // add useSlots to existing vue import
const slots    = useSlots()
const showEvidence = ref(false)
```

**Template pseudocode** showing exact placement:

```html
<!-- existing: header, citation, inputs slot ... -->

<template v-if="hasOutput">
  <div class="lab-card__divider" />
  <div class="lab-card__output">
    <slot name="output" />
  </div>

  <!-- Evidence toggle — only when evidence slot is filled -->
  <button
    v-if="slots.evidence"
    class="lab-card__evidence-toggle"
    @click="showEvidence = !showEvidence"
  >
    {{ showEvidence ? '▾' : '▸' }} Research basis
  </button>

  <!-- Evidence body — fade only (no height animation) -->
  <div
    v-if="slots.evidence"
    class="lab-card__evidence-wrap"
    :class="{ 'lab-card__evidence-wrap--open': showEvidence }"
  >
    <slot name="evidence" />
  </div>
</template>
```

**CSS for the toggle and fade:**
```css
.lab-card__evidence-toggle {
  align-self: flex-start;
  background: none;
  border: none;
  padding: 0;
  margin-top: 0.35rem;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  color: rgba(255, 246, 233, 0.35);
  cursor: pointer;
  transition: color 0.15s;
}
.lab-card__evidence-toggle:hover {
  color: var(--card-accent);
}

.lab-card__evidence-wrap {
  display: none;       /* hidden by default */
  margin-top: 0.25rem;
}
.lab-card__evidence-wrap--open {
  display: block;
}
```

Use `display: none` / `display: block` (class toggle) rather than `v-show` or a max-height transition. This avoids all height-animation edge cases and is consistent with the scoped-CSS-first approach used throughout the project.

**All other files: no changes.** The five card components (`NapCalcCard`, `AlcoholImpactCard`, `BreathworkCard`, `MealWindowCard`, `ExerciseTimingCard`) keep their `<template #evidence>` slot content exactly as-is. `LabEvidenceBlock.vue` is unchanged.

### Behaviour

- Toggle state is local to each card instance — expanding one card does not affect others
- Evidence starts collapsed on every page load (no persistence)
- The toggle button is not rendered when the card has no `#evidence` slot content (guarded by `v-if="slots.evidence"`)
- The toggle and evidence body are inside the `v-if="hasOutput"` gate — they do not render for invalid states (e.g., MealWindowCard with bad inputs)

---

## 3. Feature 2 — Dynamic Supplement Recommendations

### Problem

`SupplementGuideCard.vue` renders a static, hardcoded array of three supplements (Melatonin, Mg Glycinate, Glycine) with equal visual weight and no awareness of the user's biometric data.

### Supplement Data Change

**Remove:** Melatonin — primarily targets circadian misalignment (jet lag/shift work) which is not well-represented by rMSSD/sleep score signals. It will be re-added in a future supplement timing feature tied to chronotype.

**Replace with / update:**

| Supplement | Dose | Timing | Effect | Caveat | Grade | Citation |
|---|---|---|---|---|---|---|
| Magnesium Glycinate | 300–400 mg elemental | 30–60 min before bed | +16 min TST, +deep sleep quality | Effect strongest in adults with low dietary Mg or insomnia; smaller in healthy well-nourished adults | A | Abbasi 2012, Mah 2021 BMC |
| Ashwagandha KSM-66 | 300 mg KSM-66 extract | Morning with food | −15% cortisol, +11% HRV in stressed adults | Benefits most pronounced under high perceived stress. Full effect takes 8–12 weeks. | A | Chandrasekhar 2012, Pratte 2014 |
| Glycine | 3 g | 30 min before bed | −10 min latency, −0.1–0.2°C core temp | Mechanism well-understood (peripheral vasodilation). Fewest side effects of the three. | A | Bannai 2012 |

**`GRADE_COLOR` update** (in `SupplementGuideCard.vue`):
```typescript
const GRADE_COLOR: Record<string, string> = {
  'A+': '#00D4AA',
  A:    '#9B8BFA',
  B:    '#FFBD76',
}
```

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
  key:       'magnesium' | 'ashwagandha' | 'glycine'
  name:      string
  dose:      string
  timing:    string
  effect:    string
  caveat:    string
  citation:  string
  grade:     'A+' | 'A' | 'B'
  score:     number    // 0–3 relevance score
  note:      string    // personalized biometric note (never empty)
  isTopPick: boolean   // true for the single highest-scoring supplement
}
```

**Pure function signature:**

```typescript
export function scoreSupplements(
  hrv:        number | null,
  sleepScore: number | null,
  sleepHours: number | null
): RankedSupplement[]
```

**Null handling:** If any parameter is `null`, treat it as "threshold not met" for that signal — award 0 points for all thresholds that depend on it. Never throw.

**Scoring thresholds** (each supplement scored 0–3):

| Supplement | Signal | Threshold (strict `<`) | Points | Note copy |
|---|---|---|---|---|
| Magnesium Glycinate | `sleepHours` | `< 7.0` | +2 | `"Your ${sleepHours.toFixed(1)}h avg is below the 7h threshold — Mg supports slow-wave sleep depth"` |
| Magnesium Glycinate | `sleepScore` | `< 75` | +1 | Appended as `" · sleep score ${sleepScore} also flags low recovery"` if sleepHours also triggered; standalone `"Sleep score ${sleepScore} suggests reduced recovery — Mg glycinate supports deep sleep quality"` if sleepHours did not trigger |
| Ashwagandha KSM-66 | `hrv` | `< 40` | +2 | `"HRV ${hrv.toFixed(1)}ms suggests elevated stress load — KSM-66 reduces cortisol ~15% (Chandrasekhar 2012)"` |
| Ashwagandha KSM-66 | `sleepScore` | `< 75` | +1 | Appended as `" · sleep score also supports prioritising cortisol reduction"` if HRV also triggered; standalone `"Sleep score ${sleepScore} suggests stress-related sleep disruption — consider Ashwagandha"` if HRV did not trigger |
| Glycine | `sleepScore` | `< 72` | +1 | `"Sleep score ${sleepScore} suggests onset or fragmentation — glycine lowers core body temperature"` |
| Glycine | `sleepHours` | `< 6.5` | +1 | Appended as `" · combined with short sleep (${sleepHours.toFixed(1)}h), sleep onset is the likely bottleneck"` if sleepScore also triggered; standalone `"Short sleep (${sleepHours.toFixed(1)}h) may reflect slow sleep onset — glycine reduces latency ~10 min"` if sleepScore did not trigger |

**Fallback notes** (when score === 0, no threshold fired):

| Supplement | Fallback note |
|---|---|
| Magnesium Glycinate | `"Your sleep metrics look healthy — Mg becomes more relevant if total sleep drops below 7h or sleep score below 75"` |
| Ashwagandha KSM-66 | `"Your HRV is in a good range — Ashwagandha becomes more relevant if HRV drops below 40ms"` |
| Glycine | `"Sleep onset appears normal — consider Glycine if sleep score drops below 72 or nightly hours below 6.5h"` |

**Tie-breaking:** When two supplements share the same score, maintain stable order: Magnesium > Ashwagandha > Glycine. `isTopPick` is assigned to the first supplement in the sorted list.

**`hasPersonalization`** — `true` when `avgHRV != null && avgSleepScore != null && avgTotalSleepH != null`. All three must be non-null: without `avgTotalSleepH`, Magnesium and Glycine signals would silently score 0 while the UI still shows badges and notes, producing misleading rankings. When `false`, `SupplementGuideCard` renders the static layout (no reordering, no badges, no personalized notes).

### Modified File: `src/components/lab/SupplementGuideCard.vue`

- Replace static `supplements` array with the three new supplement definitions (see Supplement Data Change table above)
- Import `useSupplementGuide()`, use `rankedSupplements` and `hasPersonalization` from it
- When `hasPersonalization` is `true`:
  - Render supplements in `rankedSupplements` order (sorted by score desc)
  - Top pick (`isTopPick: true`) gets a `"Recommended ✓"` badge — same style as the Early TRF badge in `MealWindowCard.vue`: `color: #00D4AA`, `background: rgba(0,212,170,0.1)`, `border: 1px solid rgba(0,212,170,0.3)`, `border-radius: 4px`, `padding: 0.2rem 0.45rem`
  - Each sub-card renders `.sg-note` below `.sg-citation`:
    - Triggered note (score ≥ 1): `color: #00D4AA`, `background: rgba(0,212,170,0.07)`, `border-left: 2px solid rgba(0,212,170,0.35)`
    - Fallback note (score 0): `color: rgba(255,246,233,0.35)`, no background
  - Opacity by score: score ≥ 2 → `opacity: 1`; score 1 → `opacity: 0.85`; score 0 → `opacity: 0.65`
- When `hasPersonalization` is `false`: render the three new supplements in default order with no badge, no notes, no opacity scaling

### New File: `src/composables/lab/useSupplementGuide.test.ts`

Four unit tests against the pure `scoreSupplements` function:

1. **Low HRV, normal sleep** — `scoreSupplements(32, 82, 7.5)` → Ashwagandha ranks first with `score === 2`, Magnesium and Glycine have `score === 0`
2. **Short sleep + low score** — `scoreSupplements(50, 68, 6.1)` → Magnesium ranks first with `score === 3` (2 from sleep hours + 1 from sleep score), Glycine has `score === 2` (1 + 1)
3. **All metrics healthy** — `scoreSupplements(55, 88, 7.8)` → all `score === 0`; all `note` values equal their respective fallback strings; `isTopPick` is `true` on Magnesium (first in tie-break order)
4. **All null inputs** — `scoreSupplements(null, null, null)` → all `score === 0`, no throws, all notes are fallback strings
5. **Exact thresholds (not triggered)** — `scoreSupplements(40, 75, 7.0)` → all `score === 0` (strict `<`, values exactly at boundary score 0)

---

## 4. What Does Not Change

- `LabPage.vue` layout and grid — no structural changes
- `LabEvidenceBlock.vue` — component unchanged
- `NapCalcCard`, `AlcoholImpactCard`, `BreathworkCard`, `MealWindowCard`, `ExerciseTimingCard` — no changes beyond inheriting the new toggle from `LabCard.vue`
- The biometrics store — no new getters or actions added; the composable reads existing `avgHRV`, `avgSleepScore`, `avgTotalSleepH` computed properties
- The floating chatbot — separate spec and plan

---

## 5. File Summary

| File | Action |
|---|---|
| `src/components/lab/LabCard.vue` | Modify — add evidence toggle |
| `src/composables/lab/useSupplementGuide.ts` | Create |
| `src/composables/lab/useSupplementGuide.test.ts` | Create |
| `src/components/lab/SupplementGuideCard.vue` | Modify — replace supplement data, wire composable, add badge + notes |

---

## 6. Out of Scope

- Persisting evidence toggle state (localStorage, store)
- Adding more supplements beyond the three defined above
- Supplement timing recommendations (separate future feature)
- Melatonin re-integration (deferred to chronotype-aware supplement timing feature)
- The floating AI chatbot (separate spec)
