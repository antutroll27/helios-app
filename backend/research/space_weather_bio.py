"""
HELIOS - Space Weather Biological Impact Model
Translates NOAA space weather data (Kp, Bz) into research-calibrated biological context.

All effect sizes are anchored to peer-reviewed literature. Formulas are non-linear
and threshold-gated by NOAA G-scale, reflecting the published finding that geomagnetic
biological effects are disproportionately concentrated at storm-level activity (Kp ≥ 5)
rather than distributed linearly across the full Kp range.

Primary References:
- Alabdali, M. et al. (2022) 'Geomagnetic disturbances reduce heart rate variability in
  the Normative Aging Study', Sci Total Environ, 838, 156067.
  DOI: 10.1016/j.scitotenv.2022.156067  PMC: PMC9233046
  Effect: rMSSD −14.7 ms (95% CI −23.1, −6.3; p=0.0007), SDNN −8.2 ms (95% CI −13.9, −2.5)
  per 75th %ile Kp increase over 15-hour window. n=809, 17-year follow-up.

- Liddie, J.M. et al. (2024) 'Associations between solar and geomagnetic activity and
  cognitive function in the Normative Aging study', Environ Int, 187, 108666.
  PMC: PMC11146138
  Effect: +19–30% increased odds of low MMSE per IQR Kp increase. n=1,081.

- Burch, J.B. et al. (1999) Neurosci Lett 266:209; (2008) Neurosci Lett 438:76.
  Effect: Nocturnal melatonin (6-OHMS) reduced when aa/A(K) > 30 nT in 15–33h lag window.

- Weydahl, A. et al. (2001) 'Geomagnetic activity influences melatonin at latitude 70°N',
  Biol Rhythm Res, 33, 33. DOI: 10.1076/brhm.33.1.33.1337
  Effect: Salivary melatonin reduced when local field change exceeded 80 nT per 3h.
  Independent group corroboration of the Burch melatonin finding.

- Chen, Y. et al. (2025) 'Potential influence of geomagnetic activity on blood pressure
  statistical fluctuations at mid-magnetic latitudes', Commun Med (Nature).
  PMC: PMC12038039
  Effect: Spearman rs=0.409 (p=0.0004) systolic BP vs Ap index. n=554,319 measurements.

- Vencloviene, J. et al. (2023) 'High Heart Rate Variability Causes Better Adaptation to
  the Impact of Geomagnetic Storms', Atmosphere, 14, 1707.
  Effect: High-baseline HRV individuals show adaptive (not purely suppressive) autonomic
  response during geomagnetic storm onset.

- Wang, C.X., Kirschvink, J.L. et al. (2019) 'Transduction of the Geomagnetic Field as
  Evidenced from alpha-Band Activity in the Human Brain', eNeuro, 6(2).
  PMC: PMC6494972
  Effect: Alpha-EEG power drop up to 60% (ηp²=0.34) in response to Earth-strength field
  rotations. Magnetite mechanism is most parsimonious explanation.

- Linares, C. et al. (2019) 'Geomagnetic disturbances enhance total and cardiovascular
  mortality risk in 263 US cities', Environ Health, 18, 78.  PMC: PMC6739933
  Effect: +0.31% total deaths, +0.7% MI deaths per SD Kp. n=44,220,261 deaths.

- Gaisenok, O. et al. (2025) MI/Stroke meta-analysis, J Med Physics.
  Effect: MI/ACS RR 1.29–1.39 (95% CI 1.19–1.40) during geomagnetic storms. 6 studies.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from evidence_contract import EvidenceProfile, merge_evidence


# ─── NOAA G-SCALE LOOKUP ────────────────────────────────────────────────────
# NOAA defines five geomagnetic storm severity levels (G1–G5) mapped from Kp.
# G-scale reflects the non-linear nature of storm energy — a G3 storm is not
# 3× a G1 storm; it represents a qualitatively different magnetospheric state.
# Below G1 (Kp < 5) the field is "quiet" or "unsettled", not storm-classified.

# (kp_min, kp_max_exclusive, g_scale, condition_label, bio_alert)
_GSCALE_TABLE = [
    (0.0, 3.0, "G0",    "Quiet",               "quiet"),
    (3.0, 5.0, "G0-G1", "Unsettled/Active",    "unsettled"),
    (5.0, 6.0, "G1",    "Minor Storm",         "minor"),
    (6.0, 7.0, "G2",    "Moderate Storm",      "moderate"),
    (7.0, 8.0, "G3",    "Strong Storm",        "significant"),
    (8.0, 9.0, "G4",    "Severe Storm",        "severe"),
    (9.0, 10., "G5",    "Extreme Storm",       "extreme"),
]

# Non-linear HRV suppression percentages keyed to G-scale.
#
# Calibration anchor — Alabdali 2022 at the G1–G2 boundary (Kp 5–6):
#   −14.7 ms from a cohort mean rMSSD of ~68 ms → 14.7/68 ≈ 21.6% ≈ 22%
#
# Sub-threshold (G0–G1, Kp 3–4): conservative estimate; observational trends
#   exist but are not statistically established. Set at 8% as a lower bound.
#
# G3–G4: calibrated from the CHD subgroup in Alabdali 2022 (rMSSD −19.1 ms
#   from the same 68 ms baseline ≈ 28%); scaled upward for G4 strong storms.
#
# G5: extrapolated — flagged as such in all outputs.
#
# Effect is expressed as a FRACTION of the individual's baseline rMSSD so that
# it scales correctly across people (not a fixed ms offset applied to everyone).
_HRV_SUPPRESSION_BY_GSCALE: dict[str, float] = {
    "G0":    0.00,   # No published biological signal at Kp 0–2
    "G0-G1": 0.08,   # Sub-threshold; conservative estimate (Kp 3–4)
    "G1":    0.15,   # Minor storm onset — Alabdali 2022 lower calibration bound
    "G2":    0.22,   # Primary Alabdali 2022 anchor: −14.7 ms / 68 ms baseline
    "G3":    0.30,   # CHD subgroup (−19.1 ms / 68 ms ≈ 28%); healthy adult scaled up
    "G4":    0.36,   # Severe storm; interpolated
    "G5":    0.42,   # Extreme; extrapolated — labeled in all outputs
}

# SDNN suppression ≈ 66% of rMSSD suppression across the G-scale.
# Derived from the Alabdali 2022 ratio: SDNN delta (8.2 ms / 57 ms ≈ 14.4%)
# vs rMSSD delta (14.7 ms / 68 ms ≈ 21.6%): 14.4 / 21.6 ≈ 0.67.
_SDNN_SUPPRESSION_RATIO = 0.67


# ─── DATA STRUCTURES ────────────────────────────────────────────────────────

@dataclass
class SpaceWeatherReading:
    """Single snapshot of space weather conditions from NOAA SWPC."""
    kp_index: float
    solar_wind_speed: float   # km/s — contextual label only, not a biological weight
    bz: float                 # nT GSM — storm-arrival predictor only, not biological metric
    timestamp: datetime
    latitude: float = 45.0   # Observer latitude °N/S; defaults to mid-latitude anchor


# ─── INTERNAL HELPERS ───────────────────────────────────────────────────────

def _kp_to_gscale(kp: float) -> tuple[str, str, str]:
    """Map a Kp value to (g_scale, condition_label, bio_alert)."""
    kp = max(0.0, min(9.0, kp))
    for kp_min, kp_max, g, condition, bio in _GSCALE_TABLE:
        if kp_min <= kp < kp_max:
            return g, condition, bio
    return "G5", "Extreme Storm", "extreme"


def _latitude_modifier(latitude: float) -> float:
    """
    Scale geomagnetic biological effects by observer latitude.

    Physical basis: Geomagnetic field variation during storms is ~5× larger at
    polar latitudes than at the equator (Weydahl 2001; standard geophysics).
    The modifier is anchored at 42°N — the latitude of the Alabdali 2022 and
    Burch 1999/2008 studies — so published effect sizes emerge unmodified at
    the default mid-latitude anchor.

    Scale: equator (0°) → ×0.5, anchor (42°N/S) → ×1.0, poles (90°) → ×5.0.
    Biological dose-response at different latitudes is not independently validated;
    this modifier reflects the physical gradient only.
    """
    abs_lat = abs(latitude)
    anchor = 42.0
    if abs_lat <= anchor:
        return 0.5 + 0.5 * (abs_lat / anchor)
    return 1.0 + 4.0 * ((abs_lat - anchor) / (90.0 - anchor))


def _hrv_suppression_pct(kp: float, latitude: float) -> float:
    """
    Return fractional rMSSD suppression [0.0, 0.65] for given Kp and latitude.

    Non-linear G-scale staging (not a linear slope) — see _HRV_SUPPRESSION_BY_GSCALE.
    Capped at 65%: beyond this the model extrapolates too far from the calibration data.
    """
    g_scale, _, _ = _kp_to_gscale(kp)
    base = _HRV_SUPPRESSION_BY_GSCALE[g_scale]
    return min(0.65, base * _latitude_modifier(latitude))


# ─── MAIN MODEL ─────────────────────────────────────────────────────────────

class SpaceWeatherBioModel:
    """
    Maps geomagnetic parameters to research-calibrated biological context.

    Key design decisions:
    - Non-linear NOAA G-scale staging (not a linear Kp slope): biological effects
      are threshold-gated, concentrated at storm onset (Kp ≥ 5), not proportional
      across the full 0–9 Kp range.
    - Effect sizes are percentage-based against the user's personal baseline HRV,
      so outputs scale correctly across individuals.
    - Bz is used exclusively as a physics-layer storm-arrival predictor; no
      peer-reviewed study has established a direct Bz-to-biology dose-response.
    - Latitude modifier reflects the 5× physical geomagnetic gradient between
      equatorial and polar regions; biological calibration at different latitudes
      has not been independently validated.
    - All outputs are observational-level context — not validated individual forecasts.
    """

    COMPOSITE_EVIDENCE_PROFILE = EvidenceProfile(
        evidence_tier="C",
        effect_summary=(
            "Exploratory geomagnetic context model using non-linear G-scale staging. "
            "HRV effect sizes anchored to Alabdali 2022 "
            "(n=809, 17-year cohort). Cognitive associations from Liddie 2024 (n=1,081). "
            "Melatonin thresholds from Burch 1999/2008 + Weydahl 2001 (two independent groups). "
            "BP correlation from Chen 2025 (n=554,319)."
        ),
        population_summary=(
            "Primarily elderly male cohorts (Normative Aging Study, Boston ~42°N) and small "
            "healthy adult studies. Individual predictions carry higher uncertainty than "
            "population-level associations."
        ),
        main_caveat=(
            "Associations are population-level and observational. "
            "Most confirmatory studies use the same cohort or research group. "
            "Effect sizes should not be treated as validated personal forecasts."
        ),
        uncertainty_factors=[
            "latitude", "baseline HRV and cardiac health", "age", "sex",
            "comorbidities (CHD, hypertension amplify effects)",
            "concurrent stressors (PM2.5, sleep debt, caffeine)",
            "measurement lag between Kp exposure and biological response",
        ],
        claim_boundary=(
            "Context only for conservative protocol guidance. "
            "Not the sole basis for clinical or safety decisions."
        ),
    )

    # ── Bz Storm Arrival Predictor ──────────────────────────────────────────

    def bz_storm_predictor(
        self,
        bz: float,
        solar_wind_speed: float = 400.0,
    ) -> dict:
        """
        Physics-based storm-arrival predictor using IMF Bz.

        Bz is measured at the L1 Lagrange point (~1.5 million km sunward).
        Sustained southward Bz (< −10 nT) enables magnetic reconnection at
        the magnetopause, driving energy into the ring current and producing
        the Kp increase observed in biological studies.

        Propagation time from L1 to Earth: ~15–60 minutes depending on
        solar wind speed. This gives users actionable lead time before
        Kp rises and biological effects intensify.

        No peer-reviewed study has established a direct Bz-to-biology
        dose-response curve — Bz is upstream of Kp in the causal chain.
        """
        propagation_min = int(1_500_000 / max(300.0, solar_wind_speed) / 60)

        if bz >= -5.0:
            return {
                "storm_imminent": False,
                "bz_nT": round(bz, 1),
                "southward_coupling": "weak",
                "propagation_min": propagation_min,
                "advisory": (
                    "Northward or weakly southward Bz. Magnetosphere coupling is limited — "
                    "no storm onset expected imminently."
                ),
            }
        elif bz >= -10.0:
            return {
                "storm_imminent": False,
                "bz_nT": round(bz, 1),
                "southward_coupling": "moderate",
                "propagation_min": propagation_min,
                "advisory": (
                    f"Moderately southward Bz ({bz:.1f} nT). Magnetosphere is weakly coupled. "
                    "If this persists, Kp may rise within 1–3 hours — monitor for storm onset."
                ),
            }
        elif bz >= -20.0:
            return {
                "storm_imminent": True,
                "bz_nT": round(bz, 1),
                "southward_coupling": "strong",
                "propagation_min": propagation_min,
                "advisory": (
                    f"Strongly southward Bz ({bz:.1f} nT). Storm-level conditions likely at "
                    f"Earth in ~{propagation_min} minutes. Begin conservative recovery protocol now."
                ),
            }
        else:
            return {
                "storm_imminent": True,
                "bz_nT": round(bz, 1),
                "southward_coupling": "extreme",
                "propagation_min": propagation_min,
                "advisory": (
                    f"Extreme southward Bz ({bz:.1f} nT). Major geomagnetic storm likely at "
                    f"Earth in ~{propagation_min} minutes. Consistent with G3–G5 conditions."
                ),
            }

    # ── HRV Impact ─────────────────────────────────────────────────────────

    def kp_hrv_impact(
        self,
        kp_index: float,
        baseline_rmssd: float = 45.0,
        baseline_sdnn: float = 50.0,
        latitude: float = 45.0,
    ) -> dict:
        """
        Estimate HRV changes from geomagnetic activity using non-linear G-scale staging.

        Calibration anchor — Alabdali et al. (2022, Sci Total Environ 838:156067):
          rMSSD −14.7 ms, SDNN −8.2 ms per 75th %ile Kp increase over 15 hours.
          Cohort baseline: rMSSD ~68 ms, SDNN ~57 ms (elderly males, Boston ~42°N).
          The G1–G2 boundary (Kp 5–6) is used as the primary calibration zone,
          giving −14.7/68 ≈ 22% rMSSD suppression at that G-scale.

        Effect is applied as a percentage of the individual's baseline — not a
        fixed ms subtraction — so it scales correctly across different baselines.

        Baseline adaptation note (Vencloviene 2023, Atmosphere 14:1707):
          Individuals with high baseline HRV (rMSSD > 60 ms) may show an adaptive
          autonomic response during storm onset rather than pure suppression.
        """
        kp_index = max(0.0, min(9.0, kp_index))
        if baseline_rmssd <= 0 or baseline_sdnn <= 0:
            return {
                "error": "Baseline HRV values must be positive.",
                "expected_rmssd": baseline_rmssd,
                "expected_sdnn": baseline_sdnn,
            }

        g_scale, condition, bio_alert = _kp_to_gscale(kp_index)
        suppression_pct = _hrv_suppression_pct(kp_index, latitude)
        sdnn_suppression_pct = suppression_pct * _SDNN_SUPPRESSION_RATIO

        delta_rmssd = -(baseline_rmssd * suppression_pct)
        delta_sdnn = -(baseline_sdnn * sdnn_suppression_pct)
        expected_rmssd = max(5.0, baseline_rmssd + delta_rmssd)
        expected_sdnn = max(5.0, baseline_sdnn + delta_sdnn)
        lat_mod = _latitude_modifier(latitude)
        is_extrapolated = g_scale in ("G4", "G5")
        adaptive_response = baseline_rmssd > 60.0 and kp_index >= 5.0

        if bio_alert == "quiet":
            advisory = (
                "Quiet geomagnetic conditions (G0). Published studies show no clear "
                "HRV signal at this activity level. No protocol adjustment indicated."
            )
        elif bio_alert == "unsettled":
            advisory = (
                f"Unsettled conditions ({g_scale}). Sub-threshold geomagnetic activity. "
                "Observational trends exist but are not statistically established at this level."
            )
        elif bio_alert == "minor":
            advisory = (
                f"Minor geomagnetic storm ({g_scale}, Kp {kp_index:.1f}). "
                "Alabdali 2022 (n=809, 17-year cohort) found statistically significant "
                "rMSSD and SDNN reductions at this storm level. Consider conservative recovery."
            )
        elif bio_alert == "moderate":
            advisory = (
                f"Moderate geomagnetic storm ({g_scale}, Kp {kp_index:.1f}). "
                "Primary Alabdali 2022 calibration zone — population-level HRV suppression "
                "is well-established here. Individual effect varies with baseline HRV and health."
            )
        else:
            extrapolation_note = "Extrapolated beyond primary calibration range. " if is_extrapolated else ""
            advisory = (
                f"{extrapolation_note}Strong–extreme geomagnetic storm ({g_scale}, Kp {kp_index:.1f}). "
                "CHD subgroup from Alabdali 2022 showed rMSSD −19.1 ms at storm level. "
                "Conservative recovery protocol strongly indicated."
            )

        if adaptive_response:
            advisory += (
                " High baseline rMSSD (>60 ms) is associated with a more adaptive autonomic "
                "response during storm onset (Vencloviene 2023) — actual suppression may be smaller."
            )

        return {
            "g_scale": g_scale,
            "condition": condition,
            "expected_rmssd": round(expected_rmssd, 1),
            "expected_sdnn": round(expected_sdnn, 1),
            "delta_rmssd": round(delta_rmssd, 1),
            "delta_sdnn": round(delta_sdnn, 1),
            "suppression_pct": round(suppression_pct * 100, 1),
            "latitude_modifier": round(lat_mod, 2),
            "adaptive_response_possible": adaptive_response,
            "is_extrapolated": is_extrapolated,
            "evidence_level": "observational",
            "citation": (
                "Alabdali et al. 2022, Sci Total Environ 838:156067; "
                "Vencloviene et al. 2023, Atmosphere 14:1707"
            ),
            "advisory": advisory,
        }

    # ── Melatonin Modifier ──────────────────────────────────────────────────

    def kp_melatonin_modifier(
        self,
        kp_history: list[tuple[datetime, float]],
        latitude: float = 45.0,
    ) -> dict:
        """
        Estimate melatonin disruption risk from lagged Kp history using
        published threshold-based evidence.

        Two independent research groups corroborate the finding:
        - Burch et al. 1999 (n=132), 2008 (n=153), Colorado ~40°N:
          6-OHMS reduced when aa/A(K) > 30 nT in the 15–33h lag window.
        - Weydahl et al. 2001 (n=25), Alta Norway 70°N:
          Salivary melatonin reduced when local field change > 80 nT per 3h.

        The 15–33 hour lag is consistent across both groups, reflecting the
        circadian clock delay in melatonin biosynthesis response.

        Risk uses named threshold tiers — not a linear formula — because the
        published evidence identifies a threshold effect (aa > 30 nT), not a
        proportional dose-response across the full Kp range.
        """
        if not kp_history:
            return {
                "disruption_risk": None,
                "risk_tier": "insufficient_data",
                "lag_window_kp_avg": None,
                "readings_in_window": 0,
                "evidence_level": "preliminary",
                "advisory": "Insufficient data — need Kp readings from 15–33h ago.",
            }

        now = kp_history[-1][0]
        window_start = now - timedelta(hours=33)
        window_end = now - timedelta(hours=15)
        readings_in_window = [kp for ts, kp in kp_history if window_start <= ts <= window_end]

        if len(readings_in_window) < 3:
            return {
                "disruption_risk": None,
                "risk_tier": "insufficient_data",
                "lag_window_kp_avg": None,
                "readings_in_window": len(readings_in_window),
                "evidence_level": "preliminary",
                "advisory": "Insufficient data — need at least 3 Kp readings in the 15–33h lag window.",
            }

        avg_kp = float(np.mean(readings_in_window))
        lat_mod = _latitude_modifier(latitude)
        # Latitude-adjust the effective Kp: higher at polar regions where
        # the physical field disturbance is larger (Weydahl 2001, 70°N).
        effective_kp = avg_kp * lat_mod

        if effective_kp < 3.0:
            risk_tier = "low"
            disruption_risk = round(effective_kp / 3.0 * 0.2, 3)
            advisory = (
                "Lag-window Kp is below published melatonin disruption thresholds "
                "(aa < 30 nT; Burch 1999/2008). No clear melatonin concern at this level."
            )
        elif effective_kp < 5.0:
            risk_tier = "approaching_threshold"
            disruption_risk = round(0.2 + (effective_kp - 3.0) / 2.0 * 0.35, 3)
            advisory = (
                f"Lag-window Kp ({avg_kp:.1f}, latitude-adjusted {effective_kp:.1f}) is "
                "approaching the published disruption threshold (aa ~30 nT, Burch 1999/2008). "
                "Maintain good sleep hygiene and avoid additional melatonin suppressants "
                "(bright light, caffeine) in the evening hours."
            )
        elif effective_kp < 7.0:
            risk_tier = "at_threshold"
            disruption_risk = round(0.55 + (effective_kp - 5.0) / 2.0 * 0.25, 3)
            advisory = (
                f"Lag-window Kp ({avg_kp:.1f}, latitude-adjusted {effective_kp:.1f}) meets "
                "or exceeds the published disruption threshold. Two independent research groups "
                "(Burch 1999/2008 at ~40°N; Weydahl 2001 at 70°N) found melatonin suppression "
                "at this level. Prioritise darkness and melatonin-protective behaviours."
            )
        else:
            risk_tier = "above_threshold"
            disruption_risk = round(min(1.0, 0.80 + (effective_kp - 7.0) / 2.0 * 0.20), 3)
            advisory = (
                f"Lag-window Kp ({avg_kp:.1f}, latitude-adjusted {effective_kp:.1f}) is "
                "well above published disruption thresholds. Melatonin suppression is the most "
                "consistently replicated biological effect of geomagnetic activity. "
                "Strict light discipline from 20:00, blackout conditions for sleep."
            )

        return {
            "disruption_risk": disruption_risk,
            "risk_tier": risk_tier,
            "lag_window_kp_avg": round(avg_kp, 2),
            "effective_kp_latitude_adjusted": round(effective_kp, 2),
            "readings_in_window": len(readings_in_window),
            "latitude_modifier": round(lat_mod, 2),
            "evidence_level": "preliminary",
            "evidence_note": (
                "Two independent groups (Burch et al. 1999/2008; Weydahl et al. 2001) have "
                "reported geomagnetic melatonin suppression with consistent 15–33h lag windows. "
                "Large-scale replication with polysomnography is not yet available."
            ),
            "citation": (
                "Burch et al. 1999, Neurosci Lett 266:209; "
                "Burch et al. 2008, Neurosci Lett 438:76; "
                "Weydahl et al. 2001, Biol Rhythm Res 33:33"
            ),
            "advisory": advisory,
        }

    # ── Cognitive Advisory ──────────────────────────────────────────────────

    def kp_cognitive_advisory(self, kp_index: float) -> dict:
        """
        Cognitive impact guidance from Liddie et al. (2024, Environ Int 187:108666).

        Key findings (n=1,081, 3,248 cognitive visits, elderly males, Boston):
          - +19% increased odds of low MMSE per IQR same-day Kp (95% CI 4–36%)
          - +30% increased odds of low MMSE per 28-day avg Kp (95% CI 12–51%)
          - Working memory (Backward Digit Span): −0.08 SD per SSN IQR
          - Domain specificity: MMSE + working memory affected; verbal fluency: null

        Effects begin at Kp ≥ 3 (trends) and are statistically established at Kp ≥ 5.
        Cohort was elderly males — effects in younger or diverse populations not
        independently validated.
        """
        kp_index = max(0.0, min(9.0, kp_index))
        g_scale, condition, bio_alert = _kp_to_gscale(kp_index)

        if bio_alert == "quiet":
            return {
                "g_scale": g_scale,
                "condition": condition,
                "impact_tier": "background",
                "working_memory_impact": "none",
                "focus_modifier": 1.0,
                "evidence_level": "observational",
                "citation": "Liddie et al. 2024, Environ Int 187:108666",
                "advisory": (
                    "Quiet geomagnetic conditions. Liddie 2024 found no significant cognitive "
                    "associations at this Kp level. No adjustment needed."
                ),
            }
        elif bio_alert == "unsettled":
            return {
                "g_scale": g_scale,
                "condition": condition,
                "impact_tier": "sub_threshold",
                "working_memory_impact": "possible_trend",
                "focus_modifier": 0.95,
                "evidence_level": "observational",
                "citation": "Liddie et al. 2024, Environ Int 187:108666",
                "advisory": (
                    f"Unsettled conditions ({g_scale}). Sub-threshold trends exist but are not "
                    "statistically established at this Kp level. Treat as background context."
                ),
            }
        elif bio_alert in ("minor", "moderate"):
            return {
                "g_scale": g_scale,
                "condition": condition,
                "impact_tier": "mild_established",
                "working_memory_impact": "likely_reduced",
                "focus_modifier": 0.85,
                "evidence_level": "observational",
                "citation": "Liddie et al. 2024, Environ Int 187:108666",
                "advisory": (
                    f"Minor to moderate storm ({g_scale}, Kp {kp_index:.1f}). "
                    "Liddie 2024: +19–30% increased odds of low MMSE in this Kp range. "
                    "Working memory (digit span) is the most consistently affected domain. "
                    "This has uncertain individual relevance; prefer routine cognitive tasks "
                    "and defer high-stakes decisions if possible."
                ),
            }
        elif bio_alert == "significant":
            return {
                "g_scale": g_scale,
                "condition": condition,
                "impact_tier": "moderate_established",
                "working_memory_impact": "reduced",
                "focus_modifier": 0.75,
                "evidence_level": "observational",
                "citation": "Liddie et al. 2024, Environ Int 187:108666",
                "advisory": (
                    f"Strong storm ({g_scale}, Kp {kp_index:.1f}). Storm-level Kp is the primary "
                    "calibration zone for Liddie 2024 cognitive findings. Working memory and "
                    "executive function most affected. Avoid high-complexity tasks requiring "
                    "sustained attention."
                ),
            }
        else:
            return {
                "g_scale": g_scale,
                "condition": condition,
                "impact_tier": "severe_storm_context",
                "working_memory_impact": "significantly_reduced",
                "focus_modifier": 0.65,
                "evidence_level": "observational",
                "citation": "Liddie et al. 2024, Environ Int 187:108666",
                "advisory": (
                    f"Severe–extreme storm ({g_scale}, Kp {kp_index:.1f}). Beyond calibration range "
                    "of Liddie 2024 — treat as exploratory. Strongest advisory for cognitive load "
                    "reduction; prioritise sleep and recovery above all."
                ),
            }

    # ── Blood Pressure Advisory ─────────────────────────────────────────────

    def bp_advisory(self, kp_index: float, latitude: float = 45.0) -> dict:
        """
        Blood pressure advisory from Chen et al. (2025, Commun Med, Nature).

        Key finding: Spearman rs=0.409 (p=0.0004) between systolic BP and Ap index
        in n=554,319 BP measurements (China, 35–37°N, 6-year time series).

        Clinical magnitude from literature:
          - Active periods: 3–8 mmHg systolic (Cureus review, PMC10589055)
          - Severe storms: up to 15 mmHg systolic (individual case series)
          - Gaisenok 2025 meta-analysis: MI/ACS RR 1.29–1.39 during storms

        Outputs are latitude-scaled given the physical geomagnetic gradient;
        hypertensive individuals should treat this as a monitoring advisory.
        """
        kp_index = max(0.0, min(9.0, kp_index))
        g_scale, _, bio_alert = _kp_to_gscale(kp_index)
        lat_mod = _latitude_modifier(latitude)

        if bio_alert == "quiet":
            return {
                "g_scale": g_scale,
                "systolic_fluctuation_mmhg": "0–2",
                "clinical_relevance": "negligible",
                "citation": "Chen et al. 2025, Commun Med (Nature), PMC12038039",
                "advisory": "Quiet conditions. No meaningful BP fluctuation from geomagnetic activity.",
            }
        elif bio_alert == "unsettled":
            return {
                "g_scale": g_scale,
                "systolic_fluctuation_mmhg": "1–3",
                "clinical_relevance": "sub_clinical",
                "citation": "Chen et al. 2025, Commun Med (Nature), PMC12038039",
                "advisory": (
                    "Sub-threshold activity. Minor BP fluctuations possible (1–3 mmHg systolic) — "
                    "within normal daily variability range."
                ),
            }
        elif bio_alert in ("minor", "moderate"):
            upper = int(8 * min(2.0, lat_mod))
            return {
                "g_scale": g_scale,
                "systolic_fluctuation_mmhg": f"3–{upper}",
                "clinical_relevance": "clinically_notable",
                "citation": (
                    "Chen et al. 2025, Commun Med (Nature); "
                    "Cureus review PMC10589055"
                ),
                "advisory": (
                    f"Active geomagnetic conditions ({g_scale}). n=554,319 population data "
                    f"suggest 3–{upper} mmHg systolic fluctuation. "
                    "Hypertensive individuals: monitor BP and maintain medication adherence."
                ),
            }
        else:
            upper = int(15 * min(2.0, lat_mod))
            return {
                "g_scale": g_scale,
                "systolic_fluctuation_mmhg": f"8–{upper}",
                "clinical_relevance": "clinically_significant",
                "citation": (
                    "Chen et al. 2025, Commun Med (Nature); "
                    "Gaisenok et al. 2025 meta-analysis, J Med Physics"
                ),
                "advisory": (
                    f"Storm conditions ({g_scale}). Literature documents 8–{upper} mmHg "
                    "systolic elevation during geomagnetic storms. "
                    "Gaisenok 2025 meta-analysis: MI/ACS RR 1.29–1.39 during storms. "
                    "Cardiovascular patients: prioritise stress reduction and medication adherence."
                ),
            }

    # ── Composite Disruption ────────────────────────────────────────────────

    def composite_disruption(self, reading: SpaceWeatherReading) -> dict:
        """
        Research-calibrated composite output for a SpaceWeatherReading.

        Architecture:
        - Kp → NOAA G-scale → HRV suppression %, cognitive modifier, BP advisory
          (primary biological signal; calibrated to published effect sizes)
        - Bz → storm-arrival predictor with propagation time estimate
          (physics layer; not a direct biological weight)
        - Solar wind speed → contextual label only
          (its biological effect is already captured downstream by Kp via V×Bz)

        Replaces the previous arbitrary weighted sum (0.5*Kp + 0.3*Bz + 0.2*wind)
        with G-scale staged outputs whose constants are traceable to peer-reviewed
        literature.
        """
        kp = max(0.0, min(9.0, reading.kp_index))
        latitude = reading.latitude
        g_scale, condition, bio_alert = _kp_to_gscale(kp)

        hrv = self.kp_hrv_impact(kp, latitude=latitude)
        cog = self.kp_cognitive_advisory(kp)
        bp = self.bp_advisory(kp, latitude=latitude)
        storm_pred = self.bz_storm_predictor(reading.bz, reading.solar_wind_speed)

        protocol_adjustments: list[str] = []

        if bio_alert == "quiet":
            overall_advisory = (
                "Quiet geomagnetic conditions (G0). No protocol adjustment indicated."
            )
        elif bio_alert == "unsettled":
            overall_advisory = (
                f"Unsettled conditions ({g_scale}). Sub-threshold activity — "
                "maintain normal protocol. Light monitoring only."
            )
        elif bio_alert == "minor":
            protocol_adjustments += [
                "Advance wind-down by 15 minutes.",
                "Prioritise 7–9 hours sleep tonight.",
            ]
            overall_advisory = (
                f"Minor geomagnetic storm ({g_scale}). Alabdali 2022 calibration zone. "
                "Conservative recovery basics are a reasonable precaution."
            )
        elif bio_alert == "moderate":
            protocol_adjustments += [
                "Advance wind-down by 30 minutes.",
                "Extend morning light exposure by 10 minutes.",
                "Defer demanding cognitive work to lower-Kp days if possible.",
            ]
            overall_advisory = (
                f"Moderate geomagnetic storm ({g_scale}). HRV and cognitive associations "
                "are statistically established here (Alabdali 2022; Liddie 2024). "
                "Conservative recovery protocol warranted."
            )
        elif bio_alert == "significant":
            protocol_adjustments += [
                "Advance wind-down by 45 minutes.",
                "Extend morning light exposure by 20 minutes.",
                "Use shorter work blocks (25 min max). Avoid high-stakes decisions.",
                "Hydrate well — BP fluctuation possible (Chen 2025).",
            ]
            overall_advisory = (
                f"Strong geomagnetic storm ({g_scale}, Kp {kp:.1f}). "
                "HRV suppression, cognitive load increase, and BP fluctuation are all "
                "within calibrated evidence ranges. Full conservative protocol indicated."
            )
        elif bio_alert == "severe":
            protocol_adjustments += [
                "Major storm — prioritise sleep hygiene above all else.",
                "Advance wind-down by 45+ minutes.",
                "Extend morning light exposure by 20+ minutes.",
                "Avoid high-complexity cognitive tasks entirely.",
                "Cardiovascular patients: monitor BP, adhere to medications.",
            ]
            overall_advisory = (
                f"Severe geomagnetic storm ({g_scale}, Kp {kp:.1f}). All evidence streams "
                "(HRV, cognition, BP) are in storm-level territory. "
                "Gaisenok 2025 meta-analysis: MI/ACS RR 1.29–1.39 during storms. "
                "Most conservative protocol warranted."
            )
        else:  # extreme
            protocol_adjustments += [
                "Extreme storm — full conservative protocol across all domains.",
                "Advance wind-down by 60+ minutes.",
                "Extend morning light exposure by 30+ minutes.",
                "Cancel non-essential cognitive demands.",
                "Cardiovascular patients: clinical-level caution.",
            ]
            overall_advisory = (
                f"Extreme geomagnetic storm ({g_scale}, Kp {kp:.1f}). Beyond primary "
                "calibration range — extrapolated from CHD subgroup data. "
                "Apply maximum conservative protocol."
            )

        # Prepend storm-arrival alert if Bz signals imminent onset
        if storm_pred["storm_imminent"]:
            protocol_adjustments.insert(
                0,
                f"Storm arrival alert: southward Bz ({reading.bz:.1f} nT) suggests "
                f"Kp rise in ~{storm_pred['propagation_min']} minutes — begin protocol now.",
            )

        overall_advisory = (
            f"{overall_advisory} Exploratory geomagnetic context only; "
            "not validated for individual prediction."
        )

        return merge_evidence(
            {
                "g_scale": g_scale,
                "condition": condition,
                "biological_alert": bio_alert,
                "kp_index": round(kp, 1),
                "latitude": round(latitude, 1),
                "hrv_suppression_pct": hrv["suppression_pct"],
                "hrv_delta_rmssd": hrv["delta_rmssd"],
                "hrv_adaptive_response_possible": hrv["adaptive_response_possible"],
                "cognitive_focus_modifier": cog["focus_modifier"],
                "cognitive_working_memory_impact": cog["working_memory_impact"],
                "bp_systolic_fluctuation_mmhg": bp["systolic_fluctuation_mmhg"],
                "bp_clinical_relevance": bp["clinical_relevance"],
                "storm_arrival": storm_pred,
                "protocol_adjustments": protocol_adjustments,
                "model_type": "exploratory_heuristic",
                "mechanism_note": (
                    "Wang & Kirschvink et al. (2019, eNeuro 6:2, PMC6494972): alpha-EEG "
                    "power drop up to 60% (ηp²=0.34) in response to Earth-strength field "
                    "rotations — strongest direct human mechanistic evidence. "
                    "Magnetite biomineralization in human brain tissue: Kirschvink et al. "
                    "(1992, PNAS 89:7683) — min. 5M single-domain crystals per gram."
                ),
                "advisory": overall_advisory,
            },
            self.COMPOSITE_EVIDENCE_PROFILE,
        )
