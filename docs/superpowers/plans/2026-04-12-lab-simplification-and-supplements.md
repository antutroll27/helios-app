# Lab Page: UI Simplification + Dynamic Supplements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a collapsing evidence toggle to every LabCard, and make SupplementGuideCard rank its three supplements by biometric relevance with personalised notes.

**Architecture:** Task 1 modifies `LabCard.vue` alone (all five card components inherit the toggle automatically). Task 2 creates the `useSupplementGuide` composable using TDD — a pure `scoreSupplements()` function plus a reactive wrapper that reads the biometrics store. Task 3 wires the composable into `SupplementGuideCard.vue` and replaces the static supplement array with the new biometric-aware data.

**Tech Stack:** Vue 3 `<script setup lang="ts">`, Pinia, Vitest, scoped CSS (no Tailwind arbitrary values, no animation libraries)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/components/lab/LabCard.vue` | Modify | Add `showEvidence` ref + `useSlots` guard + toggle button + CSS |
| `src/composables/lab/useSupplementGuide.ts` | Create | Pure `scoreSupplements()` + `useSupplementGuide()` composable |
| `src/composables/lab/useSupplementGuide.test.ts` | Create | 5 unit tests for `scoreSupplements` |
| `src/components/lab/SupplementGuideCard.vue` | Modify | Replace static array with new supplement data, wire composable, add badge + notes |

---

## Task 1: Evidence toggle in LabCard.vue

**Files:**
- Modify: `src/components/lab/LabCard.vue`

Current `LabCard.vue` is 59 lines. The evidence slot is rendered unconditionally inside the `hasOutput` gate with no toggle. Replace the entire file with the version below.

- [ ] **Step 1: Replace LabCard.vue with the toggled version**

Write this as the new complete content of `src/components/lab/LabCard.vue`:

```vue
<script setup lang="ts">
import { ref, useSlots } from 'vue'

defineProps<{
  label:     string
  title:     string
  accent:    string
  citation:  string
  hasOutput: boolean
}>()

const slots        = useSlots()
const showEvidence = ref(false)
</script>

<template>
  <div class="lab-card bento-card" :style="{ '--card-accent': accent }">
    <div class="lab-card__header">
      <div class="lab-card__label">{{ label }}</div>
      <h2 class="lab-card__title">{{ title }}</h2>
    </div>
    <slot name="inputs" />
    <template v-if="hasOutput">
      <div class="lab-card__divider" />
      <slot name="output" />
      <button
        v-if="slots.evidence"
        class="lab-card__evidence-toggle"
        @click="showEvidence = !showEvidence"
      >
        {{ showEvidence ? '▾' : '▸' }} Research basis
      </button>
      <div
        v-if="slots.evidence"
        class="lab-card__evidence-wrap"
        :class="{ 'lab-card__evidence-wrap--open': showEvidence }"
      >
        <slot name="evidence" />
      </div>
    </template>
    <div class="lab-card__citation">{{ citation }}</div>
  </div>
</template>

<style scoped>
.lab-card {
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.lab-card__label {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-label);
  color: var(--card-accent);
  font-weight: 700;
  text-transform: uppercase;
}
.lab-card__title {
  font-size: var(--font-size-md2);
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 0.1rem;
}
.lab-card__divider {
  height: 1px;
  background: rgba(255,246,233,0.06);
  margin: 0.25rem 0;
}
.lab-card__citation {
  font-size: var(--font-size-4xs);
  color: rgba(255,246,233,0.2);
  font-style: italic;
  margin-top: auto;
  padding-top: 0.4rem;
}

/* Evidence toggle */
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

/* Evidence body — hidden by default, shown via class */
.lab-card__evidence-wrap {
  display: none;
  margin-top: 0.25rem;
}
.lab-card__evidence-wrap--open {
  display: block;
}
</style>
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd helios-app && npm run build 2>&1 | tail -20
```

Expected: build succeeds (zero type errors). If there are errors, fix them before continuing.

- [ ] **Step 3: Manual smoke test**

Run `npm run dev`, navigate to `/lab`. Open the Breathwork card. Confirm:
- Evidence block is hidden by default
- Clicking "▸ Research basis" reveals it
- Clicking "▾ Research basis" hides it again
- Expanding one card does not expand others
- MealWindowCard with invalid inputs (first meal after last meal) shows no toggle (because `hasOutput` is false)

- [ ] **Step 4: Commit**

```bash
git add src/components/lab/LabCard.vue
git commit -m "feat(lab): collapse evidence section behind toggle in LabCard"
```

---

## Task 2: useSupplementGuide composable (TDD)

**Files:**
- Create: `src/composables/lab/useSupplementGuide.ts`
- Create: `src/composables/lab/useSupplementGuide.test.ts`

Write the tests first. The pure function `scoreSupplements` takes three `number | null` inputs and returns a sorted `RankedSupplement[]`. All logic is deterministic and store-free.

- [ ] **Step 1: Write the test file**

Create `src/composables/lab/useSupplementGuide.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { scoreSupplements } from './useSupplementGuide'

describe('scoreSupplements', () => {

  it('low HRV (32ms) with normal sleep → Ashwagandha ranks first, score 2', () => {
    const results = scoreSupplements(32, 82, 7.5)
    expect(results[0].key).toBe('ashwagandha')
    expect(results[0].score).toBe(2)
    expect(results[0].isTopPick).toBe(true)
    const mg = results.find(s => s.key === 'magnesium')!
    expect(mg.score).toBe(0)
    const glycine = results.find(s => s.key === 'glycine')!
    expect(glycine.score).toBe(0)
  })

  it('short sleep (6.1h) + low score (68) → Magnesium ranks first, score 3; Glycine score 2', () => {
    const results = scoreSupplements(50, 68, 6.1)
    expect(results[0].key).toBe('magnesium')
    expect(results[0].score).toBe(3)
    expect(results[0].isTopPick).toBe(true)
    const glycine = results.find(s => s.key === 'glycine')!
    expect(glycine.score).toBe(2)
  })

  it('all metrics healthy → all scores 0, fallback notes, Magnesium wins tie-break', () => {
    const results = scoreSupplements(55, 88, 7.8)
    expect(results.every(s => s.score === 0)).toBe(true)
    expect(results[0].key).toBe('magnesium')
    expect(results[0].isTopPick).toBe(true)
    const mg = results.find(s => s.key === 'magnesium')!
    expect(mg.note).toBe(
      'Your sleep metrics look healthy — Mg becomes more relevant if total sleep drops below 7h or sleep score below 75'
    )
    const ashwa = results.find(s => s.key === 'ashwagandha')!
    expect(ashwa.note).toBe(
      'Your HRV is in a good range — Ashwagandha becomes more relevant if HRV drops below 40ms'
    )
    const glycine = results.find(s => s.key === 'glycine')!
    expect(glycine.note).toBe(
      'Sleep onset appears normal — consider Glycine if sleep score drops below 72 or nightly hours below 6.5h'
    )
  })

  it('all null inputs → all scores 0, no throws, all notes non-empty', () => {
    const results = scoreSupplements(null, null, null)
    expect(results.every(s => s.score === 0)).toBe(true)
    expect(results.every(s => s.note.length > 0)).toBe(true)
  })

  it('exact boundary values → all scores 0 (strict < thresholds)', () => {
    // hrv === 40, sleepScore === 75, sleepHours === 7.0 — at the boundary, not below it
    const results = scoreSupplements(40, 75, 7.0)
    expect(results.every(s => s.score === 0)).toBe(true)
  })

})
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd helios-app && npm test -- useSupplementGuide 2>&1 | tail -30
```

Expected: 5 tests fail with "Cannot find module './useSupplementGuide'" or similar. If they don't fail, something is wrong — stop and investigate before continuing.

- [ ] **Step 3: Create the composable**

Create `src/composables/lab/useSupplementGuide.ts`:

```typescript
import { computed } from 'vue'
import { useBiometricsStore } from '@/stores/biometrics'

export interface RankedSupplement {
  key:       'magnesium' | 'ashwagandha' | 'glycine'
  name:      string
  dose:      string
  timing:    string
  effect:    string
  caveat:    string
  citation:  string
  grade:     'A+' | 'A' | 'B'
  score:     number     // 0–3
  note:      string     // personalised biometric note — never empty
  isTopPick: boolean
}

// ── Static supplement definitions ────────────────────────────────────────────
const SUPPLEMENTS: Omit<RankedSupplement, 'score' | 'note' | 'isTopPick'>[] = [
  {
    key:      'magnesium',
    name:     'Magnesium Glycinate',
    dose:     '300–400 mg elemental',
    timing:   '30–60 min before bed',
    effect:   '+16 min TST, +deep sleep quality',
    caveat:   'Effect strongest in adults with low dietary Mg or insomnia; smaller in healthy well-nourished adults.',
    citation: 'Abbasi 2012, Mah 2021 BMC',
    grade:    'A',
  },
  {
    key:      'ashwagandha',
    name:     'Ashwagandha KSM-66',
    dose:     '300 mg KSM-66 extract',
    timing:   'Morning with food',
    effect:   '−15% cortisol, +11% HRV in stressed adults',
    caveat:   'Benefits most pronounced under high perceived stress. Full effect takes 8–12 weeks.',
    citation: 'Chandrasekhar 2012, Pratte 2014',
    grade:    'A',
  },
  {
    key:      'glycine',
    name:     'Glycine',
    dose:     '3 g',
    timing:   '30 min before bed',
    effect:   '−10 min latency, −0.1–0.2°C core temp',
    caveat:   'Mechanism well-understood (peripheral vasodilation lowers core temp). Fewest side effects.',
    citation: 'Bannai 2012',
    grade:    'A',
  },
]

// ── Scoring helpers ──────────────────────────────────────────────────────────
function scoreMagnesium(
  sleepScore: number | null,
  sleepHours: number | null,
): { score: number; note: string } {
  const hoursLow = sleepHours != null && sleepHours < 7.0
  const scoreLow = sleepScore != null && sleepScore < 75
  const score    = (hoursLow ? 2 : 0) + (scoreLow ? 1 : 0)

  if (hoursLow && scoreLow) {
    return { score, note: `Your ${sleepHours!.toFixed(1)}h avg is below the 7h threshold — Mg supports slow-wave sleep depth · sleep score ${sleepScore} also flags low recovery` }
  }
  if (hoursLow) {
    return { score, note: `Your ${sleepHours!.toFixed(1)}h avg is below the 7h threshold — Mg supports slow-wave sleep depth` }
  }
  if (scoreLow) {
    return { score, note: `Sleep score ${sleepScore} suggests reduced recovery — Mg glycinate supports deep sleep quality` }
  }
  return { score: 0, note: 'Your sleep metrics look healthy — Mg becomes more relevant if total sleep drops below 7h or sleep score below 75' }
}

function scoreAshwagandha(
  hrv:        number | null,
  sleepScore: number | null,
): { score: number; note: string } {
  const hrvLow   = hrv != null && hrv < 40
  const scoreLow = sleepScore != null && sleepScore < 80
  const score    = (hrvLow ? 2 : 0) + (scoreLow ? 1 : 0)

  if (hrvLow && scoreLow) {
    return { score, note: `HRV ${hrv!.toFixed(1)}ms suggests elevated stress load — KSM-66 reduces cortisol ~15% (Chandrasekhar 2012) · sleep score also supports prioritising cortisol reduction` }
  }
  if (hrvLow) {
    return { score, note: `HRV ${hrv!.toFixed(1)}ms suggests elevated stress load — KSM-66 reduces cortisol ~15% (Chandrasekhar 2012)` }
  }
  if (scoreLow) {
    return { score, note: `Sleep score ${sleepScore} suggests stress-related sleep disruption — consider Ashwagandha` }
  }
  return { score: 0, note: 'Your HRV is in a good range — Ashwagandha becomes more relevant if HRV drops below 40ms' }
}

function scoreGlycine(
  sleepScore: number | null,
  sleepHours: number | null,
): { score: number; note: string } {
  const scoreLow = sleepScore != null && sleepScore < 72
  const hoursLow = sleepHours != null && sleepHours < 6.5
  const score    = (scoreLow ? 1 : 0) + (hoursLow ? 1 : 0)

  if (scoreLow && hoursLow) {
    return { score, note: `Sleep score ${sleepScore} suggests onset or fragmentation — glycine lowers core body temperature · combined with short sleep (${sleepHours!.toFixed(1)}h), sleep onset is the likely bottleneck` }
  }
  if (scoreLow) {
    return { score, note: `Sleep score ${sleepScore} suggests onset or fragmentation — glycine lowers core body temperature` }
  }
  if (hoursLow) {
    return { score, note: `Short sleep (${sleepHours!.toFixed(1)}h) may reflect slow sleep onset — glycine reduces latency ~10 min` }
  }
  return { score: 0, note: 'Sleep onset appears normal — consider Glycine if sleep score drops below 72 or nightly hours below 6.5h' }
}

// ── Pure function (injectable for tests) ─────────────────────────────────────
export function scoreSupplements(
  hrv:        number | null,
  sleepScore: number | null,
  sleepHours: number | null,
): RankedSupplement[] {
  const mg    = scoreMagnesium(sleepScore, sleepHours)
  const ashwa = scoreAshwagandha(hrv, sleepScore)
  const gly   = scoreGlycine(sleepScore, sleepHours)

  const scored: RankedSupplement[] = [
    { ...SUPPLEMENTS[0], ...mg,    isTopPick: false },
    { ...SUPPLEMENTS[1], ...ashwa, isTopPick: false },
    { ...SUPPLEMENTS[2], ...gly,   isTopPick: false },
  ]

  // Sort descending by score; stable (magnesium > ashwagandha > glycine on tie)
  scored.sort((a, b) => b.score - a.score)
  scored[0].isTopPick = true

  return scored
}

// ── Composable (store-aware) ──────────────────────────────────────────────────
export function useSupplementGuide() {
  const biometrics = useBiometricsStore()

  const hasPersonalization = computed(() =>
    biometrics.avgHRV != null && biometrics.avgSleepScore != null
  )

  const rankedSupplements = computed(() =>
    scoreSupplements(biometrics.avgHRV, biometrics.avgSleepScore, biometrics.avgTotalSleepH)
  )

  return { rankedSupplements, hasPersonalization }
}
```

- [ ] **Step 4: Run tests — expect all 5 to pass**

```bash
cd helios-app && npm test -- useSupplementGuide 2>&1 | tail -30
```

Expected output contains `5 passed`. If any test fails, read the error message and fix the scoring logic before continuing.

- [ ] **Step 5: Run full test suite to catch regressions**

```bash
cd helios-app && npm test 2>&1 | tail -20
```

Expected: all existing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add src/composables/lab/useSupplementGuide.ts src/composables/lab/useSupplementGuide.test.ts
git commit -m "feat(lab): add useSupplementGuide composable with biometric-driven supplement scoring"
```

---

## Task 3: Wire SupplementGuideCard.vue

**Files:**
- Modify: `src/components/lab/SupplementGuideCard.vue`

Replace the entire file. The new version:
- Imports `useSupplementGuide()`
- Renders `rankedSupplements` (always the correct order — sorted by the composable)
- Shows "Recommended ✓" badge on the top pick when `hasPersonalization`
- Shows per-supplement `.sg-note` callout when `hasPersonalization`
- Applies opacity scaling by score when `hasPersonalization`
- Falls back to the same cards with no personalization UI when `hasPersonalization` is false

- [ ] **Step 1: Replace SupplementGuideCard.vue**

Write this as the complete new content of `src/components/lab/SupplementGuideCard.vue`:

```vue
<script setup lang="ts">
import { useSupplementGuide } from '../../composables/lab/useSupplementGuide'

const { rankedSupplements, hasPersonalization } = useSupplementGuide()

const GRADE_COLOR: Record<string, string> = {
  'A+': '#00D4AA',
  A:    '#9B8BFA',
  B:    '#FFBD76',
}

function opacityForScore(score: number): number {
  if (score >= 2) return 1
  if (score === 1) return 0.85
  return 0.65
}
</script>

<template>
  <div class="sg-card bento-card">

    <!-- Header -->
    <div class="sg-header">
      <div class="sg-label">SUPPLEMENTS</div>
      <h2 class="sg-title">Sleep Stack</h2>
    </div>

    <!-- Sub-card grid -->
    <div class="sg-grid">
      <div
        v-for="s in rankedSupplements"
        :key="s.key"
        class="sg-sub"
        :style="{
          '--grade-color': GRADE_COLOR[s.grade],
          opacity: hasPersonalization ? opacityForScore(s.score) : 1,
        }"
      >
        <!-- Grade badge + Recommended badge -->
        <div class="sg-badge-row">
          <div class="sg-grade-badge">GRADE {{ s.grade }}</div>
          <div v-if="hasPersonalization && s.isTopPick" class="sg-recommended-badge">
            Recommended ✓
          </div>
        </div>

        <!-- Name -->
        <div class="sg-name">{{ s.name }}</div>

        <!-- Dose + timing -->
        <div class="sg-dose-row">
          <span class="sg-dose">{{ s.dose }}</span>
          <span class="sg-sep">·</span>
          <span class="sg-timing">{{ s.timing }}</span>
        </div>

        <!-- Effect -->
        <div class="sg-effect">{{ s.effect }}</div>

        <!-- Caveat -->
        <p class="sg-caveat">{{ s.caveat }}</p>

        <!-- Citation -->
        <div class="sg-citation">{{ s.citation }}</div>

        <!-- Personalized note (only when biometrics are available) -->
        <div
          v-if="hasPersonalization"
          class="sg-note"
          :class="s.score >= 1 ? 'sg-note--triggered' : 'sg-note--fallback'"
        >
          {{ s.note }}
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.sg-card {
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  grid-column: 1 / -1;
}

/* ── Header ── */
.sg-label {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-label);
  color: #FFBD76;
  font-weight: 700;
  text-transform: uppercase;
}

.sg-title {
  font-size: var(--font-size-md2);
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 0.1rem;
}

/* ── Sub-card grid ── */
.sg-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.6rem;
}

@media (max-width: 580px) {
  .sg-grid {
    grid-template-columns: 1fr;
  }
}

/* ── Individual sub-card ── */
.sg-sub {
  background: rgba(255, 246, 233, 0.03);
  border: 1px solid rgba(255, 246, 233, 0.08);
  border-radius: 0.6rem;
  padding: 0.75rem 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  transition: opacity 0.2s;
}

/* Badge row */
.sg-badge-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

/* Grade badge */
.sg-grade-badge {
  display: inline-flex;
  align-self: flex-start;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-4xs);
  letter-spacing: var(--tracking-label);
  font-weight: 700;
  text-transform: uppercase;
  color: #0A171D;
  background: var(--grade-color);
  border-radius: 3px;
  padding: 0.15rem 0.4rem;
}

/* Recommended badge */
.sg-recommended-badge {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
  color: #00D4AA;
  background: rgba(0, 212, 170, 0.1);
  border: 1px solid rgba(0, 212, 170, 0.3);
  border-radius: 4px;
  padding: 0.2rem 0.45rem;
  white-space: nowrap;
}

/* Name */
.sg-name {
  font-size: var(--font-size-xs5);
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 0.1rem;
}

/* Dose + timing */
.sg-dose-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  color: var(--text-muted);
  letter-spacing: var(--tracking-fine);
}

.sg-sep {
  opacity: 0.4;
}

/* Effect */
.sg-effect {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: var(--tracking-fine);
}

/* Caveat */
.sg-caveat {
  font-size: var(--font-size-xs3);
  font-style: italic;
  color: rgba(255, 189, 118, 0.75);
  background: rgba(255, 189, 118, 0.06);
  border-left: 2px solid rgba(255, 189, 118, 0.3);
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  line-height: 1.45;
  margin: 0.1rem 0 0;
}

/* Citation */
.sg-citation {
  font-size: var(--font-size-4xs);
  color: rgba(255, 246, 233, 0.2);
  font-style: italic;
  margin-top: auto;
  padding-top: 0.2rem;
}

/* Personalized note */
.sg-note {
  font-size: var(--font-size-xs3);
  line-height: 1.4;
  border-left: 2px solid;
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  margin-top: 0.1rem;
}

.sg-note--triggered {
  color: #00D4AA;
  background: rgba(0, 212, 170, 0.07);
  border-left-color: rgba(0, 212, 170, 0.35);
}

.sg-note--fallback {
  color: rgba(255, 246, 233, 0.35);
  background: none;
  border-left-color: rgba(255, 246, 233, 0.1);
}
</style>
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd helios-app && npm run build 2>&1 | tail -20
```

Expected: zero type errors. If `avgTotalSleepH` or `avgHRV` or `avgSleepScore` are flagged as missing on the biometrics store, check `src/stores/biometrics.ts` for the exact property name and fix the composable reference.

- [ ] **Step 3: Run full test suite**

```bash
cd helios-app && npm test 2>&1 | tail -20
```

Expected: all tests pass (including the 5 new useSupplementGuide tests).

- [ ] **Step 4: Manual smoke test**

Run `npm run dev`, navigate to `/lab`. Verify:

1. **With mock biometrics data loaded (default state):** The supplement card shows three cards in biometric-ranked order. The top card has a "Recommended ✓" badge. Each card has a teal callout note (triggered) or a dim fallback note. Lower-scoring cards are visibly less opaque.
2. **Toggle the 7d/30d filter on the biometrics page:** Return to `/lab` — supplement order may shift.
3. **All other lab cards:** Evidence section still collapses correctly (Task 1 regression check).
4. **Responsive:** At 580px, supplement cards stack vertically.

- [ ] **Step 5: Commit**

```bash
git add src/components/lab/SupplementGuideCard.vue
git commit -m "feat(lab): wire useSupplementGuide into SupplementGuideCard — ranked supplements, personalised notes, recommended badge"
```
