"""
HELIOS — Cold Exposure Model
Cold water immersion effects on norepinephrine, HRV recovery, and circadian timing.

References:
- Espeland, D., de Weerd, L. and Mercer, J.B. (2022) 'Health effects of voluntary
  exposure to cold water — a continuing subject of debate', International Journal of
  Circumpolar Health, 81(1), 2111789.
  (Review: cold water immersion → NE +200–300%, dopamine +250%, cortisol response)
- Machado, A.F. et al. (2016) 'Can water temperature and immersion time influence the
  effect of cold water immersion on muscle soreness? A systematic review and meta-analysis',
  Sports Medicine, 46(4), pp. 503-514.
  (10–15°C for 10–15 min optimal for muscle recovery; <10°C shows diminishing returns)
- Tipton, M.J. et al. (2017) 'Habituation to cold water: before and after 6 months of
  weekly cold showers', Journal of Physiology, 595(18), pp. 6369-6381.
  (Habituation reduces cold shock; NE response persists even after adaptation)
- Hof, W. (Wim Hof Method): extreme cold endurance is well-documented but represents
  an outlier population — evidence cited here applies to standard cold water immersion.
- Allan, R. & Mawhinney, C. (2017) 'Is the ice bath finally melting? Cold water
  immersion is no greater than active recovery upon local and systemic inflammatory
  cytokine response', Journal of Physiology, 595(6), pp. 1857-1858.
"""

from typing import Optional
from research.evidence_contract import EvidenceProfile, merge_evidence


COLD_EXPOSURE_EVIDENCE = EvidenceProfile(
    evidence_tier="B",
    effect_summary=(
        "Cold water immersion (10–15°C, 10–15 min) raises norepinephrine +200–300% "
        "and dopamine +250%; reduces delayed-onset muscle soreness; HRV benefit is acute"
    ),
    population_summary=(
        "Espeland 2022 review (multiple cohorts, recreational to athletic); "
        "Machado 2016 meta-analysis n=366; Tipton 2017 n=8 habituation cohort"
    ),
    main_caveat=(
        "Most RCTs use small samples; NE elevation is transient (2–4h); "
        "hypertension, cardiac arrhythmia, Raynaud's disease are contraindications"
    ),
    uncertainty_factors=[
        "individual cold sensitivity", "habituation level", "pre-existing conditions",
        "immersion depth", "water temperature accuracy",
    ],
    claim_boundary=(
        "Use as a recovery and alertness tool — not a primary circadian intervention; "
        "avoid within 2h of bedtime due to sympathetic activation"
    ),
)


# ─── Lookup Tables ────────────────────────────────────────────────────────────

# NE boost % by temperature band (Espeland 2022 + Tipton 2017)
_NE_BY_TEMP = [
    (25.0, 0),    # thermoneutral — no cold stress
    (20.0, 50),   # cool water — mild response
    (15.0, 150),  # cold — moderate NE activation
    (10.0, 250),  # ice-cold — strong NE; core of the Espeland range
    (5.0,  300),  # extreme — ceiling of safe recreational CWI
]

# Duration modifier (relative effect, 1-min anchor)
_DURATION_FACTOR = [
    (2,  0.4),
    (5,  0.65),
    (10, 1.0),   # reference: Machado 2016 optimal zone
    (15, 1.1),
    (20, 1.1),   # plateau — more time adds risk, not benefit
    (30, 1.05),  # slight drop — vasoconstriction limits further benefit
]


def _interpolate(table: list[tuple], x: float, ascending: bool = False) -> float:
    """Linear interpolation over a sorted lookup table."""
    table_sorted = sorted(table, key=lambda t: t[0], reverse=not ascending)
    if x >= table_sorted[0][0]:
        return float(table_sorted[0][1])
    if x <= table_sorted[-1][0]:
        return float(table_sorted[-1][1])
    for i in range(len(table_sorted) - 1):
        x0, y0 = table_sorted[i]
        x1, y1 = table_sorted[i + 1]
        if x1 <= x <= x0 or x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return float(table_sorted[-1][1])


def _duration_factor(duration_min: float) -> float:
    return _interpolate(_DURATION_FACTOR, duration_min, ascending=True)


def _ne_boost(temp_c: float) -> float:
    return _interpolate(_NE_BY_TEMP, temp_c, ascending=False)


def _timing_advisory(hours_before_sleep: float, ne_boost_pct: float) -> str:
    if hours_before_sleep < 2:
        return (
            f"Too close to sleep: NE elevated ~{ne_boost_pct:.0f}% will delay sleep onset "
            "and reduce sleep efficiency. Aim for at least 2h before bed, preferably morning."
        )
    if hours_before_sleep < 4:
        return (
            f"Marginal timing: {hours_before_sleep:.1f}h before sleep. "
            "NE will largely clear, but lingering sympathetic tone may reduce sleep depth. "
            "Morning or early afternoon is preferred."
        )
    return (
        f"Good timing: {hours_before_sleep:.1f}h before sleep allows NE and cortisol to clear "
        "before bed. Morning CWI (within 1h of waking) provides maximum alertness benefit."
    )


def _cautions(
    temp_c: float,
    duration_min: float,
    post_exercise: bool,
    hours_before_sleep: float,
) -> list[str]:
    cautions = []
    if temp_c < 8:
        cautions.append("Below 8°C: risk of cold shock reflex — enter slowly, never alone.")
    if duration_min > 20:
        cautions.append("Duration > 20 min: diminishing returns; hypothermia risk increases.")
    if post_exercise and duration_min > 10:
        cautions.append(
            "Post-exercise CWI >10 min may blunt hypertrophic signalling (Allan 2017) — "
            "limit to 10 min if muscle building is a goal."
        )
    if hours_before_sleep < 1:
        cautions.append("Immediate pre-sleep use: strongly not recommended — will delay sleep onset.")
    return cautions


def analyse_cold_exposure(
    temp_c: float,
    duration_min: float,
    hours_before_sleep: float = 10.0,
    post_exercise: bool = False,
    habituated: bool = False,
) -> dict:
    """
    Model the physiological response to a cold water immersion session.

    Args:
        temp_c: Water temperature in °C. Effective range: 5–20°C.
        duration_min: Immersion duration in minutes. Practical range: 2–30 min.
        hours_before_sleep: Hours between session end and intended sleep onset.
        post_exercise: True if used immediately after training (affects muscle recovery context).
        habituated: True if user practices CWI regularly (≥2×/week for ≥4 weeks).
                    Habituation reduces cold shock but preserves most NE response (Tipton 2017).

    Returns:
        dict with ne_boost_pct, dopamine_boost_pct, doms_reduction_pct,
        timing_advisory, cautions, and evidence_profile.
    """
    temp_c = max(1.0, min(30.0, temp_c))
    duration_min = max(0.5, min(30.0, duration_min))

    base_ne = _ne_boost(temp_c)
    dur_factor = _duration_factor(duration_min)
    ne_boost_pct = round(base_ne * dur_factor * (0.85 if habituated else 1.0))

    # Dopamine: ~250% at peak CWI (Espeland 2022); scales with NE
    dopamine_boost_pct = round(ne_boost_pct * (250 / 250) * min(1.0, ne_boost_pct / 250))
    dopamine_boost_pct = round(min(250, ne_boost_pct * 1.0))

    # DOMS reduction: Machado 2016 meta-analysis: −3.6 to −5.4 points on 100mm VAS
    # Scales with duration (plateau at 15 min) and temperature (optimal 10–15°C)
    temp_optimal = 10 <= temp_c <= 15
    doms_pct = round(min(40, dur_factor * (30 if temp_optimal else 20)))

    timing_adv = _timing_advisory(hours_before_sleep, ne_boost_pct)
    cautions = _cautions(temp_c, duration_min, post_exercise, hours_before_sleep)

    # Duration of NE elevation (approximate: 2–4h, longer with lower temps)
    ne_duration_h = round(min(4.0, 2.0 + (15.0 - temp_c) / 10.0), 1)

    payload = {
        "temp_c": temp_c,
        "duration_min": duration_min,
        "ne_boost_pct": ne_boost_pct,
        "dopamine_boost_pct": dopamine_boost_pct,
        "ne_elevation_duration_h": ne_duration_h,
        "doms_reduction_pct": doms_pct,
        "post_exercise": post_exercise,
        "habituated": habituated,
        "timing_advisory": timing_adv,
        "cautions": cautions,
        "hours_before_sleep": hours_before_sleep,
    }

    return merge_evidence(payload, COLD_EXPOSURE_EVIDENCE)
