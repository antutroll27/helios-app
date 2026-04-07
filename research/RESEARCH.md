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

### Full Stack
```
Vue 3 Frontend (useAI.ts)
    │ POST /api/chat/send
    ▼
FastAPI Backend
    ├── Supabase (auth, user DB, chat logs, wearable data, protocol logs)
    ├── Hermes Learner (per-user markdown memory, uses user's own LLM key)
    ├── LLM Proxy (BYOK + shared key fallback for free tier users)
    ├── Wearable Parsers (file-upload adapters per platform)
    ├── ChronotypeEngine (existing)
    ├── CaffeineModel (existing)
    ├── SpaceWeatherBioModel (existing)
    ├── CircadianLightModel (existing)
    └── ProtocolScorer (existing)
```

### How It Works
- **Hermes as per-user background learner** — runs after each chat session ends using the user's own LLM API key. Analyzes the conversation, extracts circadian insights, updates structured markdown memory file. Zero extra API costs.
- **Markdown memory files in Postgres** — each user has one `user_memories` row containing structured markdown (categories: sleep, caffeine, light, adherence, biometrics, lifestyle, preferences). No Mem0, no pgvector, no vector embeddings. Plain text, queryable, GDPR-deletable.
- **System prompt injection** — before each LLM call, the user's memory.md is formatted and injected as `[USER PROFILE FROM MEMORY]` alongside the scientific knowledge base.
- **Shared key for free tier** — users without their own API key get a rate-limited shared model (Kimi/DeepInfra, 20 msgs/day). Hermes still learns from these sessions.
- **Supabase for structured data** — raw chat logs, wearable imports, sleep logs, protocol adherence. Queryable SQL for analytics and investor demos.
- **System prompt injection** — before each LLM call, FastAPI queries Mem0 for top 5-10 relevant memories, formats them as a `[USER PROFILE]` section in the system prompt alongside the existing scientific knowledge base.

### Supabase Schema
```
users              → auth, profile, LLM API keys (encrypted)
chat_sessions      → full conversation logs (raw)
chat_messages      → individual messages with role/content/timestamp
memories           → Mem0 distilled insights (semantic/episodic/procedural)
sleep_logs         → nightly sleep data (maps to SleepLog dataclass)
data_imports       → uploaded wearable files (source, date range, status)
wearable_tokens    → OAuth tokens for future live sync (encrypted)
protocol_logs      → daily protocol + adherence (maps to ProtocolLog)
caffeine_logs      → intake tracking for CaffeineModel
biometric_logs     → HR, HRV (rMSSD/SDNN), skin temp, respiratory rate, SpO2
```

### The Learning Loop
1. User chats → LLM responds with Mem0-enriched context
2. Session ends → Hermes processes conversation, extracts learnings
3. Mem0 stores distilled insights (not raw chat — compact and searchable)
4. User uploads wearable data → parsers extract SleepLog + biometric entries
5. ChronotypeEngine reassesses chronotype from accumulated sleep logs
6. ProtocolScorer correlates protocol adherence with sleep outcomes
7. Next session → richer context → better personalized advice

### Wearable Data Import (No OAuth Required)

Users export their own data and upload to HELIOS. No API partnerships needed for v1.

| Platform | Format | Parser | Key Biometrics |
|---|---|---|---|
| Oura Ring | JSON | stdlib `json` | Sleep stages, HRV (rMSSD), skin temp, respiratory rate |
| Whoop | CSV | `pandas` | Sleep stages, HRV (rMSSD), skin temp, respiratory rate |
| Fitbit | JSON (Google Takeout) | stdlib `json` | Sleep stages, HRV, skin temp deviation |
| Samsung Health | CSV | `pandas` | Sleep stages, HR, stress, SpO2 |
| Garmin | FIT binary | `fitparse` | Sleep stages, HRV, stress, Body Battery |
| Apple Health | XML | `lxml.iterparse` | ALL synced device data (universal import) |

**UX Flow:**
```
User drags file onto chat/upload area
→ Frontend detects format (filename + content sniffing)
→ FastAPI routes to platform-specific parser adapter
→ Parser extracts SleepLog + biometric entries
→ Stored in Supabase per-user
→ ChronotypeEngine + research modules run on accumulated data
→ Hermes updates user memory with new patterns
→ Next chat: "Based on 14 nights of Oura data, your HRV drops
   18% on nights after afternoon caffeine..."
```

**Parser Architecture:**
```python
class WearableParser(Protocol):
    def parse(self, file_content: bytes, filename: str) -> list[SleepLog]: ...

class OuraParser(WearableParser): ...
class GarminParser(WearableParser): ...
class FitbitParser(WearableParser): ...
class AppleHealthParser(WearableParser): ...
class SamsungParser(WearableParser): ...
class WhoopParser(WearableParser): ...
```

**Priority:** Oura > Whoop > Fitbit > Garmin > Apple Health > Samsung

### Biometric Data Beyond Sleep

HELIOS collects more than sleep timing — the full biometric picture enables ISS-grade circadian analysis:

| Metric | What It Tells Us | Source Papers |
|---|---|---|
| HRV (rMSSD) | Parasympathetic tone, circadian phase marker, Kp impact indicator | Alabdali 2022, Woelders 2023 |
| HRV (SDNN) | Overall autonomic variability, stress recovery | McCraty 2018 |
| Resting HR | Circadian rhythm marker (HR acrophase = phase estimate) | Kolbe 2024 |
| Skin/wrist temperature | CBTmin proxy (skin max ≈ core min), sleep readiness signal | Cuesta 2017, Martinez-Nicolas 2019 |
| Respiratory rate | Sleep stage quality indicator, illness detection | — |
| SpO2 | Sleep apnea screening, altitude effects | — |
| Sleep stages | Deep/REM/light architecture for protocol scoring | — |

### Future: Custom Wearable Hardware

Long-term vision: build affordable, stylish sleep-specific wearables that outperform smartwatches for circadian metrics. HELIOS software is the foundation for a future hardware+software ecosystem. The file-upload pipeline (v1) → live API sync (v2) → custom hardware (v3) progression builds the data science and user base before committing to hardware.

### Rejected Approaches
| Approach | Why Not |
|---|---|
| Mem0 + pgvector | Needed shared API key for embeddings, added pgvector dependency, overkill for structured categories |
| Shared Gemini/GPT key for Hermes | Extra API cost to us, privacy concern (user data processed by our key), unnecessary when user's own key works |
| Hermes as orchestrator | Too heavy as middleware — simpler as background learner |
| Letta (MemGPT) | Replaces entire AI layer, too big a commitment |
| LangGraph | Overkill orchestration for a memory + markdown problem |
| CrewAI | Multi-agent = wrong paradigm, adds latency and cost |
| AutoGen | Maintenance mode, Microsoft pivoted to Semantic Kernel |
| Vector embeddings | Structured markdown categories are sufficient for circadian insights — semantic search is overkill when you have 7 clear categories |

---

## Quick Reference: Existing vs. Planned Python Modules

### Already Built (`research/chronotype_engine.py`)
- `ChronotypeEngine` — MCTQ (MSF, MSFsc, SJL)
- `ProtocolScorer` — Protocol effectiveness scoring
- `CircadianPhaseEstimator` — CBTmin and DLMO estimation

### Built (V1)
- `caffeine_model.py` — Personalized pharmacokinetics (CYP1A2, ADORA2A)
- `light_model.py` — Melanopic EDI zones, melatonin suppression prediction
- `space_weather_bio.py` — Kp → HRV impact, melatonin modifier, cognitive advisory

### To Build (V2 — see RESEARCH_V2.md)
- `alcohol_model.py` — BAC pharmacokinetics, HRV impact, REM suppression (Pietilä 2018, n=4,098)
- `breathwork_model.py` — Resonance breathing HRV response (Laborde 2022 meta-analysis)
- `nap_model.py` — NASA nap science, duration/timing optimization (Rosekind 1995)
- `meal_timing_model.py` — TRF, peripheral clock alignment (Sutton 2018, Cell Metabolism)
- `exercise_timing_model.py` — First human exercise PRC (Youngstedt 2019)
- `supplement_model.py` — Mg glycinate, melatonin, glycine (meta-analysis effect sizes)
- `cold_exposure_model.py` — Cold water HRV rebound (Espeland 2022)
- `hrv_sleep_model.py` — Sleep regularity index (Windred 2024)
- `wearable_pipeline.py` — Garmin/Oura data ingestion, cosinor phase extraction
- `jetlag_optimizer.py` — Kronauer model, optimal light schedules, asymmetry correction
