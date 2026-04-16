# HELIOS Science and Algorithm Credibility Upgrade Design

## Goal

Upgrade HELIOS from a promising science-forward prototype into a more credible consumer sleep optimizer and circadian operating system by tightening evidence claims, improving core algorithm quality, and making user-facing guidance more useful without overstating medical certainty.

This spec focuses on science and algorithm credibility first. Security hardening is intentionally deferred to the next spec.

---

## Product Positioning

HELIOS should not behave like a generic sleep app that only reports yesterday's sleep score, and it should not pretend to be a medical diagnostic system.

The target position is:

- a consumer sleep optimizer with practical, daily-use guidance
- a circadian operating system that helps users make better decisions around light, caffeine, sleep timing, travel, recovery, and selected wellness interventions

The product should feel more differentiated than commodity sleep apps because it:

- models timing, not just sleep duration
- integrates circadian, travel, and environmental context
- explains why it is making a recommendation
- shows evidence quality and uncertainty instead of flattening all outputs into "science-backed"

---

## Core Problems To Fix

### 1. Claim inflation

Some prompts, docs, and model outputs still imply more certainty than the cited literature supports. This weakens user trust and investor confidence.

### 2. Mixed evidence classes

The system currently mixes validated foundations, practical heuristics, and exploratory research in one flat layer. Users and investors cannot easily tell what is solid versus speculative.

### 3. Weak chronotype personalization

The chronotype engine is a strong foundation, but it still relies too heavily on weekday assumptions and lacks explicit confidence or instability reporting.

### 4. Heuristic calculators without explicit boundaries

Several research modules and lab tools provide precise-looking outputs from evidence that is population-level, heterogeneous, or context-dependent.

### 5. Supplement advice is not yet mature enough

The supplement layer can be useful and differentiated, but it needs clearer evidence framing, safer wellness boundaries, and more transparent personalization logic.

### 6. Investor-facing research narrative drifts from implementation

Docs, prompts, and shipped systems do not always tell the same story about what HELIOS actually does today.

---

## Design Principles

### Truth over theater

If a model is heuristic, it should say so plainly. HELIOS should still feel ambitious, but it must not use false precision to create the appearance of sophistication.

### More useful, not more medical

Recommendations should help users make better wellness decisions without drifting into diagnosis or treatment advice. When boundaries are close to medical territory, the UI should say so.

### Evidence should be visible by default

Users should not need to dig for the population studied, effect size, or main caveat. Investors should immediately see that the science layer is disciplined.

### Personalization requires confidence, not just output

Any personalized model should state how confident it is, what data it used, and when the data is too weak or unstable.

### Preserve product differentiation

The goal is not to simplify HELIOS into a generic tracker. The goal is to make its unique positioning more defensible.

---

## Evidence Architecture

HELIOS should classify each science surface into one of three evidence tiers.

### Tier A: Validated Foundations

These are models or concepts with strong support and relatively direct application:

- chronotype from sleep timing
- social jet lag
- sleep-window regularity
- light timing zones and melanopic thresholds
- basic caffeine pharmacokinetics
- simple timing-window logic

Expected behavior:

- can drive primary recommendations
- may be described as strong or established guidance
- should still note individual variation where material

### Tier B: Citation-Informed Heuristics

These are useful product models built from real literature but not individually validated predictors:

- alcohol impact estimates
- nap timing/duration recommendations
- breathwork effect sizing
- exercise timing guidance
- supplement relevance ranking
- practical jet-lag support heuristics that are not full validated physiological forecasts

Expected behavior:

- can inform user guidance
- must be labeled as heuristic or estimate
- should avoid rigid personalized promises

### Tier C: Exploratory / Observational Context

These rely on weak, observational, heterogeneous, or mechanistically incomplete evidence:

- space-weather biology
- weak cross-domain extrapolations
- any model whose literature support is not robust enough for user-level prediction

Expected behavior:

- contextual only
- never the sole basis for a strong recommendation
- always framed as uncertain and observational

### Shared Evidence Contract

Every research module, lab tool, and AI guidance surface should expose:

- `evidence_tier`
- `effect_summary`
- `population_summary`
- `main_caveat`
- `uncertainty_factors`
- `claim_boundary`

The exact copy can differ by surface, but the structure should be uniform across:

- Python research modules
- frontend calculator outputs
- supplement guidance
- AI prompts and generated recommendations

---

## Chronotype Engine Upgrade

### Current issues

The existing engine is a good MCTQ-style start, but it relies on fixed weekday assumptions and does not clearly communicate confidence or instability.

### Upgrade goals

The upgraded chronotype engine should:

- infer constrained versus unconstrained sleep more realistically
- report confidence and data sufficiency
- flag unstable or irregular schedules
- support wearable-informed refinement without requiring it
- remain understandable and auditable

### Proposed model improvements

#### 1. Better day classification

Replace default Monday-Friday assumptions with a classification system based on:

- alarm-constrained wake times when available
- sleep regularity patterns
- wake-time clustering
- user-declared work/free patterns if explicitly provided

If the engine cannot reliably distinguish constrained from unconstrained days, it should say so and reduce confidence.

#### 2. Confidence scoring

Chronotype output should include:

- estimated chronotype label
- estimated MSF / MSFsc
- confidence score
- data sufficiency state
- irregularity warning when variance is too high

Confidence should consider:

- number of nights
- presence of both constrained and unconstrained nights
- sleep timing variance
- recent schedule drift

#### 3. Wearable-informed refinement

Where supported data exists, the engine may refine chronotype using:

- sleep midpoint consistency
- resting HR rhythm proxies
- temperature timing proxies
- HRV rhythm proxies

This refinement should improve confidence or nuance, not silently override the base sleep-timing model.

#### 4. Clear failure states

The engine must be able to say:

- insufficient data
- irregular schedule
- no reliable free-day proxy
- wearable signals inconsistent with sleep timing

These are product strengths, not weaknesses, because they prevent false confidence.

---

## Module-by-Module Recalibration

Each major science model should be reviewed against primary papers and reclassified or adjusted as needed.

### Caffeine

Keep:

- half-life modeling
- residual-caffeine calculations
- timing-based bedtime burden estimates

Improve:

- cite studied population more precisely
- avoid treating trial thresholds as universal truths
- separate pharmacokinetics from sleep-impact heuristic mapping

Target state:

- Tier A for elimination math
- Tier B for personalized sleep-impact estimates

### Light

Keep:

- melanopic threshold framing
- dose-response structure

Improve:

- keep "suppression" and "sleep-onset delay" language explicitly heuristic where mapping is indirect
- preserve age/sensitivity adjustments but clearly frame them as modifiers, not exact personal calibration

Target state:

- Tier A for light-zone guidance
- Tier B for estimated suppression / delay outputs

### Alcohol

Keep:

- Widmark-based BAC estimate

Improve:

- make architecture and HRV outputs visibly heuristic
- tie stronger warnings to bedtime BAC, not only drink bins
- preserve real-world utility without pretending to forecast exact next-day biology

Target state:

- Tier A for BAC math
- Tier B for sleep and HRV impact guidance

### Breathwork

Keep:

- technique differentiation
- duration and exhale-ratio logic

Improve:

- position outputs as protocol estimates, not personal biometric predictions
- emphasize acute response and variance

Target state:

- Tier B

### Nap

Keep:

- timing windows
- duration recommendations
- NASA special-case support

Improve:

- make the timing penalty heuristic explicit
- keep guidance useful while acknowledging individual tolerance and context

Target state:

- Tier B

### Exercise timing

Keep:

- phase-direction logic
- chronotype modifiers

Improve:

- separate strong directionality from weaker exact minute estimates

Target state:

- Tier B

### Supplements

Keep:

- visible effect, caveat, and evidence framing

Improve:

- goal-driven relevance
- input-based personalization
- stronger safety and non-medical boundaries
- better contraindication handling

Target state:

- Tier B for general wellness support
- never positioned as diagnosis or treatment

### Space weather

Keep:

- contextual environmental/orbital framing

Improve:

- prevent it from driving strong biological claims
- make the observational nature impossible to miss
- reduce deterministic protocol actions that imply causal certainty

Target state:

- Tier C only

---

## Supplement Guidance Redesign

### Product goal

Create a supplement guide that feels useful and differentiated, but clearly stays within wellness support and non-diagnostic boundaries.

### Inputs

The supplement guide may use:

- explicit user goals
  - fall asleep faster
  - improve recovery
  - support stress resilience
  - handle jet lag / schedule shift
  - support circadian realignment
- user context
  - chronotype
  - travel or jet-lag state
  - bedtime consistency
- available biometrics
  - sleep duration
  - sleep score
  - HRV
  - recent instability or stress proxies

### Output structure

Each supplement recommendation should show:

- what it may help with
- why HELIOS suggested it for this user
- effect size with units
- population studied
- important caveat
- timing and dose
- evidence grade or evidence tier

### Medical boundary language

Every supplement surface should include language equivalent to:

- this is general wellness guidance, not medical advice
- if you have a medical condition, take medication, are pregnant, or are unsure, consult a clinician before using supplements

Some supplements should additionally require visible caution notes when relevant, especially around:

- sedation
- blood pressure
- thyroid effects
- medication interactions
- pregnancy / breastfeeding

### Personalization rule

Personalization should rank relevance, not claim certainty.

That means HELIOS should say:

- "this may be more relevant given your pattern of X"

rather than:

- "you need this supplement"

---

## AI Prompt and Guidance Alignment

The AI layer should consume the same evidence architecture as the models.

### Prompt requirements

Prompts should:

- distinguish Tier A, Tier B, and Tier C logic
- forbid escalation of heuristic outputs into deterministic claims
- require population and caveat framing when using research findings
- prevent the model from speaking as if all modules are equally validated

### Recommendation requirements

When the AI references a model or paper, it should preferably indicate:

- the mechanism or direction of the effect
- the population it comes from
- uncertainty when relevant

The AI should feel informed and useful, not legalistic, but the truth boundary must be hard.

---

## Investor-Facing Research Consistency

The docs and shipped product must tell the same story.

### Required cleanup

Align:

- research docs
- architecture docs
- prompts
- frontend copy
- shipped model behavior

### Specifically

Remove or correct:

- contradictions about Mem0 versus markdown memory
- claims that live backend prompt data exists when it is still placeholder
- broad statements that suggest a model is individually validated when it is not

### Investor outcome

After cleanup, an investor should be able to see:

- a genuine wedge
- a thoughtful evidence hierarchy
- a path from consumer wellness to deeper personalization
- a team that knows the difference between scientific inspiration and validated inference

---

## Deliverables

This spec should produce the following implementation workstreams:

1. evidence-tier and claim-boundary framework
2. chronotype engine upgrade
3. research module recalibration
4. supplement guide redesign with safety boundaries
5. prompt and docs alignment

Each of those will map to concrete tasks in the implementation plan.

---

## Verification Strategy

The resulting implementation should be validated with:

- targeted unit tests for core model logic
- targeted tests for confidence and invalid-data states
- prompt truthfulness tests
- documentation consistency checks where practical
- build verification

Success is not just "tests pass." Success means the system becomes:

- more helpful
- more scientifically disciplined
- more legible to diligence and investor review

---

## Out of Scope

This spec does not include:

- backend security hardening
- infrastructure or Cloudflare deployment changes
- broad visual redesign
- live medical diagnosis or treatment support
- medical-grade claims or regulatory positioning

Security is the next spec after this one.

---

## Risks and Tradeoffs

### Risk: less flashy outputs

More honest evidence framing may make some outputs look less dramatic.

Mitigation:

- keep the product confident in areas where the evidence is genuinely strong
- explain "why" better so honesty feels premium rather than timid

### Risk: chronotype upgrade becomes too research-heavy

Mitigation:

- preserve a simple primary user output
- move complexity into confidence and diagnostics, not the main card copy

### Risk: supplement layer drifts too close to medical advice

Mitigation:

- keep the domain in wellness support
- require visible disclaimers and contraindication language
- rank relevance, not need

---

## Bottom Line

HELIOS should become more credible without becoming generic.

The science layer should be explicit about what is established, what is heuristic, and what is exploratory. The chronotype engine should become more realistic and confidence-aware. The supplement guide should become more useful and more differentiated while staying safely within wellness boundaries. The docs and prompts should then be aligned so investors and users see the same truthful system.
