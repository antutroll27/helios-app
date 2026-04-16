# Science Consistency and Evidence Hardening Design

Date: 2026-04-08
Project: HELIOS
Status: Approved for planning

## Goal

Harden HELIOS against pseudo-scientific overreach without abandoning the product direction.

This pass focuses on two things only:

1. Internal scientific consistency
2. Weak-evidence claim hardening

The core product ambition remains intact:

- HELIOS should continue using public NASA and NOAA space-weather data where actually integrated.
- HELIOS should continue moving toward optimization based on user sleep, HRV, and wearable data.
- HELIOS should continue building quantitative research modules.

What changes in this pass is the truthfulness standard for present-tense claims and model outputs.

## Non-Goals

This pass does not cover:

- General marketing cleanup unrelated to scientific consistency
- Broad brand wording changes except where wording encodes a scientific contradiction
- New external integrations
- A full re-architecture of the jet-lag or research systems
- A full literature review for every module in the repo

## Design Principles

### 1. Preserve the roadmap, harden the present tense

The code and docs may continue to describe HELIOS as moving toward a system that combines:

- public NASA and NOAA data
- solar timing
- user sleep timing
- HRV and wearable biomarkers

But current code must not present heuristic outputs as if they are already validated individualized predictors.

### 2. Separate heuristics from validated models

If a module is built from simplified thresholds, interpolation, or engineering assumptions layered onto published results, it must be labeled as:

- heuristic
- citation-informed
- exploratory

It must not be described as:

- personalized prediction
- expected individual effect
- validated physiologic forecast

unless the implementation and evidence actually support that claim.

### 3. Observational geomagnetic evidence must stay observational

Geomagnetic-biology outputs must consistently use associative framing.

Allowed framing:

- limited observational research has reported associations
- uncertain individual relevance
- exploratory heuristic
- emerging or preliminary research

Disallowed framing:

- likely melatonin suppression
- expected HRV suppression
- significant biological disruption expected
- elevated cortisol due to current storm
- exact individual decrement forecasts from Kp alone

### 4. Chronobiology language must match actual computation

If the UI or prompts say a timing is chronotype-adjusted, the timing computation must actually use chronotype.

If the app uses a proxy metric, it must be named as a proxy rather than as a standard scientific construct.

## Scope

### Primary code paths

- `src/stores/protocol.ts`
- `src/stores/jetlag.ts`
- `src/stores/spaceWeather.ts`
- `src/composables/useAI.ts`
- `backend/chat/prompt_builder.py`
- `research/space_weather_bio.py`
- `research/caffeine_model.py`
- `research/light_model.py`
- `research/alcohol_model.py`
- `research/breathwork_model.py`
- `research/nap_model.py`

### Primary documentation

- `research/RESEARCH.md`
- `research/RESEARCH_V2.md`

### Secondary documentation if needed for consistency

- `PRD.md`
- `MARKETING.md`
- `TECHNICAL.md`

Secondary docs should only be touched where they directly repeat the same scientific contradictions or overclaims being fixed in code.

## Change Set

## A. Protocol Consistency

### A1. Peak focus window

Current issue:

- `protocol.ts` computes peak focus as a universal pre-sleep window.
- Prompt text explicitly says not to describe peak cognition that way.

Required change:

- Replace the current pre-sleep peak-focus calculation with a chronotype-based deep-work window.
- The exact window may remain heuristic, but it must actually depend on `user.chronotype`.

Required framing:

- The UI should describe this as a recommended deep-work window.
- The pre-sleep wake-maintenance zone should be treated as a separate alertness phenomenon, not the default "best focus" slot.

### A2. Social jet lag naming

Current issue:

- The frontend metric currently labeled as social jet lag is actually a solar-midnight misalignment estimate.
- The research engine uses the standard workday/free-day definition.

Required change:

- Rename the frontend metric to something like solar alignment gap or circadian alignment gap unless the implementation is changed to the standard social-jet-lag definition.
- Copy and subtitles must stop implying that this proxy is canonical social jet lag.

### A3. Melatonin timing terms

Current issue:

- `protocol.ts` treats melatonin onset as 90 minutes before sleep.
- Other code and research files imply earlier DLMO-like timing.

Required change:

- Stop equating wind-down start with true physiologic melatonin onset.
- Use softer wording such as estimated pre-sleep wind-down anchor.
- Avoid precise physiologic naming unless the implementation actually estimates that construct.

### A4. Caffeine wording and math

Current issue:

- Current comments and subtitles mix phase delay and melatonin suppression.
- At least one inline residual-caffeine statement is mathematically wrong.
- The protocol store uses a fixed half-life while research code supports personalization.

Required change:

- Fix incorrect half-life math in comments and explanatory text.
- Remove wording that implies the cutoff guarantees safety.
- Use wording like default conservative cutoff for a typical adult.
- Distinguish clearly between:
  - likely residual caffeine burden
  - possible sleep disruption
  - possible circadian phase delay
- Do not describe caffeine as blocking or suppressing melatonin in the same way as light.

## B. Weak-Evidence Hardening

### B1. Space weather store

Current issue:

- `spaceWeather.ts` currently presents deterministic biological advisories.

Required change:

- Rewrite advisories to observational, low-certainty framing.
- Remove deterministic statements about disrupted sleep, elevated cortisol, or biological stress risk.
- Keep the store useful as a context signal, but frame it as a possible recovery-priority day rather than a biologically predicted event.

### B2. Space weather biology model

Current issue:

- `space_weather_bio.py` converts population-level observational findings into exact personal deltas and behavior changes.

Required change:

- Remove or soften exact individual HRV and cognition predictions where they are not justified.
- Keep evidence-level labeling and explanatory notes.
- Preserve the model as exploratory if needed, but make that explicit in docstrings, return fields, and advisory text.

Specific outputs to harden:

- exact per-Kp HRV change claims
- exact cognitive impairment modifiers
- deterministic composite bio-score interpretations
- storm-triggered protocol prescriptions presented as evidence-backed

### B3. V2 research modules

Current issue:

- Alcohol, breathwork, nap, and parts of light modeling read as validated personalized predictors even where the implementation is heuristic.

Required change:

- Reframe these modules as citation-informed heuristic models where appropriate.
- Replace deterministic advisory wording with ranges, uncertainty, and conditional language.
- Remove claims that imply precise individualized prediction from sparse inputs.

Module-specific intent:

- `alcohol_model.py`: retain BAC math, downgrade sleep/recovery outputs to heuristic risk estimates
- `breathwork_model.py`: retain technique guidance, downgrade exact HRV and LF/HF claims
- `nap_model.py`: retain duration categories, downgrade deterministic performance/stage outcomes
- `light_model.py`: retain dose-response directionality, downgrade exact onset-delay and sufficiency claims where unsupported

### B4. Prompt hardening

Current issue:

- The prompts include cautionary wording but still instruct the model to produce specific mechanistic space-weather explanations as if they were established for the individual user.

Required change:

- Update prompt instructions so the model can mention geomagnetic research only as limited observational evidence with uncertain individual relevance.
- Remove prompt pressure that forces personalized causal narratives from Kp/Bz alone.

## C. Documentation Alignment

### C1. Research docs

Required change:

- `research/RESEARCH.md` and `research/RESEARCH_V2.md` should explicitly distinguish:
  - literature findings
  - implementation heuristics
  - aspirational future modules

Required language direction:

- "citation-informed"
- "heuristic implementation"
- "not yet validated for individual prediction"

Avoid:

- "ready to convert to code" when the eventual implementation clearly requires simplifications
- investor-style certainty inside research-roadmap docs

### C2. Secondary docs

If root docs are touched, changes should be surgical:

- fix contradictory peak-focus language
- soften deterministic geomagnetic-biology claims
- avoid absolute scientific claims that current code cannot support

## Output Standard After This Pass

After the pass:

- HELIOS may still surface space-weather context, but as exploratory context rather than deterministic biology.
- HELIOS may still recommend timing windows, but only where the names match the actual logic.
- HELIOS may still use research-derived heuristics, but they must be labeled honestly.
- HELIOS may still pursue a future in which user HRV, sleep logs, and NASA/NOAA data jointly optimize daily life.

This pass is specifically about making the current implementation worthy of that future.

## Testing and Verification

### Python

Add or update focused tests for touched research helpers where practical, especially around:

- wording-sensitive return structures
- evidence-level labeling
- renamed or reframed outputs
- corrected caffeine comment/math assumptions where testable

### Frontend / prompt

Verify:

- peak-focus output uses chronotype-dependent logic
- renamed alignment metric no longer claims to be social jet lag unless it truly is
- space-weather advisories no longer make deterministic biological claims
- prompt text no longer instructs causal overclaiming

### Build

Run:

- `npm run build` in `helios-app`

Run targeted Python verification for touched modules if no formal suite exists.

## Risks

### 1. Product may feel less magical

Mitigation:

- Keep useful recommendations and strong UX.
- Remove false precision, not all interpretive value.

### 2. Docs may drift again

Mitigation:

- Make the research docs explicitly distinguish evidence, heuristics, and roadmap.

### 3. Some outputs may become less concrete

Mitigation:

- Prefer bounded, honest risk language over pseudo-precision.

## Recommended Implementation Order

1. Prompt and protocol consistency
2. Space-weather user-facing advisory hardening
3. Research model wording and return-shape hardening
4. Research-doc alignment
5. Secondary-doc surgical cleanup
6. Verification

## Acceptance Criteria

- No user-facing or prompt-facing code claims deterministic geomagnetic biological outcomes from current conditions alone.
- Peak-focus logic and wording are consistent across protocol, prompt, and docs.
- The current frontend "social jet lag" metric is either renamed or brought into alignment with the standard definition.
- Caffeine wording no longer mixes suppression, phase delay, and mathematically incorrect residue claims.
- V2 research modules no longer present heuristic outputs as validated individualized predictors.
- Research docs clearly separate evidence, heuristics, and roadmap.
