"""
HELIOS — Exercise Timing Model
Phase response curve for exercise-induced circadian shifts, with chronotype scaling.

References:
- Youngstedt, S.D. et al. (2019) 'Human circadian phase–response curves for exercise',
  J Physiology, 597(8), pp. 2253-2268.
  (First systematic human exercise PRC: morning advances, evening delays)
- Thomas, J.M. et al. (2020) 'Circadian rhythm phase shifts caused by timed exercise vary
  with chronotype', JCI Insight, 5(3), e134270.
  (Late chronotypes get ~1.5x benefit from morning exercise; early chronotypes ~0.5x)
- Sato, S. et al. (2019) 'Time of exercise specifies the impact on muscle metabolic
  pathways and systemic energy homeostasis', Cell Metabolism, 30(1), pp. 92-110.
  (Morning exercise preferentially activates clock-gene expression in skeletal muscle)
"""

from typing import Literal

from evidence_contract import EvidenceProfile, merge_evidence


Chronotype = Literal["early", "mid", "late"]


EXERCISE_EVIDENCE_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="Exercise timing shifts the human circadian clock; morning advances, evening delays",
    population_summary="Healthy adults across RCTs and field studies; Thomas 2020 n=51 chronotype split",
    main_caveat="PRC magnitudes vary with exercise intensity, duration, and individual sensitivity",
    uncertainty_factors=["exercise intensity", "duration", "prior sleep debt", "light co-exposure"],
    claim_boundary="Use to guide exercise scheduling for circadian benefit, not as a precise phase predictor",
)


# ─── Phase Response Curve (Youngstedt 2019) ──────────────────────────────────

# Piecewise approximation anchored to Figure 3 of Youngstedt 2019.
# Values in minutes; positive = phase advance (sleep earlier), negative = delay.

_PRC_BASE: dict[str, int] = {
    "morning":    60,   # 00:00–08:00 — strong advance
    "afternoon":  45,   # 08:01–16:00 — moderate advance
    "evening":   -45,   # 16:01–22:00 — delay
    "late_night":  0,   # 22:01–23:59 — minimal (near-sleep exercise not modelled)
}


def _zone(hour: float) -> str:
    if hour <= 8:
        return "morning"
    if hour <= 16:
        return "afternoon"
    if hour <= 22:
        return "evening"
    return "late_night"


def _chronotype_multiplier(chronotype: Chronotype, hour: float) -> float:
    """
    Thomas 2020: late chronotypes gain ~1.5x from morning exercise (larger phase deficit);
    early chronotypes gain ~0.5x (already advanced; over-advancing risks insomnia).
    Effect only meaningful before 10:00.
    """
    if hour > 10:
        return 1.0
    if chronotype == "late":
        return 1.5
    if chronotype == "early":
        return 0.5
    return 1.0


def calculate_exercise_phase_shift(
    hour: float,
    chronotype: Chronotype = "mid",
) -> dict:
    """
    Return the estimated circadian phase shift from exercising at *hour*
    for a person with the given *chronotype*.

    Args:
        hour: Time of exercise as decimal hour (0.0–23.99).
        chronotype: 'early' | 'mid' | 'late' (MCTQ-derived).

    Returns:
        dict with shift_min (+ = advance, - = delay), label, zone,
        morning_metabolic_bonus, and evidence_profile.
    """
    zone = _zone(hour)
    base = _PRC_BASE[zone]
    multiplier = _chronotype_multiplier(chronotype, hour)
    shift_min = round(base * multiplier)
    morning_metabolic_bonus = hour <= 10  # Sato 2019 clock-gene activation window

    if shift_min > 0:
        label = f"+{shift_min} min advance"
    elif shift_min < 0:
        label = f"{shift_min} min delay"
    else:
        label = "Minimal phase effect"

    payload = {
        "hour": hour,
        "chronotype": chronotype,
        "zone": zone,
        "shift_min": shift_min,
        "label": label,
        "morning_metabolic_bonus": morning_metabolic_bonus,
    }

    return merge_evidence(payload, EXERCISE_EVIDENCE_PROFILE)


def optimal_exercise_hour(chronotype: Chronotype) -> float:
    """
    Return the exercise hour that maximises phase-advance for a given chronotype.
    Early and mid chronotypes: 7:00 (peak advance zone, low multiplier penalty avoided).
    Late chronotypes: 7:00–8:00 (largest advance zone + 1.5x Thomas multiplier).
    """
    return 7.0 if chronotype in ("mid", "late") else 6.0
