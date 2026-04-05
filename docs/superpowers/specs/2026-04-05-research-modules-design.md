# HELIOS Research Modules Design Spec

**Date**: 2026-04-05
**Modules**: `caffeine_model.py`, `space_weather_bio.py`, `light_model.py`
**Location**: `research/`

## Context

HELIOS has an existing `chronotype_engine.py` with `ChronotypeEngine`, `ProtocolScorer`, and `CircadianPhaseEstimator`. These 3 new modules extend the research backend with peer-reviewed science that maps to actionable protocol recommendations.

## Architecture Decisions

- **Independent modules** with shared dataclasses where relevant — each scientific domain is self-contained
- **Progressive profiling** — sensible population defaults, optional overrides for genotype/age/smoking/etc.
- **Raw values + advisory text** — every function returns computed values AND human-readable recommendations
- **Same patterns** as `chronotype_engine.py` — dataclasses, numpy, docstrings with citations, `__main__` examples

## Module 1: `caffeine_model.py`

### Purpose
Personalized caffeine pharmacokinetics — when to stop drinking coffee based on YOUR metabolism, not a generic "2pm cutoff."

### Citations
- Chinoy et al. (2024, SLEEP 48:zsae230) — dose-timing effects
- Nehlig et al. (2022, Front Pharmacol 12:752826) — CYP1A2 half-life variation
- Lin et al. (2022, Front Nutrition 8:787225) — steady-state accumulation
- Retey et al. (2007, Psychopharmacology) — ADORA2A sensitivity

### Data Structures

```python
@dataclass
class CaffeineProfile:
    half_life_h: float = 5.0         # population default
    genotype: str = "unknown"         # CYP1A2: "fast" | "slow" | "unknown"
    sensitivity: str = "unknown"      # ADORA2A: "sensitive" | "insensitive" | "unknown"
    smoker: bool = False              # halves half-life
    oral_contraceptive: bool = False  # doubles half-life

@dataclass
class CaffeineDose:
    mg: float
    time: datetime
```

### Functions

| Function | Inputs | Output | Science |
|---|---|---|---|
| `personalized_half_life(profile)` | CaffeineProfile | float (hours) | Base 5h, modified by genotype (3-7h), smoking (0.5x), OC (2x) |
| `remaining_caffeine(doses, target_time, profile)` | list[CaffeineDose], datetime, CaffeineProfile | dict: remaining_mg, breakdown per dose, advisory | First-order elimination: `remaining = dose * 0.5^(elapsed/half_life)` |
| `sleep_impact(doses, bedtime, profile)` | list[CaffeineDose], datetime, CaffeineProfile | dict: impact_level, sleep_latency_increase_min, fragmentation_risk, advisory | Chinoy 2024 thresholds: >100mg=significant, 50-100=moderate, <50=minimal |
| `optimal_cutoff(bedtime, profile, target_remaining_mg)` | datetime, CaffeineProfile, float=50 | dict: cutoff_time, for standard doses (100mg, 200mg, 400mg), advisory | Back-solve: `cutoff = bedtime - half_life * log2(dose/target)` |
| `steady_state(daily_doses, profile)` | list[CaffeineDose], CaffeineProfile | dict: peak_level_mg, trough_level_mg, accumulation_factor, advisory | Multi-day simulation, paraxanthine buildup per Lin 2022 |

## Module 2: `space_weather_bio.py`

### Purpose
Translate NOAA space weather data (Kp, solar wind, Bz) into biological impact predictions — the science that makes HELIOS unique.

### Citations
- Alabdali et al. (2022, Sci Total Environ 838:156067) — Kp-HRV impact (n=809)
- McCraty et al. (2018, Scientific Reports 8:2663) — long-term HRV-solar correlations
- Burch et al. (2008, Neuroscience Letters 438:76-79) — Kp-melatonin lag
- Alabdali et al. (2024, Environ Int 185:108526) — Kp-cognitive function

### Data Structures

```python
@dataclass
class SpaceWeatherReading:
    kp: float
    solar_wind_speed: float  # km/s
    bz: float                # nT (negative = southward, more geoeffective)
    timestamp: datetime
```

### Functions

| Function | Inputs | Output | Science |
|---|---|---|---|
| `kp_hrv_impact(kp, baseline_rmssd, baseline_sdnn)` | float, float=40, float=50 | dict: expected_rmssd, expected_sdnn, delta_rmssd, delta_sdnn, risk_tier, advisory | Linear: -14.7ms rMSSD per 75th-pct Kp increase (Alabdali 2022) |
| `kp_melatonin_modifier(kp_history)` | list[tuple[datetime, float]] | dict: disruption_risk (0-1), lag_window_kp_avg, advisory | Average Kp in 15-33h prior window (Burch 2008) |
| `kp_cognitive_advisory(kp)` | float | dict: impact_tier, focus_modifier (0-1), advisory | Kp>=5: significant cognitive impact (Alabdali 2024) |
| `composite_disruption(reading)` | SpaceWeatherReading | dict: bio_score (0-10), hrv_risk, melatonin_risk, cognitive_risk, protocol_adjustments, advisory | Weighted composite: Kp (0.5) + Bz (0.3) + wind (0.2) |

### Kp-to-Biology Mapping

```
Kp 0-1: Quiet       → bio_score 0-1, no adjustments
Kp 2-3: Unsettled   → bio_score 2-4, minor HRV dip expected
Kp 4:   Active      → bio_score 4-6, advance wind-down 15min
Kp 5-6: Minor Storm → bio_score 6-8, advance wind-down 30min, extend morning light
Kp 7-9: Major Storm → bio_score 8-10, advance wind-down 45min, flag cognitive impact
```

## Module 3: `light_model.py`

### Purpose
Circadian light science — melanopic EDI zones, melatonin suppression prediction, screen impact assessment.

### Citations
- Brown et al. (2022, PLOS Biology 20:e3001571) — consensus light thresholds
- Gimenez et al. (2022, J Pineal Research 72:e12786) — melatonin suppression logistic model
- Nagare et al. (2019, J Biol Rhythms 34:178-189) — age-dependent sensitivity
- West et al. (2011, J Appl Physiol 110:619-626) — blue LED dose-response
- Spitschan et al. (2023, Commun Biol 6:228) — display melanopic impact
- Mouland et al. (2025, Sci Reports 15:29882) — lamp type suppression rates

### Data Structures

```python
@dataclass
class LightReading:
    melanopic_edi_lux: float
    duration_hours: float = 1.0
    source: str = "outdoor"  # "outdoor" | "screen" | "indoor_cool" | "indoor_warm"

@dataclass
class LightProfile:
    age: int = 30
    light_sensitive: bool = False  # user override
```

### Functions

| Function | Inputs | Output | Science |
|---|---|---|---|
| `light_zone(melanopic_edi, hours_to_sleep)` | float, float | dict: zone, threshold, compliance, advisory | Brown 2022: daytime>=250, evening<=10, sleep<=1 melanopic EDI lux |
| `melatonin_suppression(melanopic_edi, duration_h, profile)` | float, float, LightProfile | dict: suppression_pct, onset_delay_min, age_factor, advisory | Gimenez 4-param logistic, age-adjusted per Nagare 2019 |
| `screen_impact(device, duration_h, hours_before_bed, profile)` | str, float, float, LightProfile | dict: device_melanopic_edi, suppression_pct, onset_delay_min, advisory | Device lookup + suppression model. Devices: phone~80, tablet~100, laptop~60, TV~30 lux |
| `lighting_risk(lamp_type, blue_filter)` | str, bool=False | dict: suppression_pct, risk_level, advisory | Mouland 2025 lookup. Blue filter = 0.5x modifier |
| `daily_light_dose(readings)` | list[LightReading] | dict: total_melanopic_lux_hours, daytime_dose, evening_dose, sufficient, advisory | Cumulative exposure assessment |

### Melatonin Suppression Model (Gimenez 2022)

```
suppression = a + (c - a) / (1 + (ED50 / melanopic_edi)^d)

Full parameter set:
  a (floor)    = 0.0   (no suppression at zero light)
  c (ceiling)  = 0.65  (max ~65% suppression, per West 2011)
  d (steepness)= 1.2   (Hill coefficient from dose-response curve)

ED50 varies by duration (interpolate for intermediate values):
  0.5h → 600 lux
  1.0h → 350 lux
  2.0h → 120 lux
  3.0h →  43 lux
  4.0h →  15 lux

Age adjustment (Nagare 2019):
  <18 years:  multiply melanopic_edi input by 1.5 before model
  18-65:      no adjustment
  >65:        multiply melanopic_edi input by 0.7 (lens yellowing)
```

### Edge Cases

- **Zero caffeine doses**: `remaining_caffeine([])` returns `{remaining_mg: 0, advisory: "No caffeine tracked"}`
- **log2(0) guard**: If dose_mg <= 0, skip that dose. If dose <= target_remaining, cutoff = "no restriction needed"
- **Midnight crossing**: Caffeine cutoff uses absolute datetime math (timedelta), not time-of-day. A 2AM bedtime with 8h cutoff = 6PM previous day — handled naturally by datetime subtraction
- **Kp baseline**: Kp=0 produces zero HRV delta. The linear model anchors at Kp=0 (quiet conditions). The -14.7ms figure is per unit increase from the 25th to 75th percentile (~Kp 1.3 to Kp 3.7, delta ~2.4 units)
- **Bz normalization**: Range -25nT to +10nT. Score = max(0, -bz) / 25, clamped to 0-1. Negative (southward) = more geoeffective
- **Solar wind normalization**: Range 300-1000 km/s. Score = (speed - 300) / 700, clamped to 0-1
- **Sparse Kp history**: `kp_melatonin_modifier` requires minimum 3 readings in the 15-33h window. Fewer = return `{disruption_risk: None, advisory: "Insufficient data"}`
- **Naming**: Use `kp_index` in SpaceWeatherReading to match existing ProtocolLog field

### Device Melanopic EDI Lookup (Spitschan 2023)

```
phone (30cm):     ~80 melanopic EDI lux
tablet (40cm):   ~100 melanopic EDI lux
laptop (50cm):    ~60 melanopic EDI lux
TV (2.5m):        ~30 melanopic EDI lux
e-reader (backlit): ~20 melanopic EDI lux
```

## Testing Strategy

Each module includes `if __name__ == "__main__"` with realistic examples:
- `caffeine_model.py`: Night owl drinks 3 coffees, check impact on 1AM bedtime
- `space_weather_bio.py`: Kp 5 storm, show HRV/melatonin/cognitive impact
- `light_model.py`: 2h tablet at 11PM, predict melatonin suppression for a 25-year-old

## Integration Points

These modules are pure Python with no frontend dependencies. Future integration:
1. **FastAPI backend** imports them as services
2. **useAI.ts** knowledge base gets updated citations
3. **protocol.ts** can call the backend for personalized protocol adjustments
4. **Mem0** stores per-user profiles (CaffeineProfile, LightProfile) that evolve over time

## Dependencies

- `numpy` (already in requirements.txt)
- `datetime`, `dataclasses`, `typing` (stdlib)
- No new dependencies needed
