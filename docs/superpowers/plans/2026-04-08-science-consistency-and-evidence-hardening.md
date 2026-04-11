# Science Consistency and Evidence Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make HELIOS scientifically self-consistent and reduce pseudo-scientific overreach by aligning timing logic, renaming misleading metrics, and downgrading weak-evidence outputs from deterministic predictions to clearly labeled heuristics.

**Architecture:** Extract the most fragile frontend timing and naming decisions into a small pure TypeScript helper module so they can be tested with Vitest before wiring them into the Pinia stores and Vue components. On the Python side, add a minimal `pytest` path that guards prompt wording and research-model advisory language, then harden the space-weather and V2 research modules in place without changing the product roadmap.

**Tech Stack:** Vue 3 + Pinia + TypeScript + Vitest, FastAPI/Python + pytest, Vite build, Markdown docs.

---

## File Map

### Frontend consistency boundary

- Create: `src/lib/circadianTruth.ts`
- Create: `src/lib/circadianTruth.test.ts`
- Modify: `package.json`
- Modify: `src/stores/protocol.ts`
- Modify: `src/components/SocialJetLagScore.vue`
- Modify: `src/stores/jetlag.ts`

Responsibility split:

- `src/lib/circadianTruth.ts` owns reusable timing/naming heuristics that should be testable without Pinia or Vue.
- `src/stores/protocol.ts` consumes those helpers and exposes UI-ready timing/state.
- `src/components/SocialJetLagScore.vue` only renders the renamed alignment metric and its copy.
- `src/stores/jetlag.ts` keeps schedule generation but uses corrected caffeine wording.

### Prompt and low-certainty advisory boundary

- Modify: `src/composables/useAI.ts`
- Modify: `backend/chat/prompt_builder.py`
- Modify: `src/stores/spaceWeather.ts`
- Modify: `backend/requirements.txt`
- Create: `backend/tests/test_prompt_builder_truthfulness.py`

Responsibility split:

- `useAI.ts` and `prompt_builder.py` must agree on the same evidence posture.
- `spaceWeather.ts` must present low-certainty, non-deterministic advisory copy.
- `backend/tests/test_prompt_builder_truthfulness.py` guards the backend prompt wording against regressions.

### Research-model hardening boundary

- Modify: `research/requirements.txt`
- Modify: `research/space_weather_bio.py`
- Modify: `research/caffeine_model.py`
- Modify: `research/light_model.py`
- Modify: `research/alcohol_model.py`
- Modify: `research/breathwork_model.py`
- Modify: `research/nap_model.py`
- Create: `research/tests/test_space_weather_bio.py`
- Create: `research/tests/test_language_hardening.py`

Responsibility split:

- `space_weather_bio.py` is the strongest pseudo-scientific risk and gets its own dedicated tests.
- The remaining research modules keep their current function signatures where practical, but their advisory strings and metadata must be hardened and labeled honestly.

### Documentation alignment boundary

- Modify: `research/RESEARCH.md`
- Modify: `research/RESEARCH_V2.md`
- Optional modify: `PRD.md`
- Optional modify: `MARKETING.md`
- Optional modify: `TECHNICAL.md`

Responsibility split:

- Research docs must separate literature findings, heuristic implementations, and roadmap items.
- Root docs are only touched if they repeat the exact contradictions fixed in code.

---

### Task 1: Frontend Timing Consistency and Metric Rename

**Files:**
- Modify: `package.json`
- Create: `src/lib/circadianTruth.ts`
- Create: `src/lib/circadianTruth.test.ts`
- Modify: `src/stores/protocol.ts:50-275`
- Modify: `src/components/SocialJetLagScore.vue:1-52`
- Modify: `src/stores/jetlag.ts:128-245`

- [ ] **Step 1: Write the failing Vitest tests**

Create `src/lib/circadianTruth.test.ts`:

```ts
import { describe, expect, it } from 'vitest'
import {
  getDeepWorkWindowOffsets,
  getAlignmentMetricCopy,
  getCaffeineCutoffNarrative,
} from './circadianTruth'

describe('getDeepWorkWindowOffsets', () => {
  it('moves the recommended deep-work window earlier for early chronotypes', () => {
    expect(getDeepWorkWindowOffsets('early')).toEqual({ startHoursAfterWake: 5, endHoursAfterWake: 8 })
  })

  it('uses a middle daytime window for intermediate chronotypes', () => {
    expect(getDeepWorkWindowOffsets('intermediate')).toEqual({ startHoursAfterWake: 6, endHoursAfterWake: 9 })
  })

  it('moves the recommended deep-work window later for late chronotypes', () => {
    expect(getDeepWorkWindowOffsets('late')).toEqual({ startHoursAfterWake: 8, endHoursAfterWake: 11 })
  })
})

describe('getAlignmentMetricCopy', () => {
  it('does not label the solar-midnight proxy as social jet lag', () => {
    const copy = getAlignmentMetricCopy()
    expect(copy.label).toBe('SOLAR ALIGNMENT')
    expect(copy.description).toContain('solar midnight')
    expect(copy.description).not.toContain('workday')
    expect(copy.description).not.toContain('Social Jet Lag')
  })
})

describe('getCaffeineCutoffNarrative', () => {
  it('uses default-risk language instead of guaranteed safety or melatonin suppression language', () => {
    const text = getCaffeineCutoffNarrative('16:00', '21:30')
    expect(text).toContain('default conservative cutoff')
    expect(text).toContain('possible circadian phase delay')
    expect(text).not.toContain('guarantees safety')
    expect(text).not.toContain('melatonin suppression')
  })
})
```

- [ ] **Step 2: Add Vitest and run the test to verify it fails**

Modify `package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.2.2",
    "@types/node": "^24.12.0",
    "@vitejs/plugin-vue": "^6.0.5",
    "@vue/tsconfig": "^0.9.0",
    "tailwindcss": "^4.2.2",
    "typescript": "~5.9.3",
    "vite": "^8.0.1",
    "vite-plugin-pwa": "^1.2.0",
    "vitest": "^3.2.4",
    "vue-tsc": "^3.2.5"
  }
}
```

Run:

```bash
npm install
npm run test -- src/lib/circadianTruth.test.ts
```

Expected:

- `npm install` updates `package-lock.json`
- `npm run test -- src/lib/circadianTruth.test.ts` fails with an import/module-not-found error for `./circadianTruth`

- [ ] **Step 3: Write the minimal helper implementation**

Create `src/lib/circadianTruth.ts`:

```ts
export type Chronotype = 'early' | 'intermediate' | 'late'

export function getDeepWorkWindowOffsets(chronotype: Chronotype): {
  startHoursAfterWake: number
  endHoursAfterWake: number
} {
  if (chronotype === 'early') return { startHoursAfterWake: 5, endHoursAfterWake: 8 }
  if (chronotype === 'late') return { startHoursAfterWake: 8, endHoursAfterWake: 11 }
  return { startHoursAfterWake: 6, endHoursAfterWake: 9 }
}

export function getAlignmentMetricCopy(): {
  label: string
  description: string
} {
  return {
    label: 'SOLAR ALIGNMENT',
    description: 'Difference between solar midnight and your estimated sleep midpoint.',
  }
}

export function getCaffeineCutoffNarrative(cutoffTime: string, estimatedSleepTime: string): string {
  return `Default conservative cutoff: no caffeine after ${cutoffTime}. This reduces residual caffeine near ${estimatedSleepTime} and lowers the risk of possible sleep disruption or circadian phase delay, but it does not guarantee safety for every dose or every metabolism.`
}
```

- [ ] **Step 4: Wire the helper into the store and component code**

Update the relevant parts of `src/stores/protocol.ts`:

```ts
import { getAlignmentMetricCopy, getCaffeineCutoffNarrative, getDeepWorkWindowOffsets } from '@/lib/circadianTruth'

const solarAlignmentGapMinutes = computed<number>(() => {
  try {
    const sleepMidpoint = addHours(sleepTime.value, 4)
    const nadirMinOfDay = solar.nadir.getHours() * 60 + solar.nadir.getMinutes()
    const midpointMinOfDay = sleepMidpoint.getHours() * 60 + sleepMidpoint.getMinutes()
    let diff = Math.abs(nadirMinOfDay - midpointMinOfDay)
    if (diff > 720) diff = 1440 - diff
    return Math.min(Math.round(diff), 360)
  } catch {
    return 0
  }
})

const peakFocusStart = computed<Date>(() => {
  const offsets = getDeepWorkWindowOffsets(user.chronotype)
  return addHours(dailyProtocol.value.wakeWindow.time, offsets.startHoursAfterWake)
})

const peakFocusEnd = computed<Date>(() => {
  const offsets = getDeepWorkWindowOffsets(user.chronotype)
  return addHours(dailyProtocol.value.wakeWindow.time, offsets.endHoursAfterWake)
})
```

Replace the UI copy in `dailyProtocol.peakFocus.subtitle` and `dailyProtocol.caffeineCutoff.subtitle`:

```ts
subtitle: `Recommended deep-work window: ${fmt(peakFocusStart.value)} – ${fmt(peakFocusEnd.value)}. The pre-sleep wake-maintenance zone is a separate alertness phenomenon, not your default best focus window.`
```

```ts
subtitle: getCaffeineCutoffNarrative(fmt(caffeineCutoff.value), fmt(sleepTime.value))
```

Update `src/components/SocialJetLagScore.vue`:

```ts
import { getAlignmentMetricCopy } from '@/lib/circadianTruth'

const copy = getAlignmentMetricCopy()
const minutes = computed(() => Math.min(protocol.solarAlignmentGapMinutes, 360))
```

```vue
<span class="sjl-label font-mono">{{ copy.label }}</span>
<span class="sjl-desc">{{ copy.description }}</span>
```

Update the caffeine wording in `src/stores/jetlag.ts`:

```ts
/**
 * - Caffeine is permitted from local wake time and cut off 6 h before the
 *   target sleep time as a conservative default to reduce residual caffeine
 *   burden and possible phase/sleep disruption.
 */
```

- [ ] **Step 5: Run the tests and build to verify the wiring**

Run:

```bash
npm run test -- src/lib/circadianTruth.test.ts
npm run build
```

Expected:

- Vitest shows all tests in `src/lib/circadianTruth.test.ts` passing
- Vite build exits `0`

- [ ] **Step 6: Commit**

```bash
git add package.json package-lock.json src/lib/circadianTruth.ts src/lib/circadianTruth.test.ts src/stores/protocol.ts src/components/SocialJetLagScore.vue src/stores/jetlag.ts
git commit -m "Align circadian timing copy and rename solar alignment metric"
```

---

### Task 2: Prompt and Space-Weather Advisory Hardening

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/tests/test_prompt_builder_truthfulness.py`
- Modify: `backend/chat/prompt_builder.py:69-156`
- Modify: `src/composables/useAI.ts:72-163`
- Modify: `src/stores/spaceWeather.ts:59-69`

- [ ] **Step 1: Write the failing Python tests for backend prompt truthfulness**

Create `backend/tests/test_prompt_builder_truthfulness.py`:

```python
from backend.chat.prompt_builder import build_system_prompt


def test_prompt_labels_geomagnetic_claims_as_limited_observational_research():
    prompt = build_system_prompt(
        lat=16.0544,
        lng=108.2022,
        timezone="Asia/Ho_Chi_Minh",
        user_id="test-user",
    )

    assert "limited observational research" in prompt
    assert "uncertain individual relevance" in prompt


def test_prompt_does_not_force_causal_space_weather_sleep_explanations():
    prompt = build_system_prompt(
        lat=16.0544,
        lng=108.2022,
        timezone="Asia/Ho_Chi_Minh",
        user_id="test-user",
    )

    assert "Explain how current space weather affects their sleep" not in prompt
    assert "cortisol elevation" not in prompt
    assert "HRV suppression" not in prompt
```

- [ ] **Step 2: Add pytest and run the test to verify it fails**

Modify `backend/requirements.txt`:

```txt
fastapi>=0.115.0
uvicorn>=0.32.0
httpx>=0.27.0
supabase>=2.0.0
# mem0ai removed — using Hermes + markdown memory files instead
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.9
cryptography>=43.0.0
astral>=3.2
cachetools>=5.5.0
numpy>=1.24.0
pandas>=2.0.0
fitparse>=1.2.0
lxml>=5.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pytest>=8.3.0
```

Run:

```bash
python -m pip install -r backend/requirements.txt
python -m pytest backend/tests/test_prompt_builder_truthfulness.py -q
```

Expected:

- `pytest` fails because the current prompt still contains deterministic/causal wording

- [ ] **Step 3: Make the minimal backend and frontend prompt changes**

Update the space-weather section in `backend/chat/prompt_builder.py`:

```python
GEOMAGNETIC ACTIVITY & SLEEP:
- Limited observational research has reported associations between geomagnetic activity and sleep-, HRV-, and cognition-related measures.
- Evidence strength is uneven: HRV associations are stronger than melatonin associations, and individual relevance is uncertain.
- Do not present current Kp or Bz values as a deterministic personal sleep forecast.
- If relevant, describe this as exploratory context that may justify more conservative recovery behavior, not as a proven causal mechanism in the user.
```

Replace the rules block lines about space weather:

```python
3. If geomagnetic conditions are relevant, describe them as limited observational context with uncertain individual relevance. Do not present them as deterministic causes of the user's sleep or cognition.
```

```python
8. Be specific about mechanisms only when they are strongly supported. Do not imply personal cortisol elevation, HRV suppression, or melatonin suppression from Kp/Bz alone.
```

Mirror the same wording in `src/composables/useAI.ts`.

Update `src/stores/spaceWeather.ts` advisories:

```ts
if (score === 0) return 'Geomagnetic conditions are calm. Limited observational research suggests no special recovery adjustment is needed for most users.'
if (score === 1) return 'Quiet geomagnetic activity. Treat this as neutral background context rather than a sleep forecast.'
if (score === 2) return 'Unsettled conditions. Limited observational research has reported associations with physiology, but individual effects are uncertain.'
if (score === 3) return 'Geomagnetic storm in progress. Consider a more conservative recovery routine, but do not assume a direct personal sleep effect.'
if (score === 4) return 'Severe storm. Use this as a cue to prioritize recovery basics; research on individual sleep effects remains limited and observational.'
return 'Extreme geomagnetic storm. Prioritize recovery basics, but avoid treating the current conditions as a deterministic biological forecast.'
```

- [ ] **Step 4: Re-run the Python tests and the frontend build**

Run:

```bash
python -m pytest backend/tests/test_prompt_builder_truthfulness.py -q
npm run build
```

Expected:

- `2 passed` from the backend prompt tests
- Vite build exits `0`

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/tests/test_prompt_builder_truthfulness.py backend/chat/prompt_builder.py src/composables/useAI.ts src/stores/spaceWeather.ts
git commit -m "Harden prompt and space weather advisory evidence language"
```

---

### Task 3: Research Model Language Hardening

**Files:**
- Modify: `research/requirements.txt`
- Create: `research/tests/test_space_weather_bio.py`
- Create: `research/tests/test_language_hardening.py`
- Modify: `research/space_weather_bio.py:34-318`
- Modify: `research/caffeine_model.py:45-323`
- Modify: `research/light_model.py:45-400`
- Modify: `research/alcohol_model.py:33-417`
- Modify: `research/breathwork_model.py:68-455`
- Modify: `research/nap_model.py:107-491`

- [ ] **Step 1: Write the failing tests for explicit heuristic/evidence labeling**

Create `research/tests/test_space_weather_bio.py`:

```python
from datetime import datetime

from research.space_weather_bio import SpaceWeatherBioModel, SpaceWeatherReading


def test_kp_cognitive_advisory_uses_observational_not_deterministic_language():
    model = SpaceWeatherBioModel()
    advisory = model.kp_cognitive_advisory(6.0)

    assert advisory["evidence_level"] == "observational"
    assert "uncertain individual relevance" in advisory["advisory"]
    assert "likely" not in advisory["advisory"].lower()
    assert "expected" not in advisory["advisory"].lower()


def test_composite_disruption_is_labeled_exploratory():
    model = SpaceWeatherBioModel()
    result = model.composite_disruption(
        SpaceWeatherReading(kp_index=5.0, solar_wind_speed=650.0, bz=-12.0, timestamp=datetime(2026, 4, 5, 14, 0))
    )

    assert result["model_type"] == "exploratory_heuristic"
    assert "not validated for individual prediction" in result["advisory"]
```

Create `research/tests/test_language_hardening.py`:

```python
from datetime import datetime

from research.alcohol_model import AlcoholModel
from research.breathwork_model import BreathworkModel
from research.caffeine_model import CaffeineModel, CaffeineProfile
from research.light_model import CircadianLightModel
from research.nap_model import NapModel


def test_alcohol_sleep_impact_is_labeled_heuristic():
    result = AlcoholModel().sleep_impact(3, 4, 80.0, "male")
    assert result["model_type"] == "heuristic"
    assert "individual response varies" in result["advisory"]


def test_breathwork_response_does_not_claim_validated_personal_prediction():
    result = BreathworkModel().hrv_response("resonance", 5.5, 10, baseline_rmssd=38.0)
    assert result["model_type"] == "heuristic"
    assert "rough estimate" in result["advisory"]


def test_caffeine_cutoff_uses_default_conservative_language():
    result = CaffeineModel().optimal_cutoff(datetime(2026, 4, 5, 23, 0), CaffeineProfile(), dose_mg=200)
    assert "default conservative estimate" in result["advisory"]
    assert "guarantee" not in result["advisory"].lower()


def test_light_model_uses_risk_band_language():
    result = CircadianLightModel().melatonin_suppression(100, 2.0)
    assert result["model_type"] == "heuristic"
    assert "rough risk estimate" in result["advisory"]


def test_nap_recommendation_does_not_treat_study_results_as_universal():
    result = NapModel().recommendation(14.0, 7.0, 23.0, 7.0, sleep_debt_hours=3.0, goal="alertness")
    assert "study-specific" in result["advisory"]
    assert "universal" not in result["advisory"].lower()
```

- [ ] **Step 2: Add pytest for research and run the tests to verify they fail**

Modify `research/requirements.txt`:

```txt
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
numpy>=2.0.0
scipy>=1.14.0
pandas>=2.2.0
httpx>=0.28.0
pydantic>=2.10.0
python-dotenv>=1.0.0
pytest>=8.3.0
```

Run:

```bash
python -m pip install -r research/requirements.txt
python -m pytest research/tests/test_space_weather_bio.py research/tests/test_language_hardening.py -q
```

Expected:

- multiple failures because the current models do not expose `model_type` / `evidence_level` or hardened advisory language

- [ ] **Step 3: Implement the minimal hardening in the Python models**

Apply these patterns consistently:

In `research/space_weather_bio.py`, return observational/exploratory metadata:

```python
return {
    "impact_tier": impact_tier,
    "focus_modifier": round(focus_modifier, 2),
    "evidence_level": "observational",
    "advisory": (
        "Limited observational research has reported associations between elevated geomagnetic activity and cognition-related outcomes, "
        "but individual relevance is uncertain. Use this as exploratory context rather than a personal prediction."
    ),
}
```

```python
return {
    "bio_score": bio_score,
    "kp_norm": round(kp_norm, 3),
    "bz_norm": round(bz_norm, 3),
    "wind_norm": round(wind_norm, 3),
    "protocol_adjustments": protocol_adjustments,
    "model_type": "exploratory_heuristic",
    "advisory": "Exploratory heuristic based on space-weather context. Not validated for individual prediction.",
}
```

In `research/alcohol_model.py`, `research/breathwork_model.py`, `research/light_model.py`, and `research/nap_model.py`, add `model_type: "heuristic"` to the return dicts that drive advisory text, and rewrite those advisories to use:

```python
"This is a citation-informed heuristic. Individual response varies."
```

In `research/caffeine_model.py`, change the cutoff advisory to:

```python
advisory = (
    f"Default conservative estimate: with a {half_life:.1f}h half-life, a {dose_mg}mg dose needs "
    f"{hours_needed:.1f}h to decay to {target_remaining_mg}mg. This reduces residual caffeine burden near bedtime, "
    f"but does not guarantee safety for every dose or metabolism."
)
```

Also correct any incorrect inline comments that claim the current cutoff leaves `~1/64` of peak when the implemented math does not support that statement.

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python -m pytest research/tests/test_space_weather_bio.py research/tests/test_language_hardening.py -q
```

Expected:

- all tests pass

- [ ] **Step 5: Commit**

```bash
git add research/requirements.txt research/tests/test_space_weather_bio.py research/tests/test_language_hardening.py research/space_weather_bio.py research/caffeine_model.py research/light_model.py research/alcohol_model.py research/breathwork_model.py research/nap_model.py
git commit -m "Harden research models against deterministic overclaiming"
```

---

### Task 4: Research-Doc Alignment and Final Verification

**Files:**
- Modify: `research/RESEARCH.md`
- Modify: `research/RESEARCH_V2.md`
- Optional modify: `PRD.md`
- Optional modify: `MARKETING.md`
- Optional modify: `TECHNICAL.md`

- [ ] **Step 1: Rewrite the research-roadmap wording so evidence, heuristics, and roadmap are distinct**

Apply these exact wording patterns in `research/RESEARCH.md` and `research/RESEARCH_V2.md`:

```md
- Literature finding: published result from the cited paper
- Current implementation: citation-informed heuristic, not validated for individual prediction
- Future direction: roadmap item not yet implemented
```

Replace over-strong claims like:

```md
Based on peer-reviewed quantitative models ready to convert to code.
```

with:

```md
Based on peer-reviewed findings that can inform code, but current implementations may require heuristic simplifications and are not automatically validated for individual prediction.
```

- [ ] **Step 2: Verify the docs no longer contain the strongest contradictory phrases**

Run:

```bash
rg -n "Melatonin suppression likely|Significant biological disruption expected|ready to convert to code|validated individual|wake maintenance zone is your best focus|Social Jet Lag" research/RESEARCH.md research/RESEARCH_V2.md PRD.md MARKETING.md TECHNICAL.md
```

Expected:

- no hits for the hardened phrases in the research docs
- if root docs still hit on the exact contradictions, patch only those lines in this task

- [ ] **Step 3: Run the full verification set**

Run:

```bash
python -m pytest backend/tests/test_prompt_builder_truthfulness.py research/tests/test_space_weather_bio.py research/tests/test_language_hardening.py -q
npm run test -- src/lib/circadianTruth.test.ts
npm run build
```

Expected:

- all Python tests pass
- Vitest passes
- Vite build exits `0`

- [ ] **Step 4: Commit**

```bash
git add research/RESEARCH.md research/RESEARCH_V2.md PRD.md MARKETING.md TECHNICAL.md
git commit -m "Align research docs with heuristic evidence posture"
```

---

## Self-Review

### Spec coverage

- Peak-focus consistency is covered in Task 1.
- Social-jet-lag proxy rename is covered in Task 1.
- Caffeine wording/math cleanup is covered in Tasks 1 and 3.
- Space-weather low-certainty framing is covered in Tasks 2 and 3.
- Prompt hardening is covered in Task 2.
- Research-module heuristic labeling is covered in Task 3.
- Research-doc alignment is covered in Task 4.

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- All tasks include exact file paths and commands.
- Code-changing steps include concrete code snippets.

### Type consistency

- Frontend helper uses `Chronotype = 'early' | 'intermediate' | 'late'`, which matches the user store.
- The renamed metric is consistently `solarAlignmentGapMinutes`.
- Research-model metadata fields are consistently `model_type` and `evidence_level`.

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-08-science-consistency-and-evidence-hardening.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
