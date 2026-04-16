# HELIOS Research V2 — Deep Research Findings

## 10 New Python Modules to Build

Based on peer-reviewed findings that can inform code, while current implementations may still require heuristic simplifications and are not automatically validated for individual prediction.

## Evidence Language
- Tier A: strong foundations used for primary timing guidance
- Tier B: heuristic calculators built from peer-reviewed literature
- Tier C: exploratory context only, never a deterministic personal forecast

## Current Implementation Boundary
- These modules describe research-backed directions, not blanket claims that every model is already shipped.
- Chronotype, light timing, caffeine timing, and protocol generation are the strongest current foundations.
- Alcohol, nap, breathwork, supplement, meal-timing, and exercise-timing outputs should be framed as heuristic decision support.
- Space-weather biological context remains exploratory and should stay non-deterministic in user-facing copy.

### Module 1: `alcohol_model.py` (Priority: HIGH — simplest math, high user demand)
- **Pietilä et al. (2018, JMIR, n=4,098 nights)**: 1-2 drinks = -9.3% HRV, 3-4 = -24%, 5+ = -39.2%
- **BAC pharmacokinetics**: `BAC(t) = (drinks × 14g) / (weight_kg × 0.68m/0.55f × 10) - 0.015 × hours`
- **Function**: `alcohol_sleep_impact(drinks, hours_before_bed, weight_kg, sex) → BAC, HRV %, REM loss, cutoff time`

### Module 2: `breathwork_model.py` (Priority: HIGH — clean dose-response)
- **Laborde et al. (2022, Neuroscience & Biobehavioral Reviews, meta-analysis)**: Resonance breathing (5.5 bpm) = +20-50ms rMSSD during, +8-15ms residual for 1-4h
- **Dose-response**: 5min = +15%, 10min = +25%, 20min = +35% (diminishing returns)
- **Optimal inhale:exhale ratio**: 1:2 yields +40% vs 1:1 at +25% (Van Diest 2014)
- **Function**: `breathwork_hrv_response(technique, breaths_per_min, duration_min) → rMSSD during/post, LF/HF ratio`

### Module 3: `nap_model.py` (Priority: HIGH — well-characterized)
- **NASA nap study (Rosekind 1995)**: 26-min nap = +54% alertness, +34% performance in pilots
- **Duration dose-response (Dutheil 2021, meta-analysis)**: 10min = 155min alertness, 20min = 185min, 26min = 3h, 90min = 8h+
- **Timing**: optimal 1-3 PM, after 3 PM each hour later = -3-5% night sleep efficiency
- **Function**: `nap_recommendation(current_time, wake_time, sleep_debt, goal) → should_nap, duration, alertness_boost`

### Module 4: `meal_timing_model.py` (Priority: MEDIUM)
- **Sutton et al. (2018, Cell Metabolism)**: Early TRF (8AM-2PM) = +36% insulin sensitivity, -11/10 mmHg BP, -30% oxidative stress
- **Manoogian et al. (2022, Endocrine Reviews)**: ≤10h window = +10-15% glucose tolerance; last meal ≥3h before sleep = +5-8% sleep efficiency
- **Wehrens et al. (2017, Current Biology)**: 5h meal delay → peripheral clock delay 0.5-1.5h (central clock unchanged)
- **Function**: `meal_timing_circadian_score(first_meal, last_meal, wake, sleep) → eating_window, clock_alignment, glucose_clearance`

### Module 5: `exercise_timing_model.py` (Priority: MEDIUM)
- **Youngstedt et al. (2019, J Physiology)**: FIRST human exercise PRC — 7AM/1-4PM = 30-90min advance, 7-10PM = 30-60min delay
- **Thomas et al. (2020, JCI Insight)**: Chronotype matters — morning exercise advances late types 50-80min but early types only 10-20min
- **Sato et al. (2019, Cell Metabolism)**: Morning exercise = +2-3x clock gene expression, +20% insulin sensitivity
- **Function**: `exercise_circadian_effect(time, duration, intensity, chronotype) → phase_shift, metabolic_benefit`

### Module 6: `supplement_model.py` (Priority: MEDIUM)
- **Mah 2021 (BMC, meta-analysis)**: Mg glycinate 225-500mg = -17.36min latency, +16.06min TST
  - **CAVEAT**: Studies mostly in elderly insomniacs. Effect in healthy young adults likely MUCH smaller. Supplement blinding is inherently weak.
- **Fatemeh 2022 (J Neurology, k=23 RCTs)**: Melatonin 0.5-1mg = -7.06min latency (0.5mg > 5mg due to receptor desensitization)
  - Effect size is modest (7 min). Most useful for circadian misalignment, not general insomnia.
- **Bannai 2012**: 3g glycine before bed = -0.1-0.2°C core temp, -10min latency
- **FRAMING**: Always present as "may help, evidence strongest in older adults or those with deficiency." Never claim supplements fix sleep problems. The timing/light/caffeine protocols have much stronger evidence.
- **Function**: `supplement_sleep_effect(supplement, dose, timing, days_of_use) → latency_reduction, TST_gain, optimal_dose, evidence_quality`

### Module 7: `cold_exposure_model.py` (Priority: MEDIUM)
- **Espeland 2022 (Int J Circumpolar Health)**: 10-15°C for 1-3min = +200-300% norepinephrine, +250% dopamine
  - **CAVEAT**: These numbers are from ice bath protocols, not cold showers. Cold shower response is lower and highly individual. Some people get no parasympathetic rebound at all.
- **Post-cold HRV rebound**: rMSSD +15-30% within 30-60 min — **wide range, highly variable between individuals**
- **Morning cold amplifies cortisol awakening response by ~30%**
- **FRAMING**: Present ranges not point estimates. "You may experience..." not "You will experience..." Individual response varies 2-5x.
- **Function**: `cold_exposure_hrv_response(water_temp, duration, time_since_waking) → NE fold_range, rMSSD delta_range`

### Module 8: `hrv_sleep_model.py` (Priority: MEDIUM)
- **Faust et al. (2020, npj Digital Medicine)**: Each 30min bedtime deviation = -4-5ms rMSSD, +1.5 bpm RHR
- **Windred et al. (2024, Sleep)**: Sleep Regularity Index — each 10-point SRI decrease = +8% all-cause mortality
- **Function**: `hrv_sleep_timing_penalty(actual_bedtime, habitual_bedtime) → predicted_rMSSD, quality_score`

### Module 9: `screen_time_model.py` (Priority: LOW — extends existing light_model.py)
- **Chinoy et al. (2018, PNAS)**: 2h tablet = -55% melatonin, -1.5h onset delay, -12min REM, -8h next-day alertness
- **Cajochen 2011**: 5h LED screen = SWA power -12%, cortisol delay 30-45min
- **Green 2017**: 2h full-spectrum screen = +28min latency, -31% total melatonin, +14% attention lapses next day
- **Function**: `screen_time_circadian_impact(duration, device, night_mode, blue_blockers) → full impact profile`

### Module 10: `light_exposure_model.py` (Priority: LOW — extends existing light_model.py)
- **Burns et al. (2021, J Affective Disorders, n=400,000 UK Biobank)**: Each 30min outdoor light = +0.7% sleep efficiency, -4min onset latency
- **Stothard 2017 (Current Biology)**: Weekend camping (natural light) = -1.4h melatonin onset advance, -30min latency
- **Gladwell 2012**: 20min outdoor nature = +15-25% HF-HRV (parasympathetic)
- **Function**: `light_exposure_hrv_benefit(lux, duration, time_of_day, is_outdoor) → HRV delta, phase shift, alignment score`

---

## Disruptive Technologies to Integrate

### Tier 1: Build Now (Investor Demo-Ready)

**1. ~~Digital Phenotyping — REJECTED~~**
- Source: npj Digital Medicine, Dec 2025 (Nature)
- BiAffect keyboard: typing dynamics predict circadian phase
- **Why we rejected it:** Signal too indirect (proxy of a proxy), easily faked, and "app monitors your keystrokes" is a privacy nightmare. Direct physiological measurement (HRV, skin temp, sleep stages) from existing wearables is superior in every way. We evaluated it and made a scientific judgment call to pass.

**2. NASA Countermeasure Protocols for Civilians**
- Source: Life Sciences in Space Research, June 2025
- Astronaut light protocol, scheduled darkness, pink noise
- **Investor line:** *"Same circadian countermeasures NASA uses for ISS crew."*

**3. Heat Protocol Card**
- Source: Meta-analysis (n=5,322), 2019
- Warm shower/sauna 1-2h before bed: sleep onset latency -36%, SWS +10%

### Tier 2: Build Partnerships (3-6 months)

**4. CGM + Circadian = Metabolic Chronotyping**
- Dexcom REST API (FDA-cleared), Thryve unified CGM API
- Overlay glucose curves on circadian phase
- **Investor line:** *"We overlay your blood glucose on your circadian clock."*

**5. TimeTeller Molecular Clock Profiling**
- Saliva-based clock gene expression analysis
- Commercializing in Germany, at-home kits available
- **Investor line:** *"We're the dashboard for molecular circadian medicine."*

**6. tDCS Timing Optimization**
- Brain stimulation effectiveness is circadian-dependent (MDPI 2025)
- HELIOS tells tDCS users WHEN to stimulate

### Tier 3: Moonshots

**7. Circadian Digital Twin** (Med-Real2Sim, NeurIPS 2024)
- Simulate "what if you shifted your wake time?" before doing it

### Do NOT Build
- Polyphasic sleep (abolishes 95% growth hormone — Uberman scientifically discredited)
- Psychedelic microdosing (legal risk, insufficient evidence)

---

## New Open Source Libraries

### Top Priority Integrations

| Library | License | Stars | Capability | Demo Potential |
|---|---|---|---|---|
| **Open Wearables** | MIT | 1000+ | Unified API for 200+ devices, MCP Server | 5/5 |
| **Arcascope `circadian`** | MIT | ~6 | Kronauer-Jewett circadian ODE model | 5/5 |
| **YASA** | BSD | — | Sleep staging 86.6% accuracy (eLife) | 5/5 |
| **OpenHRV** | — | 156 | Real-time HRV biofeedback + breathing pacer | 5/5 |
| **StudyU** | Open | — | N-of-1 trial platform | 5/5 |
| **Glucose360** | — | — | Stanford CGM event-based analysis | 5/5 |
| **circStudio** | — | — | Unified actigraphy + circadian analysis (March 2026) | 4/5 |
| **BioSPPy** | BSD | 632 | Medical-grade biosignal processing | 4/5 |
| **Med-Real2Sim** | CC BY 4.0 | — | Physiological digital twin (NeurIPS 2024) | 5/5 |

### Smart Home Integration
- **Philips Hue** via `hueautotemp`: push circadian color temps to smart bulbs
- **Awair/Aranet4**: indoor CO2 + VOC monitoring (CO2 >1000ppm impairs cognition)

---

## The Investor Narrative

HELIOS is best described today as a consumer sleep optimizer plus circadian operating system. The strongest shipped surfaces are chronotype inference from sleep timing, light timing guidance, caffeine timing, protocol generation, and increasingly explicit evidence labeling. Hermes adds a markdown-memory personalization layer, but the system is still a pragmatic consumer product, not a clinical-grade digital twin.

What is strong today:
- chronotype from sleep timing and schedule regularity
- circadian light and timing guidance
- caffeine timing and bedtime burden estimation
- live location, solar, environmental, and space-weather context

What is heuristic today:
- alcohol, nap, breathwork, supplement, meal-timing, and exercise-timing tools
- wearable-informed refinement beyond baseline sleep timing
- investor-demo modules that still simplify heterogeneous literature

What is exploratory today:
- space-weather biology
- any roadmap feature that depends on N-of-1 trials, CGM integration, or molecular clock profiling

Roadmap narrative, not shipped fact:
- broader wearable ingestion through unified connectors
- deeper circadian simulation via Kronauer-style models
- structured N-of-1 experimentation
- HRV biofeedback and metabolic chronotyping
- a long-term circadian digital twin

Five investor lines that stay honest:
1. "HELIOS is a consumer sleep optimizer evolving into a circadian operating system."
2. "We work with user-owned wearables and uploaded data instead of requiring proprietary hardware first."
3. "Our strongest product surfaces are chronotype, light, caffeine, travel, and schedule timing."
4. "We separate validated foundations, heuristics, and exploratory context instead of flattening everything into fake certainty."
5. "The long-term moat is personalized circadian decision support built on user data, evidence tiers, and better validation over time."
