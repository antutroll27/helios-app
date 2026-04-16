# Science and Algorithm Credibility Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade HELIOS so its science claims, chronotype logic, supplement guidance, and AI prompts become more accurate, more bounded, and more useful without flattening the product into a generic sleep app.

**Architecture:** Introduce one shared evidence contract across Python and TypeScript, upgrade the chronotype engine with explicit day-classification and confidence reporting, recalibrate heuristic models so they expose clear claim boundaries, redesign the supplement layer around user goals plus safety disclaimers, and align frontend/backend prompts plus research docs to the same evidence language. Keep the product differentiated by preserving circadian timing, travel, and environmental context while making uncertainty explicit.

**Tech Stack:** Python research modules + `pytest`, Vue 3 Composition API + TypeScript + `vitest`, FastAPI backend prompt builder/router.

---

## File Structure

### New files

- `research/evidence_contract.py`
  - Shared Python helper for `evidence_tier`, `effect_summary`, `population_summary`, `main_caveat`, `uncertainty_factors`, and `claim_boundary`.
- `research/tests/test_evidence_contract.py`
  - Unit tests for the Python evidence helper.
- `research/tests/test_chronotype_engine.py`
  - Regression tests for constrained/free-day classification, confidence scoring, and failure states.
- `research/tests/test_model_evidence_profiles.py`
  - Verifies every calibrated model returns the same evidence metadata shape.
- `src/lib/evidence.ts`
  - TypeScript mirror of the evidence contract for lab cards and AI-facing UI.
- `src/lib/evidence.test.ts`
  - Vitest coverage for the TypeScript evidence helper.
- `src/composables/lab/supplementCatalog.ts`
  - Static supplement definitions, effect sizes, caveats, contraindications, and goal tags.
- `src/lib/chatContext.ts`
  - Pure helper that converts store state into a backend-safe prompt context snapshot.
- `src/lib/chatContext.test.ts`
  - Vitest coverage for authenticated prompt context serialization.

### Existing files to modify

- `research/chronotype_engine.py`
  - Add day classification, confidence scoring, irregularity warnings, and low-confidence failure states.
- `research/caffeine_model.py`
  - Separate Tier A pharmacokinetics from Tier B sleep-impact heuristics.
- `research/light_model.py`
  - Keep light-zone logic strong, expose suppression/delay outputs as heuristic estimates with population notes.
- `research/alcohol_model.py`
  - Keep BAC math strong, harden sleep/HRV outputs as heuristic.
- `research/breathwork_model.py`
  - Keep useful protocol logic, attach caveats and evidence metadata.
- `research/nap_model.py`
  - Preserve nap timing value but label study-specific and heuristic outputs clearly.
- `research/space_weather_bio.py`
  - Keep exploratory context but prevent it from reading like a validated biological forecast.
- `src/components/lab/LabEvidenceBlock.vue`
  - Render the shared evidence structure instead of three loose strings.
- `src/components/lab/LabCard.vue`
  - Make evidence visible by default and keep evidence disclosure consistent.
- `src/composables/lab/useSupplementGuide.ts`
  - Switch from hard-coded thresholds to goal-driven, data-aware ranking.
- `src/composables/lab/useSupplementGuide.test.ts`
  - Update tests for goals, contraindications, and clinician-disclaimer behavior.
- `src/components/lab/SupplementGuideCard.vue`
  - Add bounded goal input and visible "not medical advice / consult a clinician" language.
- `src/composables/useAI.ts`
  - Serialize full science context for authenticated backend chat instead of sending location only.
- `backend/chat/router.py`
  - Accept the richer prompt context payload and pass user profile/context into the builder.
- `backend/chat/prompt_builder.py`
  - Consume real context fields, use shared evidence language, and stop claiming placeholder data is live.
- `backend/tests/test_prompt_builder_truthfulness.py`
  - Extend truthfulness tests to cover context injection and evidence-boundary wording.
- `research/RESEARCH.md`
  - Align the roadmap with the shipped evidence tiers and current architecture.
- `research/RESEARCH_V2.md`
  - Mark which models are heuristic versus exploratory.
- `README.md`
  - Replace the Vite placeholder with an investor-legible explanation of what HELIOS does today.

---

### Task 1: Shared Evidence Contract

**Files:**
- Create: `research/evidence_contract.py`
- Create: `research/tests/test_evidence_contract.py`
- Create: `src/lib/evidence.ts`
- Create: `src/lib/evidence.test.ts`
- Modify: `src/components/lab/LabEvidenceBlock.vue`
- Modify: `src/components/lab/LabCard.vue`

- [ ] **Step 1: Write the failing Python evidence-contract test**

```python
from research.evidence_contract import EvidenceProfile, merge_evidence


def test_merge_evidence_adds_required_metadata():
    profile = EvidenceProfile(
        evidence_tier="B",
        effect_summary="+16 min total sleep time in insomnia-focused trials",
        population_summary="adults with insomnia symptoms or low magnesium intake",
        main_caveat="effect sizes are population-level and not diagnostic",
        uncertainty_factors=["baseline deficiency", "dose form"],
        claim_boundary="general wellness support only",
    )

    merged = merge_evidence({"model_type": "heuristic"}, profile)

    assert merged["evidence_profile"]["evidence_tier"] == "B"
    assert merged["evidence_profile"]["claim_boundary"] == "general wellness support only"
    assert merged["evidence_profile"]["uncertainty_factors"] == ["baseline deficiency", "dose form"]


def test_evidence_profile_rejects_invalid_tier():
    try:
        EvidenceProfile(
            evidence_tier="D",
            effect_summary="x",
            population_summary="y",
            main_caveat="z",
            uncertainty_factors=[],
            claim_boundary="wellness only",
        )
    except ValueError as exc:
        assert "evidence_tier" in str(exc)
    else:
        raise AssertionError("EvidenceProfile accepted an invalid tier")
```

- [ ] **Step 2: Run the Python test to verify it fails**

Run: `python -m pytest research/tests/test_evidence_contract.py -q`

Expected: `ModuleNotFoundError: No module named 'research.evidence_contract'`

- [ ] **Step 3: Implement the Python evidence contract**

```python
from dataclasses import dataclass
from typing import Literal

EvidenceTier = Literal["A", "B", "C"]


@dataclass(frozen=True)
class EvidenceProfile:
    evidence_tier: EvidenceTier
    effect_summary: str
    population_summary: str
    main_caveat: str
    uncertainty_factors: list[str]
    claim_boundary: str

    def __post_init__(self) -> None:
        if self.evidence_tier not in {"A", "B", "C"}:
            raise ValueError("evidence_tier must be one of: A, B, C")

    def as_dict(self) -> dict:
        return {
            "evidence_tier": self.evidence_tier,
            "effect_summary": self.effect_summary,
            "population_summary": self.population_summary,
            "main_caveat": self.main_caveat,
            "uncertainty_factors": list(self.uncertainty_factors),
            "claim_boundary": self.claim_boundary,
        }


def merge_evidence(payload: dict, profile: EvidenceProfile) -> dict:
    merged = dict(payload)
    merged["evidence_profile"] = profile.as_dict()
    return merged
```

- [ ] **Step 4: Write the failing TypeScript evidence-contract test**

```ts
import { describe, expect, it } from 'vitest'
import { buildEvidenceProfile } from './evidence'

describe('buildEvidenceProfile', () => {
  it('normalizes the shared evidence structure', () => {
    const profile = buildEvidenceProfile({
      evidenceTier: 'B',
      effectSummary: '+16 min total sleep time in insomnia-focused trials',
      populationSummary: 'Adults with insomnia symptoms or low magnesium intake',
      mainCaveat: 'Population-level effect, not diagnosis',
      uncertaintyFactors: ['baseline deficiency', 'dose form'],
      claimBoundary: 'General wellness support only',
    })

    expect(profile.evidenceTier).toBe('B')
    expect(profile.uncertaintyFactors).toEqual(['baseline deficiency', 'dose form'])
  })
})
```

- [ ] **Step 5: Run the TypeScript test to verify it fails**

Run: `npm run test -- src/lib/evidence.test.ts`

Expected: `Failed to resolve import "./evidence"`

- [ ] **Step 6: Implement the TypeScript mirror**

```ts
export type EvidenceTier = 'A' | 'B' | 'C'

export interface EvidenceProfile {
  evidenceTier: EvidenceTier
  effectSummary: string
  populationSummary: string
  mainCaveat: string
  uncertaintyFactors: string[]
  claimBoundary: string
}

export function buildEvidenceProfile(profile: EvidenceProfile): EvidenceProfile {
  return {
    ...profile,
    uncertaintyFactors: [...profile.uncertaintyFactors],
  }
}
```

- [ ] **Step 7: Wire the lab components to the shared evidence shape**

```vue
<script setup lang="ts">
import type { EvidenceProfile } from '@/lib/evidence'

defineProps<{ profile: EvidenceProfile }>()
</script>

<template>
  <div class="lab-evidence">
    <div class="lab-evidence__row">
      <span class="lab-evidence__key">Tier</span>
      <span class="lab-evidence__val">Tier {{ profile.evidenceTier }}</span>
    </div>
    <div class="lab-evidence__row">
      <span class="lab-evidence__key">Effect</span>
      <span class="lab-evidence__val">{{ profile.effectSummary }}</span>
    </div>
    <div class="lab-evidence__row">
      <span class="lab-evidence__key">Population</span>
      <span class="lab-evidence__val">{{ profile.populationSummary }}</span>
    </div>
    <div class="lab-evidence__row lab-evidence__row--caveat">
      <span class="lab-evidence__key">Caveat</span>
      <span class="lab-evidence__val">{{ profile.mainCaveat }}</span>
    </div>
    <div class="lab-evidence__row">
      <span class="lab-evidence__key">Boundary</span>
      <span class="lab-evidence__val">{{ profile.claimBoundary }}</span>
    </div>
  </div>
</template>
```

```vue
<template>
  <div class="lab-card bento-card">
    <div class="lab-card__header">
      <div class="lab-card__label">{{ label }}</div>
      <h2 class="lab-card__title">{{ title }}</h2>
    </div>
    <slot name="inputs" />
    <template v-if="hasOutput">
      <div class="lab-card__divider" />
      <slot name="output" />
      <div v-if="slots.evidence" class="lab-card__evidence-wrap lab-card__evidence-wrap--open">
        <slot name="evidence" />
      </div>
    </template>
    <div class="lab-card__citation">{{ citation }}</div>
  </div>
</template>
```

- [ ] **Step 8: Run both evidence-contract test commands**

Run:
- `python -m pytest research/tests/test_evidence_contract.py -q`
- `npm run test -- src/lib/evidence.test.ts`

Expected:
- `2 passed`
- `1 passed`

- [ ] **Step 9: Commit**

```bash
git add research/evidence_contract.py research/tests/test_evidence_contract.py src/lib/evidence.ts src/lib/evidence.test.ts src/components/lab/LabEvidenceBlock.vue src/components/lab/LabCard.vue
git commit -m "feat: add shared evidence contract for science surfaces"
```

### Task 2: Chronotype Engine Upgrade

**Files:**
- Modify: `research/chronotype_engine.py`
- Create: `research/tests/test_chronotype_engine.py`

- [ ] **Step 1: Write the failing chronotype regression tests**

```python
from datetime import datetime

from research.chronotype_engine import ChronotypeEngine, SleepLog


def make_log(date: str, onset_h: int, wake_h: int, alarm_used=None) -> SleepLog:
    return SleepLog(
        date=date,
        sleep_onset=datetime(2026, 4, int(date[-2:]), onset_h, 0),
        wake_time=datetime(2026, 4, int(date[-2:]), wake_h, 0),
        total_sleep_min=((wake_h - onset_h) % 24) * 60,
        alarm_used=alarm_used,
    )


def test_chronotype_prefers_alarm_flags_when_available():
    logs = [
        make_log("2026-04-01", 23, 6, True),
        make_log("2026-04-02", 23, 6, True),
        make_log("2026-04-05", 0, 8, False),
        make_log("2026-04-06", 0, 8, False),
    ]
    result = ChronotypeEngine().chronotype_from_logs(logs)
    assert result["day_classification"]["method"] == "alarm_used"


def test_chronotype_reports_low_confidence_for_irregular_schedule():
    logs = [
        make_log("2026-04-01", 22, 5, True),
        make_log("2026-04-02", 1, 9, True),
        make_log("2026-04-03", 23, 6, False),
        make_log("2026-04-04", 3, 11, False),
    ]
    result = ChronotypeEngine().chronotype_from_logs(logs)
    assert result["confidence"] == "low"
    assert "irregular schedule" in " ".join(result["warnings"]).lower()


def test_chronotype_returns_error_when_no_reliable_free_day_proxy_exists():
    logs = [
        make_log("2026-04-01", 23, 7, None),
        make_log("2026-04-02", 23, 7, None),
        make_log("2026-04-03", 23, 7, None),
    ]
    result = ChronotypeEngine().chronotype_from_logs(logs, work_days=None)
    assert result["error"] == "No reliable free-day proxy"
```

- [ ] **Step 2: Run the chronotype test to verify it fails**

Run: `python -m pytest research/tests/test_chronotype_engine.py -q`

Expected: `TypeError: SleepLog() got an unexpected keyword argument 'alarm_used'`

- [ ] **Step 3: Upgrade the engine with classification, confidence, and warnings**

```python
@dataclass
class SleepLog:
    date: str
    sleep_onset: datetime
    wake_time: datetime
    total_sleep_min: int
    deep_sleep_min: Optional[int] = None
    rem_sleep_min: Optional[int] = None
    hrv_avg: Optional[float] = None
    skin_temp_delta: Optional[float] = None
    resting_hr: Optional[float] = None
    sleep_score: Optional[int] = None
    source: str = "manual"
    alarm_used: Optional[bool] = None


def _classify_day_types(self, logs: list[SleepLog], work_days: Optional[set[int]]):
    alarm_logs = [l for l in logs if l.alarm_used is not None]
    if len([l for l in alarm_logs if l.alarm_used is True]) >= 2 and len([l for l in alarm_logs if l.alarm_used is False]) >= 2:
        return (
            [l for l in alarm_logs if l.alarm_used is True],
            [l for l in alarm_logs if l.alarm_used is False],
            {"method": "alarm_used"},
        )

    if work_days:
        work_logs = [l for l in logs if datetime.strptime(l.date, "%Y-%m-%d").weekday() in work_days]
        free_logs = [l for l in logs if datetime.strptime(l.date, "%Y-%m-%d").weekday() not in work_days]
        if len(work_logs) >= 2 and len(free_logs) >= 2:
            return work_logs, free_logs, {"method": "declared_work_days"}

    wake_minutes = sorted(
        (l, l.wake_time.hour * 60 + l.wake_time.minute) for l in logs
    )
    gaps = [
        (wake_minutes[idx + 1][1] - wake_minutes[idx][1], idx)
        for idx in range(len(wake_minutes) - 1)
    ]
    largest_gap, split_idx = max(gaps, default=(0, -1))
    if largest_gap >= 60 and split_idx >= 1 and split_idx < len(wake_minutes) - 2:
        work_logs = [pair[0] for pair in wake_minutes[: split_idx + 1]]
        free_logs = [pair[0] for pair in wake_minutes[split_idx + 1 :]]
        return work_logs, free_logs, {"method": "wake_gap"}

    return [], [], {"method": "none"}
```

```python
warnings = []
if onset_std_min > 90 or wake_std_min > 90:
    warnings.append("Irregular schedule reduces chronotype confidence.")

confidence_score = 0.35
if len(logs) >= 14:
    confidence_score += 0.2
if classification["method"] in {"alarm_used", "wake_gap"}:
    confidence_score += 0.15
if not warnings:
    confidence_score += 0.15

confidence = "high" if confidence_score >= 0.75 else "moderate" if confidence_score >= 0.55 else "low"
```

- [ ] **Step 4: Return the richer chronotype payload**

```python
return {
    "chronotype": self.chronotype_label(msf_hour),
    "msf": msf.strftime("%H:%M"),
    "msf_sc": msf_sc.strftime("%H:%M"),
    "social_jet_lag_hours": round(sjl, 1),
    "confidence": confidence,
    "confidence_score": round(confidence_score, 2),
    "data_sufficiency": "good" if len(logs) >= 14 else "limited" if len(logs) >= 7 else "minimum",
    "warnings": warnings,
    "day_classification": {
        **classification,
        "work_count": len(work_logs),
        "free_count": len(free_logs),
    },
    "wearable_support": "available" if wearable_rows >= 5 else "missing",
    "data_days": len(logs),
}
```

- [ ] **Step 5: Run the chronotype test again**

Run: `python -m pytest research/tests/test_chronotype_engine.py -q`

Expected: `3 passed`

- [ ] **Step 6: Commit**

```bash
git add research/chronotype_engine.py research/tests/test_chronotype_engine.py
git commit -m "feat: upgrade chronotype engine confidence and day classification"
```

### Task 3: Recalibrate Core Research Models

**Files:**
- Modify: `research/caffeine_model.py`
- Modify: `research/light_model.py`
- Modify: `research/alcohol_model.py`
- Create: `research/tests/test_model_evidence_profiles.py`
- Modify: `research/tests/test_language_hardening.py`

- [ ] **Step 1: Write the failing model-evidence tests**

```python
from datetime import datetime

from research.alcohol_model import AlcoholModel
from research.caffeine_model import CaffeineDose, CaffeineModel, CaffeineProfile
from research.light_model import CircadianLightModel


def test_caffeine_sleep_impact_exposes_tier_b_boundary():
    result = CaffeineModel().sleep_impact(
        doses=[CaffeineDose(mg=200, time=datetime(2026, 4, 5, 14, 0))],
        bedtime=datetime(2026, 4, 5, 23, 0),
        profile=CaffeineProfile(),
    )
    assert result["evidence_profile"]["evidence_tier"] == "B"
    assert "healthy adult" in result["evidence_profile"]["population_summary"].lower()


def test_light_model_exposes_tier_a_zone_and_tier_b_delay_boundary():
    result = CircadianLightModel().melatonin_suppression(100, 2.0)
    assert result["evidence_profile"]["evidence_tier"] == "B"
    assert "heuristic" in result["evidence_profile"]["claim_boundary"].lower()


def test_alcohol_sleep_impact_marks_bac_math_as_stronger_than_sleep_forecast():
    result = AlcoholModel().sleep_impact(3, 4, 80.0, "male")
    assert result["evidence_profile"]["evidence_tier"] == "B"
    assert "widmark" in result["method_summary"].lower()
```

- [ ] **Step 2: Run the research-model tests to verify they fail**

Run: `python -m pytest research/tests/test_model_evidence_profiles.py -q`

Expected: key errors for missing `evidence_profile` and `method_summary`

- [ ] **Step 3: Attach evidence metadata to caffeine, light, and alcohol outputs**

```python
from research.evidence_contract import EvidenceProfile, merge_evidence

CAFFEINE_SLEEP_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="Sleep-latency and efficiency estimates based on dose timing studies",
    population_summary="Healthy adults, mostly controlled laboratory sleep studies",
    main_caveat="Remaining caffeine is modeled directly, but sleep disruption is still a heuristic mapping",
    uncertainty_factors=["CYP1A2 variability", "ADORA2A sensitivity", "oral contraceptives", "smoking"],
    claim_boundary="Use for conservative bedtime planning, not a deterministic personal forecast",
)

return merge_evidence(
    {
        "impact_level": impact_level,
        "remaining_mg": remaining_mg,
        "sleep_latency_increase_min": latency_increase,
        "fragmentation_risk": fragmentation_risk,
        "method_summary": "Pharmacokinetics are Tier A; sleep-impact mapping is Tier B heuristic.",
        "advisory": advisory,
    },
    CAFFEINE_SLEEP_PROFILE,
)
```

```python
LIGHT_SUPPRESSION_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="Estimated melatonin suppression and sleep-onset delay under melanopic light exposure",
    population_summary="Controlled laboratory light-exposure studies in healthy adults and adolescents",
    main_caveat="Suppression is modeled from dose-response curves; individual delay can vary substantially",
    uncertainty_factors=["age", "sensitivity", "duration", "spectral composition"],
    claim_boundary="Useful for light-risk planning, not validated as an exact personal delay forecast",
)
```

```python
ALCOHOL_SLEEP_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="BAC-informed estimates of HRV suppression, REM reduction, and fragmentation risk",
    population_summary="Oura observational cohorts plus controlled alcohol-and-sleep literature",
    main_caveat="BAC math is stronger than the sleep-architecture forecast built on top of it",
    uncertainty_factors=["sex", "body mass", "meal timing", "clearance rate", "habitual tolerance"],
    claim_boundary="General next-night risk guidance only",
)
```

- [ ] **Step 4: Run both research test files**

Run:
- `python -m pytest research/tests/test_model_evidence_profiles.py -q`
- `python -m pytest research/tests/test_language_hardening.py -q`

Expected:
- `3 passed`
- existing language-hardening assertions remain green

- [ ] **Step 5: Commit**

```bash
git add research/caffeine_model.py research/light_model.py research/alcohol_model.py research/tests/test_model_evidence_profiles.py research/tests/test_language_hardening.py
git commit -m "feat: add evidence tiers to core research models"
```

### Task 4: Recalibrate Applied and Exploratory Models

**Files:**
- Modify: `research/breathwork_model.py`
- Modify: `research/nap_model.py`
- Modify: `research/space_weather_bio.py`
- Modify: `research/tests/test_language_hardening.py`
- Modify: `research/tests/test_space_weather_bio.py`

- [ ] **Step 1: Extend the failing tests for breathwork, nap, and space weather**

```python
from datetime import datetime

from research.breathwork_model import BreathworkModel
from research.nap_model import NapModel
from research.space_weather_bio import SpaceWeatherBioModel, SpaceWeatherReading


def test_breathwork_recommendation_exposes_tier_b_boundary():
    result = BreathworkModel().session_recommendation("stress", 38.0)
    assert result["evidence_profile"]["evidence_tier"] == "B"
    assert "acute response" in result["evidence_profile"]["main_caveat"].lower()


def test_nap_recommendation_marks_study_specific_outputs():
    result = NapModel().recommendation(14.0, 7.0, 23.0, 7.0, sleep_debt_hours=2.5, goal="alertness")
    assert result["evidence_profile"]["evidence_tier"] == "B"
    assert "study-specific" in result["evidence_profile"]["main_caveat"].lower()


def test_space_weather_composite_is_tier_c_context_only():
    result = SpaceWeatherBioModel().composite_disruption(
        SpaceWeatherReading(kp_index=6.0, solar_wind_speed=650.0, bz=-12.0, timestamp=datetime(2026, 4, 5, 14, 0))
    )
    assert result["evidence_profile"]["evidence_tier"] == "C"
    assert "exploratory" in result["evidence_profile"]["claim_boundary"].lower()
```

- [ ] **Step 2: Run the research tests to verify they fail**

Run:
- `python -m pytest research/tests/test_language_hardening.py -q`
- `python -m pytest research/tests/test_space_weather_bio.py -q`

Expected: missing `evidence_profile` keys in the new assertions

- [ ] **Step 3: Attach evidence profiles and narrower boundaries**

```python
BREATHWORK_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="Short-term parasympathetic and HRV-oriented protocol estimates",
    population_summary="Acute breathwork studies in healthy or stressed adults",
    main_caveat="Acute response is variable and should not be treated as a personal biometric prediction",
    uncertainty_factors=["technique familiarity", "baseline stress", "measurement noise"],
    claim_boundary="Protocol guidance for same-day regulation only",
)
```

```python
NAP_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="Alertness and recovery estimates from controlled nap studies",
    population_summary="Healthy adults, fatigue studies, and selected NASA operational cohorts",
    main_caveat="Study-specific nap durations do not guarantee the same outcome for every sleeper",
    uncertainty_factors=["sleep debt", "chronotype", "nap timing", "sleep inertia"],
    claim_boundary="Use to choose a nap strategy, not to guarantee cognitive lift",
)
```

```python
SPACE_WEATHER_PROFILE = EvidenceProfile(
    evidence_tier="C",
    effect_summary="Exploratory geomagnetic context for conservative recovery planning",
    population_summary="Observational HRV, melatonin, and cognition literature with uncertain individual relevance",
    main_caveat="Associations are population-level and not validated for personal biological forecasting",
    uncertainty_factors=["latitude", "baseline sensitivity", "comorbid stressors", "measurement lag"],
    claim_boundary="Context only; never the sole basis for a strong personal recommendation",
)
```

- [ ] **Step 4: Re-run the three research test commands**

Run:
- `python -m pytest research/tests/test_language_hardening.py -q`
- `python -m pytest research/tests/test_space_weather_bio.py -q`
- `python -m pytest research/tests/test_model_evidence_profiles.py -q`

Expected: all pass together

- [ ] **Step 5: Commit**

```bash
git add research/breathwork_model.py research/nap_model.py research/space_weather_bio.py research/tests/test_language_hardening.py research/tests/test_space_weather_bio.py
git commit -m "feat: narrow exploratory model claims and add evidence boundaries"
```

### Task 5: Supplement Guidance Redesign

**Files:**
- Create: `src/composables/lab/supplementCatalog.ts`
- Modify: `src/composables/lab/useSupplementGuide.ts`
- Modify: `src/composables/lab/useSupplementGuide.test.ts`
- Modify: `src/components/lab/SupplementGuideCard.vue`

- [ ] **Step 1: Write the failing supplement tests for goals and safety framing**

```ts
import { describe, expect, it } from 'vitest'
import { scoreSupplements } from './useSupplementGuide'

describe('scoreSupplements', () => {
  it('prioritizes melatonin for circadian realignment with travel context', () => {
    const results = scoreSupplements({
      goal: 'circadian_realignment',
      avgHRV: 48,
      avgSleepScore: 78,
      avgTotalSleepH: 7.1,
      chronotype: 'late',
      travelState: 'eastbound_shift',
    })
    expect(results[0].key).toBe('melatonin')
    expect(results[0].clinicianDisclaimer).toContain('consult a clinician')
  })

  it('keeps magnesium ahead of glycine when recovery debt is the main issue', () => {
    const results = scoreSupplements({
      goal: 'recovery_support',
      avgHRV: 34,
      avgSleepScore: 69,
      avgTotalSleepH: 6.1,
      chronotype: 'intermediate',
      travelState: 'none',
    })
    expect(results[0].key).toBe('magnesium')
    expect(results[0].evidenceTier).toBe('B')
  })
})
```

- [ ] **Step 2: Run the supplement test to verify it fails**

Run: `npm run test -- src/composables/lab/useSupplementGuide.test.ts`

Expected: type errors or function signature mismatch because `scoreSupplements` still accepts positional biometrics only

- [ ] **Step 3: Extract a supplement catalog with goal tags and contraindications**

```ts
export type SupplementGoal =
  | 'sleep_onset'
  | 'recovery_support'
  | 'stress_resilience'
  | 'jet_lag_support'
  | 'circadian_realignment'

export interface SupplementDefinition {
  key: 'magnesium' | 'ashwagandha' | 'glycine' | 'melatonin'
  goals: SupplementGoal[]
  evidenceTier: 'B'
  effect: string
  population: string
  caveat: string
  contraindications: string[]
  clinicianDisclaimer: string
}
```

- [ ] **Step 4: Redesign the scoring API around a context object**

```ts
export interface SupplementContext {
  goal: SupplementGoal
  avgHRV: number | null
  avgSleepScore: number | null
  avgTotalSleepH: number | null
  chronotype: 'early' | 'intermediate' | 'late'
  travelState: 'none' | 'eastbound_shift' | 'westbound_shift'
}

export function scoreSupplements(context: SupplementContext): RankedSupplement[] {
  const base = scoreCatalogAgainstGoal(context.goal)
  const biometricsAdjusted = applyBiometricAdjustments(base, context)
  return biometricsAdjusted.sort((a, b) => b.score - a.score)
}
```

- [ ] **Step 5: Add the bounded goal selector and clinician disclaimer to the card**

```vue
<script setup lang="ts">
const selectedGoal = ref<SupplementGoal>('sleep_onset')
</script>

<template>
  <label class="sg-goal">
    <span class="sg-goal__label">Goal</span>
    <select v-model="selectedGoal" class="sg-goal__select">
      <option value="sleep_onset">Fall asleep faster</option>
      <option value="recovery_support">Recover better</option>
      <option value="stress_resilience">Handle stress</option>
      <option value="jet_lag_support">Jet lag support</option>
      <option value="circadian_realignment">Circadian realignment</option>
    </select>
  </label>

  <p class="sg-disclaimer">
    General wellness guidance only. If you have a medical condition, take medication, are pregnant, or are unsure, consult a clinician before using supplements.
  </p>
</template>
```

- [ ] **Step 6: Run the supplement test again**

Run: `npm run test -- src/composables/lab/useSupplementGuide.test.ts`

Expected: `2 passed` plus the existing healthy/null boundary tests after they are updated to the new object signature

- [ ] **Step 7: Commit**

```bash
git add src/composables/lab/supplementCatalog.ts src/composables/lab/useSupplementGuide.ts src/composables/lab/useSupplementGuide.test.ts src/components/lab/SupplementGuideCard.vue
git commit -m "feat: redesign supplement guidance around goals and safety boundaries"
```

### Task 6: AI Prompt and Backend Context Alignment

**Files:**
- Create: `src/lib/chatContext.ts`
- Create: `src/lib/chatContext.test.ts`
- Modify: `src/composables/useAI.ts`
- Modify: `backend/chat/router.py`
- Modify: `backend/chat/prompt_builder.py`
- Modify: `backend/tests/test_prompt_builder_truthfulness.py`

- [ ] **Step 1: Write the failing backend-context and prompt-boundary tests**

```python
from backend.chat.prompt_builder import build_system_prompt


def test_prompt_uses_real_context_values_instead_of_na_placeholders():
    prompt = build_system_prompt(
        lat=51.5,
        lng=-0.12,
        timezone="Europe/London",
        user_id="user-123",
        user_sleep_time="22:45",
        user_chronotype="late",
        solar_context={"phase": "Night", "elevation": -12.5, "sunrise": "06:08", "sunset": "19:47", "solar_noon": "12:58"},
        space_weather_context={"kp_index": 4.0, "label": "Active", "bz": -6.0, "solar_wind": 520, "advisory": "Observational context only"},
        environment_context={"uv_index": 0, "temperature": 18, "night_temp": 12, "aqi": 38, "humidity": 74},
    )
    assert "Elevation: -12.5" in prompt
    assert "Data loading..." not in prompt
    assert "Usual sleep time: 22:45" in prompt
```

```ts
import { describe, expect, it } from 'vitest'
import { buildChatContextSnapshot } from './chatContext'

describe('buildChatContextSnapshot', () => {
  it('serializes live store values for authenticated backend chat', () => {
    const snapshot = buildChatContextSnapshot({
      geo: { lat: 51.5, lng: -0.12, timezone: 'Europe/London', locationName: 'London, UK' },
      solar: { solarPhase: 'Night', elevationDeg: -12.5, sunriseTime: '06:08', sunsetTime: '19:47', solarNoon: '12:58' },
      spaceWeather: { kpIndex: 4, disruptionLabel: 'Active', bzComponent: -6, solarWindSpeed: 520, disruptionAdvisory: 'Observational context only' },
      environment: { uvIndexNow: 0, temperatureNow: 18, temperatureNight: 12, aqiLevel: 38, humidity: 74 },
      protocol: { wakeWindow: '07:00', caffeineCutoff: '14:30', peakFocus: '15:00-18:00', windDown: '21:30', sleepTarget: '22:45' },
      user: { usualSleepTime: '22:45', chronotype: 'late' },
    })
    expect(snapshot.user.sleep_time).toBe('22:45')
    expect(snapshot.space_weather.kp_index).toBe(4)
  })
})
```

- [ ] **Step 2: Run the failing tests**

Run:
- `python -m pytest backend/tests/test_prompt_builder_truthfulness.py -q`
- `npm run test -- src/lib/chatContext.test.ts`

Expected:
- backend test fails because `build_system_prompt` lacks the new context kwargs
- frontend test fails because `src/lib/chatContext.ts` does not exist

- [ ] **Step 3: Add a pure context-serialization helper on the frontend**

```ts
export function buildChatContextSnapshot(input: {
  geo: { lat: number; lng: number; timezone: string; locationName: string }
  solar: { solarPhase: string; elevationDeg: number; sunriseTime: string; sunsetTime: string; solarNoon: string }
  spaceWeather: { kpIndex: number; disruptionLabel: string; bzComponent: number; solarWindSpeed: number; disruptionAdvisory: string }
  environment: { uvIndexNow: number; temperatureNow: number; temperatureNight: number; aqiLevel: number; humidity: number }
  protocol: { wakeWindow: string; caffeineCutoff: string; peakFocus: string; windDown: string; sleepTarget: string }
  user: { usualSleepTime: string; chronotype: string }
}) {
  return {
    location: input.geo,
    solar: {
      phase: input.solar.solarPhase,
      elevation: input.solar.elevationDeg,
      sunrise: input.solar.sunriseTime,
      sunset: input.solar.sunsetTime,
      solar_noon: input.solar.solarNoon,
    },
    space_weather: {
      kp_index: input.spaceWeather.kpIndex,
      label: input.spaceWeather.disruptionLabel,
      bz: input.spaceWeather.bzComponent,
      solar_wind: input.spaceWeather.solarWindSpeed,
      advisory: input.spaceWeather.disruptionAdvisory,
    },
    environment: {
      uv_index: input.environment.uvIndexNow,
      temperature: input.environment.temperatureNow,
      night_temp: input.environment.temperatureNight,
      aqi: input.environment.aqiLevel,
      humidity: input.environment.humidity,
    },
    protocol: input.protocol,
    user: {
      sleep_time: input.user.usualSleepTime,
      chronotype: input.user.chronotype,
    },
  }
}
```

- [ ] **Step 4: Expand the backend context model and prompt builder**

```python
class ChatContext(BaseModel):
    lat: float
    lng: float
    timezone: str
    solar: dict | None = None
    space_weather: dict | None = None
    environment: dict | None = None
    protocol: dict | None = None
    user: dict | None = None
```

```python
def build_system_prompt(
    lat: float,
    lng: float,
    timezone: str,
    user_id: str,
    memory_block: str = "",
    user_sleep_time: str = "23:00",
    user_chronotype: str = "intermediate",
    solar_context: Optional[dict] = None,
    space_weather_context: Optional[dict] = None,
    environment_context: Optional[dict] = None,
    protocol_context: Optional[dict] = None,
) -> str:
    solar_phase = solar_context["phase"] if solar_context else "Unknown"
    solar_elevation = solar_context["elevation"] if solar_context else "Unknown"
    sunrise = solar_context["sunrise"] if solar_context else "Unknown"
    sunset = solar_context["sunset"] if solar_context else "Unknown"
    kp_index = space_weather_context["kp_index"] if space_weather_context else "Unknown"
    disruption_label = space_weather_context["label"] if space_weather_context else "Unknown"
    return f"""You are HELIOS, a circadian intelligence engine.
SOLAR: {solar_phase} | Elevation: {solar_elevation}° | Sunrise: {sunrise} | Sunset: {sunset}
SPACE WEATHER: Kp Index: {kp_index} ({disruption_label})
CURRENT PROTOCOL: Wake Window: {protocol_context["wakeWindow"] if protocol_context else "Unknown"}
"""
```

- [ ] **Step 5: Run the context and prompt tests again**

Run:
- `python -m pytest backend/tests/test_prompt_builder_truthfulness.py -q`
- `npm run test -- src/lib/chatContext.test.ts`

Expected:
- backend prompt tests stay green and the new context-value assertions pass
- chat-context test passes

- [ ] **Step 6: Commit**

```bash
git add src/lib/chatContext.ts src/lib/chatContext.test.ts src/composables/useAI.ts backend/chat/router.py backend/chat/prompt_builder.py backend/tests/test_prompt_builder_truthfulness.py
git commit -m "feat: align authenticated prompt context with live science data"
```

### Task 7: Docs and Investor-Facing Research Alignment

**Files:**
- Modify: `research/RESEARCH.md`
- Modify: `research/RESEARCH_V2.md`
- Modify: `README.md`

- [ ] **Step 1: Write the doc cleanup checklist into the files before editing prose**

```md
- Tier A = validated foundations
- Tier B = citation-informed heuristic
- Tier C = exploratory / observational context
- Remove placeholder claims about live backend data
- Remove contradictions about Mem0 versus markdown memory
- State current implementation boundaries explicitly
```

- [ ] **Step 2: Replace contradictory architecture language in `research/RESEARCH.md`**

```md
### How It Works
- Hermes is the current per-user background learner.
- Memory is stored as structured markdown in Postgres.
- Prompt enrichment currently injects markdown memory blocks.
- Mem0 is not part of the shipped path and should not be described as active architecture.
```

- [ ] **Step 3: Add evidence-tier language to `research/RESEARCH_V2.md` and the root README**

```md
## Evidence Language
- Tier A: strong foundations used for primary timing guidance
- Tier B: heuristic calculators built from peer-reviewed literature
- Tier C: exploratory context only, never a deterministic personal forecast
```

```md
# HELIOS

HELIOS is a consumer sleep optimizer and circadian operating system. It combines chronotype inference, light timing, caffeine timing, travel context, and selected wellness tools.

What is strong today:
- chronotype from sleep timing
- circadian light and timing guidance
- caffeine timing and bedtime burden estimation

What is heuristic today:
- alcohol, nap, breathwork, supplement, and exercise timing guidance

What is exploratory today:
- space-weather biological context
```

- [ ] **Step 4: Run targeted grep checks so the contradictions are actually gone**

Run:
- `rg -n "Mem0|science-backed|individually validated|Data loading" research/RESEARCH.md research/RESEARCH_V2.md README.md backend/chat/prompt_builder.py`

Expected:
- no active-architecture Mem0 references
- no blanket `science-backed` flattening language
- no placeholder backend prompt text

- [ ] **Step 5: Commit**

```bash
git add research/RESEARCH.md research/RESEARCH_V2.md README.md
git commit -m "docs: align research narrative with current evidence tiers"
```

### Task 8: Final Verification and Integration Check

**Files:**
- Verify only

- [ ] **Step 1: Run the Python science test suite**

Run:
- `python -m pytest research/tests/test_evidence_contract.py research/tests/test_chronotype_engine.py research/tests/test_model_evidence_profiles.py research/tests/test_language_hardening.py research/tests/test_space_weather_bio.py -q`

Expected: all tests pass

- [ ] **Step 2: Run the frontend Vitest suite for affected files**

Run:
- `npm run test -- src/lib/evidence.test.ts`
- `npm run test -- src/lib/chatContext.test.ts`
- `npm run test -- src/composables/lab/useSupplementGuide.test.ts`
- `npm run test -- src/composables/useStagedReveal.test.ts`
- `npm run test -- src/composables/useCobeGlobeData.test.ts`

Expected: all pass

- [ ] **Step 3: Run the backend prompt truthfulness test**

Run: `python -m pytest backend/tests/test_prompt_builder_truthfulness.py -q`

Expected: pass with no placeholder-context regressions

- [ ] **Step 4: Run the production build**

Run: `npm run build`

Expected: `vue-tsc` and Vite both succeed

- [ ] **Step 5: Create the integration commit**

```bash
git add research src backend README.md
git commit -m "feat: harden HELIOS science and algorithm credibility surfaces"
```

- [ ] **Step 6: Capture residual risks in the final handoff**

```md
- Backend security hardening is still a separate follow-up spec.
- Wearable-informed chronotype refinement is confidence-adjusting, not a full circadian phase estimator yet.
- Supplement guidance remains wellness support and should not be marketed as diagnosis or treatment.
```
