# HELIOS Research Roadmap

## Overview
This document tracks peer-reviewed papers, open source libraries, data sources, and architecture decisions for the HELIOS circadian intelligence engine. Everything here is backed by citations and intended to be converted into Python algorithms.

---

## Tier 1 — Implement Now (uses existing data streams)

### Light Zone Assessment
- **Paper**: Brown et al. (2022, PLOS Biology 20:e3001571)
- **Finding**: Daytime >=250 melanopic EDI lux, evening (3h pre-bed) <=10, sleep <=1
- **Function**: `light_zone_assessment(melanopic_edi, hours_to_sleep) -> dict`

### Melatonin Suppression Prediction
- **Paper**: Gimenez et al. (2022, J Pineal Research 72:e12786)
- **Finding**: 4-param logistic model. ED50: 0.5h=600lux, 1h=350lux, 2h=120lux, 3h=43lux, 4h=15lux
- **Function**: `predict_melatonin_suppression(melanopic_edi, duration_hours) -> float`

### Kp-HRV Impact Scoring
- **Paper**: Alabdali et al. (2022, Sci Total Environ 838:156067)
- **Finding**: 75th-percentile Kp increase = -14.7ms rMSSD, -8.2ms SDNN (n=809)
- **Function**: `kp_hrv_impact(kp_index, baseline_rmssd, baseline_sdnn) -> dict`

### Kp-Melatonin Disruption
- **Paper**: Burch et al. (2008, Neuroscience Letters 438:76-79)
- **Finding**: Elevated Kp reduces melatonin metabolite excretion, 15-33h lag window
- **Function**: `kp_melatonin_modifier(kp_history_33h) -> float`

### Kp-Cognitive Advisory
- **Paper**: Alabdali et al. (2024, Environ Int 185:108526)
- **Finding**: Elevated Kp reduces cognitive performance in 0-24h window
- **Function**: `kp_cognitive_advisory(kp_current) -> str`

### Caffeine Pharmacokinetics (Personalized)
- **Paper**: Chinoy et al. (2024, SLEEP 48:zsae230)
- **Finding**: 400mg at 12h pre-bed still disrupts sleep. 100mg = no effect at any timing
- **Paper**: Nehlig et al. (2022, Front Pharmacol 12:752826)
- **Finding**: CYP1A2 fast=3h, slow=7h+. Smoking halves, OC doubles half-life
- **Function**: `personalized_caffeine_halflife(genotype, smoker, oral_contraceptive) -> float`
- **Function**: `caffeine_sleep_impact(dose_mg, hours_before_bed, half_life_h) -> dict`

### Screen/Blue Light Impact
- **Paper**: West et al. (2011, J Appl Physiol 110:619-626) — Blue LED dose-response: ED50=14.19 uW/cm2
- **Paper**: Spitschan et al. (2023, Commun Biol 6:228) — 2h tablet = 55% melatonin decrease
- **Paper**: Mouland et al. (2025, Sci Reports 15:29882) — Cool white LED: 12.3% suppression, warm: 3.6%
- **Paper**: Nagare et al. (2019, J Biol Rhythms 34:178-189) — Adolescents 1.5x more sensitive than adults
- **Function**: `screen_melatonin_impact(melanopic_edi, duration_hours, hours_before_bed) -> dict`
- **Function**: `age_adjusted_light_sensitivity(age, melanopic_edi, duration_h) -> float`

---

## Tier 2 — Wearable Integration (requires Garmin/Oura/Apple Watch data)

### Circadian Phase from HR
- **Paper**: Woelders et al. (2023, J R Soc Interface 20:20230030)
- **Finding**: Cosinor of continuous HR extracts circadian acrophase in 3-7 days
- **Function**: `circadian_acrophase_from_hr(hr_series_7d) -> dict`

### DLMO Prediction from Wearables
- **Paper**: Huang et al. (2021, SLEEP 44:zsab126)
- **Finding**: Predict DLMO within ~1h from activity data alone
- **Function**: `predict_dlmo_from_activity(activity_data_7d) -> datetime`

### Wrist Temperature Chronotyping
- **Paper**: Martinez-Nicolas et al. (2019, Front Physiol 10:1396)
- **Finding**: Wrist temp acrophase is most robust parameter for chronotype
- **Function**: `chronotype_from_wrist_temp(temp_series_7d) -> dict`

### Multi-Signal Chronotype Fusion
- **Paper**: Kolbe et al. (2024, arXiv:2404.03408)
- **Finding**: HR + temp + activity fusion outperforms any single modality
- **Function**: `multi_signal_chronotype(hr_acrophase, temp_acrophase, activity_acrophase) -> dict`

### Sleep Readiness from Temperature
- **Paper**: Cuesta et al. (2017, J Biol Rhythms 32:257-273)
- **Finding**: Wrist temp gradient rise >0.5C predicts sleep onset within 30 min
- **Function**: `predict_sleep_readiness(wrist_temp, finger_temp=None) -> dict`

### Oura Ring HRV Validation
- **Paper**: Zambotti et al. (2022, JMIR 24:e35528)
- **Finding**: Oura Gen 3 RMSSD CCC=0.97 vs ECG, Gen 4 CCC=0.99
- **Function**: `normalize_wearable_hrv(rmssd, device) -> float`

### Circadian Function Index
- **Paper**: Martinez-Nicolas et al. (2018, Sci Reports 8:15027)
- **Finding**: IS + IV + RA from temperature predict biological aging
- **Function**: `circadian_function_index(temp_series_7d, age) -> dict`

---

## Tier 3 — Advanced Models (research-grade features)

### Circadian ODE Simulation
- **Paper**: Kronauer et al. (1999, J Biol Rhythms 14:500-515) — Process L + Process P
- **Paper**: Hannay et al. (2019, J Biol Rhythms 34:658-671) — Simplified macroscopic model
- **Paper**: Tekieh et al. (2022, Front Neurosci 16:965525) — Improved accuracy
- **Library**: `circadian` by Arcascope (MIT license) — already implements these models
- **Function**: `class KronauerModel` or use Arcascope's `circadian` package directly

### Jet Lag Re-entrainment Scheduler
- **Paper**: Serkh & Forger (2014, PLOS Comput Biol 10:e1003523) — Optimal light schedules
- **Paper**: Dean et al. (2009, PLOS Comput Biol 5:e1000418) — Model-based schedule design
- **Paper**: Aleixo et al. (2025, J Biol Rhythms 40:36-61) — East-west asymmetry: eastward ~1.5x slower
- **Function**: `optimal_reentrain_schedule(current_cbtmin, target_cbtmin, available_lux) -> list`
- **Function**: `jet_lag_schedule(origin_tz, dest_tz, travel_date, tau=24.2) -> JetLagPlan`

### Particle Filter DLMO Estimation
- **Paper**: Weed et al. (2026, J Biol Rhythms 41) — State-of-the-art phase tracking
- **Function**: `particle_filter_dlmo(actigraphy, light, prior_dlmo) -> tuple[datetime, float]`

### Dynamic Lighting Schedules
- **Paper**: Brainard et al. (2022, J Pineal Research 73:e12805)
- **Finding**: 704 melanopic EDI = 3.28h advance, delay shifts more successful
- **Function**: `generate_lighting_schedule(target_shift_hours, direction) -> list`

---

## Open Source Libraries

### Tier 1 — Integrate Now (MIT/BSD)
| Package | License | Purpose |
|---|---|---|
| `circadian` (Arcascope) | MIT | Kronauer-Jewett model, PRC, light schedule simulation |
| `neurokit2` | MIT | 124 HRV metrics, PPG processing, sleep physiology |
| `pvlib-python` | BSD | Solar irradiance, atmospheric modeling (upgrade from SunCalc) |
| `garminconnect` | MIT | Garmin Connect API (sleep, HRV, stress) |
| `oura-ring` | MIT | Oura API v2 (sleep, temperature, readiness) |

### Tier 2 — Study & Reimplement (GPL)
| Package | License | Port What |
|---|---|---|
| `pyActigraphy` | GPL-3.0 | Cosinor, IS/IV/L5/M10, rest-activity rhythm variables |
| `CosinorPy` | GPL-3.0 | Multi-component cosinor models |
| `luxpy` | GPL-3.0 | CIE S 026 melanopic EDI calculation (~50 lines of math) |

### Tier 3 — Future
| Package | License | Purpose |
|---|---|---|
| `asleep` (OxWearables) | Academic | ML sleep staging from accelerometer |
| `Predstorm` | MIT | Kp forecasting from L1 data |
| `skyfield` | MIT | Precise twilight calculations |

---

## Data Sources to Add

### Priority 1 — Easy, High Impact
| Source | Auth | What It Gives Us |
|---|---|---|
| NASA POWER API | None | Surface solar irradiance, AOD, cloud-adjusted UV → "Circadian Light Dose" |
| Open-Meteo Air Quality | None | Replaces AQICN (no key needed!) + adds pollen data (6 types) |
| SunCalc moonlight/photoperiod | N/A | Moon phase, photoperiod, twilight decomposition — client-side, zero API calls |
| NOAA 3-day storm forecast | None | MinorProb/MajorProb already in JSON, just not consumed yet |

### Priority 2 — Easy, Medium Impact
| Source | Auth | What It Gives Us |
|---|---|---|
| NOAA solar proton events | None | Radiation dose advisory for air travelers |
| NOAA solar cycle position | None | "Solar Cycle 25 is at maximum" contextual card |
| DSCOVR L1 7-day trend | None | 30-60 min advance warning before geomagnetic storms hit |

### Priority 3 — Medium Effort
| Source | Auth | What It Gives Us |
|---|---|---|
| EPA AirNow (US) | Free key | Higher-resolution US AQI + next-day forecast |
| Copernicus CAMS (via Open-Meteo) | None | Global PM2.5/O3/NO2 forecasts |
| TimeZoneDB / GeoNames | Free key | Auto-resolve destination timezone for jet lag planner |

---

## Agent Architecture — Learning from User Data

### Recommended Stack
```
Vue 3 Frontend (existing useAI.ts)
    |
FastAPI Backend (feature/fastapi-backend)
    ├── Mem0 (memory: semantic + episodic + procedural)
    ├── LanceDB (local vector store, zero-ops)
    ├── ChronotypeEngine (existing)
    └── ProtocolScorer (existing)
```

### Why Mem0 + LanceDB
- Mem0: 48K stars, purpose-built memory layer, local-first with FastEmbed
- LanceDB: Zero-ops, Rust-based, versioned data for tracking patterns over time
- Plugs into existing multi-provider AI without replacing anything
- Privacy-first: all data stays on device, user's own API key for LLM calls

### Rejected Alternatives
| Framework | Why Not |
|---|---|
| Hermes Agent | Too general-purpose, would strip 80% |
| Letta (MemGPT) | Replaces entire AI layer, too big a commitment now |
| LangGraph | Overkill orchestration for a memory + scoring problem |
| CrewAI | Multi-agent = wrong paradigm, adds latency and cost |
| AutoGen | Maintenance mode, Microsoft pivoted to Semantic Kernel |

### The Learning Loop
1. User follows protocol → reports sleep quality → ProtocolScorer scores the day
2. Mem0 stores episodic memory ("protocol score 0.72, user slept 30min late")
3. After 7 days → ChronotypeEngine updates chronotype assessment
4. Before next protocol → FastAPI queries Mem0 for patterns → enriches system prompt
5. Protocol becomes personalized over time

---

## Quick Reference: Existing vs. Planned Python Modules

### Already Built (`research/chronotype_engine.py`)
- `ChronotypeEngine` — MCTQ (MSF, MSFsc, SJL)
- `ProtocolScorer` — Protocol effectiveness scoring
- `CircadianPhaseEstimator` — CBTmin and DLMO estimation

### To Build Next
- `caffeine_model.py` — Personalized pharmacokinetics (CYP1A2, ADORA2A)
- `light_model.py` — Melanopic EDI zones, melatonin suppression prediction
- `space_weather_bio.py` — Kp → HRV impact, melatonin modifier, cognitive advisory
- `wearable_pipeline.py` — Garmin/Oura data ingestion, cosinor phase extraction
- `jetlag_optimizer.py` — Kronauer model, optimal light schedules, asymmetry correction
