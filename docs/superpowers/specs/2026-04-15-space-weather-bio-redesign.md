# Space Weather Bio Model — Research-Calibrated Redesign

> **For agentic workers:** Implement this by rewriting `research/space_weather_bio.py` in full. All effect sizes must be traceable to the cited papers.

**Goal:** Replace arbitrary linear coefficients in `SpaceWeatherBioModel` with non-linear, NOAA G-scale staged formulas anchored to peer-reviewed effect sizes.

**Architecture:** Single file rewrite — `research/space_weather_bio.py`. No interface changes visible to callers except new fields added to outputs.

**Tech Stack:** Python, numpy, existing `research/evidence_contract.py` patterns

---

## What Was Wrong

| Problem | Old code | Source of old value |
|---|---|---|
| Linear HRV slope | `delta_rmssd = -6.125 * kp_index` | Unknown — not in Alabdali 2022 |
| Melatonin risk | `disruption_risk = avg_kp / 7.0` | Arbitrary |
| Composite weights | `0.5*kp + 0.3*bz + 0.2*wind` | Arbitrary |
| Bz as biological input | Direct weight in composite | No published bio dose-response for Bz |

---

## Evidence Base

### HRV — Alabdali et al. 2022
**Citation:** Alabdali M et al. *Sci Total Environ* 838:156067. DOI: 10.1016/j.scitotenv.2022.156067  
**Study:** n=809 elderly men, 2,540 visits, 17-year follow-up (Normative Aging Study, Boston ~42°N)  
**Effect sizes (per 75th%ile Kp increase over 15-hour window):**
- rMSSD: **−14.7 ms** (95% CI −23.1, −6.3; p=0.0007)
- SDNN: **−8.2 ms** (95% CI −13.9, −2.5; p=0.006)
- Cohort baseline: rMSSD ~68 ms → −14.7/68 ≈ **22% reduction at G1–G2 boundary**
- CHD subgroup: rMSSD −19.1 ms (stronger — used to calibrate G3–G4)
- Temporal: significant associations up to 9 hours prior (rMSSD), 6 hours (SDNN)

### Cognitive — Liddie et al. 2024
**Citation:** Liddie JM et al. *Environ Int* 187:108666. PMC: PMC11146138  
**Study:** n=1,081, 3,248 cognitive visits, elderly males, Boston  
**Key findings:**
- +19% increased odds of low MMSE per IQR same-day Kp (95% CI 4–36%)
- +30% increased odds per 28-day avg Kp (95% CI 12–51%)
- Working memory (Backward Digit Span): −0.08 SD per SSN IQR
- Domain specificity: MMSE + working memory; verbal fluency/recall: null

### Melatonin — Burch et al. 1999/2008 + Weydahl et al. 2001
**Citations:**
- Burch JB et al. *Neurosci Lett* 266:209 (1999); 438:76 (2008) — n=132, n=153 utility workers ~40°N
- Weydahl A et al. *Biol Rhythm Res* 33:33 (2001) — n=25, Alta Norway 70°N. **Independent group.**

**Key findings:**
- Published disruption threshold: aa/A(K) > **30 nT** (Burch) / local field change > **80 nT/3h** (Weydahl at 70°N)
- **15–33h lag window** consistent across both groups
- Two independent research groups corroborate directional finding

### Blood Pressure — Chen et al. 2025
**Citation:** Chen Y et al. *Commun Med* (Nature). PMC: PMC12038039  
**Study:** n=554,319 BP measurements, Qingdao + Weihai China (35–37°N), 6-year series  
**Key finding:** Spearman rs=0.409 (p=0.0004) between systolic BP and Ap index  
**Clinical magnitude:** 3–8 mmHg systolic at mid-latitudes; up to 15 mmHg during severe storms

### Latitude — Physical gradient
**Basis:** Geomagnetic field variation during storms is ~5× larger at poles than equator (Weydahl 2001; standard geophysics)  
**Biological calibration:** Not independently done across latitudes — modifier reflects physical gradient only

### Mechanism — Wang, Kirschvink et al. 2019
**Citation:** Wang CX, Kirschvink JL et al. *eNeuro* 6(2):ENEURO.0483-18.2019. PMC: PMC6494972  
**Study:** n=36, magnetically shielded room, Earth-strength field rotations (~35 µT)  
**Key finding:** Alpha-EEG power drop up to 50–60% (ηp²=0.34); magnetite mechanism supported  
**Replication:** Chae et al. 2022 (light-dependent variant)

---

## New Design

### NOAA G-Scale Staging (replaces linear formula)

| G-scale | Kp | Condition | rMSSD effect | Basis |
|---|---|---|---|---|
| G0 | 0–2 | Quiet | 0% | No published signal |
| G0–G1 | 3–4 | Unsettled | −8% | Sub-threshold conservative |
| G1 | 5 | Minor storm | −15% | Alabdali 2022 lower bound |
| G2 | 6 | Moderate storm | −22% | **Alabdali anchor** (−14.7ms/68ms) |
| G3 | 7 | Strong storm | −30% | CHD subgroup scaled |
| G4 | 8 | Severe storm | −36% | Interpolated |
| G5 | 9 | Extreme | −42% | Extrapolated — labeled |

Effects are **percentage-based against personal baseline rMSSD** (not fixed ms) so they scale correctly across individuals.

### Latitude Modifier

```python
# Anchored at 42°N (Alabdali/Burch study latitude) → ×1.0
# Equator (0°) → ×0.5
# Poles (90°) → ×5.0
def _latitude_modifier(latitude: float) -> float:
    anchor_lat = 42.0
    if abs(latitude) <= anchor_lat:
        return 0.5 + 0.5 * (abs(latitude) / anchor_lat)
    else:
        return 1.0 + 4.0 * ((abs(latitude) - anchor_lat) / (90.0 - anchor_lat))
```

### Bz — Storm Arrival Predictor Only

Bz is removed from the biological composite. Instead:
```
Bz < −10 nT sustained → storm_imminent = True
  "Southward Bz detected. Kp likely to rise within ~N minutes."
  (propagation time = 1,500,000 km / solar_wind_speed / 60)
```

### Melatonin — Threshold Tiers (replaces `avg_kp / 7.0`)

| effective_kp | risk_tier | disruption_risk |
|---|---|---|
| < 3.0 | low | 0.0–0.2 |
| 3.0–5.0 | approaching_threshold | 0.2–0.55 |
| 5.0–7.0 | at_threshold | 0.55–0.80 |
| ≥ 7.0 | above_threshold | 0.80–1.0 |

effective_kp = avg_kp × latitude_modifier

### New Outputs Added

- `bp_advisory()` method — Chen 2025, per-G-scale
- `bz_storm_predictor()` method — physics-based, with propagation time
- `composite_disruption()` now returns `g_scale`, `biological_alert`, `storm_arrival` block, `bp_systolic_fluctuation_mmhg`, `mechanism_note`

### Composite Redesign

Old: `0.5*kp_norm + 0.3*bz_norm + 0.2*wind_norm`  
New: G-scale derived from Kp (primary), Bz as precursor predictor, wind speed = contextual label only

---

## Files Modified

- **Rewrite:** `research/space_weather_bio.py`
- **Update:** `helios-app/CLAUDE.md` research modules grade
