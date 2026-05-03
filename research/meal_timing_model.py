"""
HELIOS — Meal Timing Model
Time-restricted feeding scoring, peripheral clock alignment, and glucose benefit estimates.

References:
- Sutton, E.F. et al. (2018) 'Early time-restricted feeding improves insulin sensitivity,
  blood pressure, and oxidative stress even without weight loss in men with prediabetes',
  Cell Metabolism, 27(6), pp. 1212-1221.
- Manoogian, E.N.C. et al. (2022) 'Improving adherence to healthy eating patterns,
  our ancestral diet, and timing', J Biological Rhythms, 37(1), pp. 3-14.
  (+10–15% glucose tolerance improvement with ≤10h eating window)
- Wilkinson, M.J. et al. (2020) '10-Hour time-restricted eating reduces weight,
  blood pressure, and atherogenic lipids in patients with metabolic syndrome',
  Cell Metabolism, 31(1), pp. 92-104.
- Jakubowicz, D. et al. (2013) 'High caloric intake at breakfast vs. dinner
  differentially influences weight loss', Obesity, 21(12), pp. 2504-2512.
"""

from research.evidence_contract import EvidenceProfile, merge_evidence


MEAL_EVIDENCE_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="≤10h eating window improves glucose tolerance +10–15% independent of caloric restriction",
    population_summary="Adults with and without metabolic syndrome; Sutton 2018 n=11; Wilkinson 2020 n=19; Manoogian 2022 review",
    main_caveat="Most trials are small and short-duration; individual variance in circadian phase may shift ideal window",
    uncertainty_factors=["window alignment with chronotype", "caloric density", "macronutrient timing", "sleep quality"],
    claim_boundary="Score reflects evidence-based TRF targets; individual metabolic response may vary",
)


def calculate_meal_window(
    first_meal_hour: float,
    last_meal_hour: float,
    sleep_hour: float,
) -> dict:
    """
    Score a time-restricted feeding window against peer-reviewed benchmarks.

    Args:
        first_meal_hour:  First food/calorie intake as decimal hour (e.g. 8.0).
        last_meal_hour:   Last caloric intake as decimal hour (e.g. 19.5).
        sleep_hour:       Sleep onset as decimal hour (e.g. 23.0). Must be > last_meal_hour.

    Returns:
        dict with score (0–100), window_hours, hours_before_sleep, early_trf,
        glucose_benefit, and evidence_profile.
        On validation failure: {"valid": False, "error": "..."}.

    Scoring breakdown (max 100):
        Window width (40 pts):  ≤10h → 40, ≤12h → 25, ≤14h → 10, >14h → 0
        First meal timing (30): 07:00–09:00 → 30, 09:01–11:00 → 15, >11:00 → 0
        Pre-sleep gap (30):     ≥3h → 30, ≥2h → 15, <2h → 0
    """
    if last_meal_hour <= first_meal_hour:
        return {"valid": False, "error": "Last meal must be after first meal (same-day times)."}

    if sleep_hour <= last_meal_hour:
        return {
            "valid": False,
            "error": "Sleep time must be after last meal. Use same-day times: first meal < last meal < sleep.",
        }

    window_hours = last_meal_hour - first_meal_hour
    hours_before_sleep = sleep_hour - last_meal_hour
    early_trf = first_meal_hour <= 9 and last_meal_hour <= 14

    # Window width component (Manoogian 2022 / Wilkinson 2020)
    if window_hours <= 10:
        window_score = 40
    elif window_hours <= 12:
        window_score = 25
    elif window_hours <= 14:
        window_score = 10
    else:
        window_score = 0

    # First-meal timing component (Jakubowicz 2013 / Sutton 2018 eTRF)
    if 7 <= first_meal_hour <= 9:
        timing_score = 30
    elif first_meal_hour <= 11:
        timing_score = 15
    else:
        timing_score = 0

    # Pre-sleep gap component (peripheral clock alignment)
    if hours_before_sleep >= 3:
        gap_score = 30
    elif hours_before_sleep >= 2:
        gap_score = 15
    else:
        gap_score = 0

    score = window_score + timing_score + gap_score
    glucose_benefit = "+10–15% glucose tolerance (Manoogian 2022)" if window_hours <= 10 else None

    payload = {
        "valid": True,
        "window_hours": round(window_hours, 2),
        "hours_before_sleep": round(hours_before_sleep, 2),
        "score": score,
        "early_trf": early_trf,
        "glucose_benefit": glucose_benefit,
    }

    return merge_evidence(payload, MEAL_EVIDENCE_PROFILE)
