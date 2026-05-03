"""
HELIOS — Supplement Model
Evidence-graded supplement ranking for sleep, recovery, and circadian realignment.

Covers four supplements with the strongest human RCT evidence bases:
  melatonin   — circadian phase shifting and jet-lag support
  magnesium   — sleep quality, HRV recovery, GABA modulation
  ashwagandha — cortisol / stress-axis adaptation (KSM-66 extract)
  glycine     — sleep onset, core body temperature reduction

References:
- Ferracioli-Oda, E. et al. (2013) 'Meta-analysis: melatonin for the treatment
  of primary sleep disorders', PLoS ONE, 8(5), e63773.
- Buscemi, N. et al. (2006) 'Efficacy and safety of exogenous melatonin for
  secondary sleep disorders', BMJ, 332(7538), pp. 385-393.
- Abbasi, B. et al. (2012) 'The effect of magnesium supplementation on primary
  insomnia in elderly', J Research Medical Sciences, 17(12), pp. 1161-1169.
  (Sleep time +17 min, sleep efficiency +12.5%, ISI –3 pts)
- Chandrasekhar, K. et al. (2012) 'A prospective, randomized double-blind,
  placebo-controlled study of Ashwagandha root extract (KSM-66)',
  Indian J Psychological Medicine, 34(3), pp. 255-262.
  (Cortisol −27.9%, PSS score −5.4 pts)
- Bannai, M. and Kawai, N. (2012) 'New therapeutic strategy for amino acid medicine:
  glycine improves the quality of sleep', J Pharmacological Sciences, 118(2), pp. 145-148.
  (3g glycine: sleep latency −9 min, daytime fatigue −12%, core temp −0.3°C)
- Kawai, N. et al. (2015) 'The sleep-promoting and hypothermic effects of glycine
  are mediated by NMDA receptors in the SCN', Neuropsychopharmacology, 40(6), pp. 1405-1416.
"""

from typing import Literal, Optional

from research.evidence_contract import EvidenceProfile, merge_evidence


SupplementKey  = Literal["melatonin", "magnesium", "ashwagandha", "glycine"]
SupplementGoal = Literal[
    "sleep_onset",
    "recovery_support",
    "stress_resilience",
    "jet_lag_support",
    "circadian_realignment",
]
Chronotype  = Literal["early", "mid", "late"]
TravelState = Literal["none", "eastbound_shift", "westbound_shift"]


SUPPLEMENT_EVIDENCE_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="Contextual supplement ranking for sleep, recovery, and circadian realignment goals",
    population_summary="Healthy adults; RCTs for each supplement are independent — combined ranking is model-derived",
    main_caveat="Effect sizes are supplement-specific; individual response, dose optimisation, and drug interactions not modelled",
    uncertainty_factors=["individual pharmacokinetics", "baseline nutrient status", "drug interactions", "dose compliance"],
    claim_boundary="Use as a priority-ordering guide, not a clinical prescription",
)


# ─── Supplement Catalog (static metadata) ─────────────────────────────────────

_CATALOG: dict[str, dict] = {
    "melatonin": {
        "name": "Melatonin",
        "dose": "0.5–1 mg",
        "timing": "30–60 min before target sleep time",
        "mechanism": (
            "Exogenous melatonin signals the SCN to advance or delay the circadian clock "
            "depending on dosing time relative to DLMO. "
            "Buscemi 2006: sleep-onset latency −7.2 min (95% CI −9.0 to −5.4)."
        ),
        "evidence_tier": "strong",
    },
    "magnesium": {
        "name": "Magnesium Glycinate",
        "dose": "200–400 mg elemental Mg",
        "timing": "30–60 min before bed",
        "mechanism": (
            "GABA-A agonism reduces sleep-onset latency; NMDA antagonism dampens nocturnal arousal. "
            "Abbasi 2012 RCT: sleep time +17 min, sleep efficiency +12.5%, ISI score −3 pts (n=46)."
        ),
        "evidence_tier": "moderate",
    },
    "ashwagandha": {
        "name": "Ashwagandha (KSM-66)",
        "dose": "300–600 mg KSM-66 extract",
        "timing": "Morning or with evening meal",
        "mechanism": (
            "Withanolides reduce hypothalamic-pituitary-adrenal (HPA) axis reactivity. "
            "Chandrasekhar 2012 RCT: serum cortisol −27.9%, PSS score −5.4 pts vs. placebo (n=64, 60 days)."
        ),
        "evidence_tier": "moderate",
    },
    "glycine": {
        "name": "Glycine",
        "dose": "3 g",
        "timing": "30 min before bed",
        "mechanism": (
            "Activates NMDA receptors in the SCN to lower core body temperature (−0.3°C), "
            "promoting faster sleep onset. "
            "Bannai 2012: sleep latency −9 min, daytime fatigue −12%, PSG-confirmed slow-wave increase."
        ),
        "evidence_tier": "moderate",
    },
}

# Tie-break order when scores are equal — goal-specific priority
_TIE_BREAK: dict[str, list[str]] = {
    "sleep_onset":           ["glycine", "melatonin", "magnesium", "ashwagandha"],
    "recovery_support":      ["magnesium", "ashwagandha", "glycine", "melatonin"],
    "stress_resilience":     ["ashwagandha", "magnesium", "glycine", "melatonin"],
    "jet_lag_support":       ["melatonin", "magnesium", "glycine", "ashwagandha"],
    "circadian_realignment": ["melatonin", "magnesium", "glycine", "ashwagandha"],
}


# ─── Signal Helpers ───────────────────────────────────────────────────────────

def _low_hrv(hrv: Optional[float]) -> bool:
    return hrv is not None and hrv < 40

def _low_sleep_score(sleep_score: Optional[float]) -> bool:
    return sleep_score is not None and sleep_score < 75

def _short_sleep(total_sleep_hours: Optional[float]) -> bool:
    return total_sleep_hours is not None and total_sleep_hours < 6.5


# ─── Scoring Functions ────────────────────────────────────────────────────────

def _score_melatonin(
    goal: str,
    chronotype: str,
    travel_state: str,
    hrv: Optional[float],
    sleep_score: Optional[float],
    total_sleep_hours: Optional[float],
) -> tuple[int, str]:
    score = 0
    if travel_state == "eastbound_shift":
        score += 3
    if travel_state == "westbound_shift":
        score += 2
    if goal in ("circadian_realignment", "jet_lag_support") and travel_state != "none":
        score += 2
    if goal == "sleep_onset" and (_low_sleep_score(sleep_score) or _short_sleep(total_sleep_hours)):
        score += 1
    if chronotype == "late" and travel_state == "eastbound_shift":
        score += 1
    if (_low_sleep_score(sleep_score) or _short_sleep(total_sleep_hours)) and travel_state != "none":
        score += 1
    score = min(5, score)

    has_circadian_shift = travel_state != "none" or goal in ("circadian_realignment", "jet_lag_support")
    if goal == "circadian_realignment" and travel_state == "eastbound_shift" and chronotype == "late":
        note = "Eastbound phase advance plus a late chronotype makes melatonin the most relevant circadian tool here."
    elif goal == "jet_lag_support" and travel_state != "none":
        note = (
            "Travel-related phase advance makes melatonin more relevant for resetting timing after an eastbound shift."
            if travel_state == "eastbound_shift"
            else "Travel-related timing disruption still makes melatonin relevant, but westbound shifts usually lean less heavily on it."
        )
    elif goal == "sleep_onset":
        note = "Melatonin may help sleep onset, but is most useful when bedtime timing itself needs support."
    elif score > 0 and has_circadian_shift:
        note = "Circadian timing inputs make melatonin more relevant than a generic sleep aid."
    else:
        note = "No strong circadian signal is present, so melatonin stays a lower-priority wellness option."

    return score, note


def _score_magnesium(
    goal: str,
    hrv: Optional[float],
    sleep_score: Optional[float],
    total_sleep_hours: Optional[float],
) -> tuple[int, str]:
    score = 0
    low_hrv = _low_hrv(hrv)
    low_ss = _low_sleep_score(sleep_score)
    short_s = _short_sleep(total_sleep_hours)
    recovery_signal = low_hrv or low_ss or short_s

    if low_hrv:
        score += 2
    if low_ss:
        score += 2
    if short_s:
        score += 1
    if goal == "recovery_support" and recovery_signal:
        score += 2
    if goal == "sleep_onset" and (low_ss or short_s):
        score += 1
    score = min(5, score)

    if low_hrv and (low_ss or short_s):
        note = "Lower HRV plus shorter or lower-quality sleep makes magnesium the clearest recovery-oriented option."
    elif low_hrv:
        note = "Lower HRV makes magnesium more relevant as a recovery-support option."
    elif low_ss or short_s:
        note = "Short sleep or lower sleep quality keeps magnesium relevant when recovery debt is part of the picture."
    elif score > 0:
        note = "Magnesium stays relevant when recovery markers start to drift down."
    else:
        note = "Recovery markers look reasonably steady, so magnesium remains a general wellness option rather than a priority."

    return score, note


def _score_ashwagandha(
    goal: str,
    hrv: Optional[float],
    sleep_score: Optional[float],
) -> tuple[int, str]:
    score = 0
    low_hrv = _low_hrv(hrv)
    low_ss = _low_sleep_score(sleep_score)

    if low_hrv:
        score += 2
    if low_ss and low_hrv:
        score += 1
    if goal == "stress_resilience" and low_hrv:
        score += 2
    if goal == "recovery_support" and low_hrv:
        score += 1
    score = min(5, score)

    if goal == "stress_resilience" and low_hrv:
        note = "Stress resilience plus lower HRV makes ashwagandha more relevant than a pure sleep aid."
    elif low_hrv:
        note = "Lower HRV suggests a stress-adaptation pattern where ashwagandha may be more relevant."
    elif goal == "stress_resilience":
        note = "Ashwagandha is the most stress-oriented option here, framed as general wellness support."
    elif score > 0:
        note = "Stress-adaptation inputs give ashwagandha some relevance, but it remains secondary to stronger goal matches."
    else:
        note = "There is no strong stress signal in the current inputs, so ashwagandha stays lower priority."

    return score, note


def _score_glycine(
    goal: str,
    sleep_score: Optional[float],
    total_sleep_hours: Optional[float],
) -> tuple[int, str]:
    score = 0
    low_ss = _low_sleep_score(sleep_score)
    short_s = _short_sleep(total_sleep_hours)
    onset_signal = low_ss or short_s

    if low_ss:
        score += 1
    if short_s:
        score += 1
    if goal == "sleep_onset" and onset_signal:
        score += 2
    score = min(5, score)

    if goal == "sleep_onset" and onset_signal:
        note = "Sleep-onset framing fits glycine best when falling asleep is the main bottleneck."
    elif goal == "sleep_onset":
        note = "Glycine is the most onset-oriented option, especially when falling asleep is the main issue."
    elif score > 0:
        note = "Glycine can help with sleep onset, but does not address recovery debt as strongly as magnesium."
    else:
        note = "Without a clear sleep-onset problem, glycine stays a lower-priority wellness option."

    return score, note


# ─── Public API ───────────────────────────────────────────────────────────────

def rank_supplements(
    goal: str = "sleep_onset",
    chronotype: str = "mid",
    travel_state: str = "none",
    hrv: Optional[float] = None,
    sleep_score: Optional[float] = None,
    total_sleep_hours: Optional[float] = None,
) -> dict:
    """
    Return all four supplements ranked by contextual relevance score (0–5).
    Ties broken by goal-specific priority order.

    Args:
        goal: One of sleep_onset / recovery_support / stress_resilience /
              jet_lag_support / circadian_realignment.
        chronotype: 'early' | 'mid' | 'late'.
        travel_state: 'none' | 'eastbound_shift' | 'westbound_shift'.
        hrv: Average HRV rMSSD (ms) — optional biometric context.
        sleep_score: Average sleep score 0–100 — optional biometric context.
        total_sleep_hours: Average total sleep hours — optional biometric context.

    Returns:
        dict with supplements list (sorted by score desc), goal, personalized flag,
        and evidence_profile.
    """
    tie_break = _TIE_BREAK.get(goal, list(_CATALOG.keys()))

    scorers = {
        "melatonin":   lambda: _score_melatonin(goal, chronotype, travel_state, hrv, sleep_score, total_sleep_hours),
        "magnesium":   lambda: _score_magnesium(goal, hrv, sleep_score, total_sleep_hours),
        "ashwagandha": lambda: _score_ashwagandha(goal, hrv, sleep_score),
        "glycine":     lambda: _score_glycine(goal, sleep_score, total_sleep_hours),
    }

    scored: list[tuple[str, int, int, str]] = []
    for key in _CATALOG:
        score, note = scorers[key]()
        priority = tie_break.index(key) if key in tie_break else 99
        scored.append((key, score, priority, note))

    scored.sort(key=lambda x: (-x[1], x[2]))

    supplements = []
    for i, (key, score, _priority, note) in enumerate(scored):
        meta = _CATALOG[key]
        supplements.append({
            "key": key,
            "name": meta["name"],
            "dose": meta["dose"],
            "timing": meta["timing"],
            "mechanism": meta["mechanism"],
            "evidence_tier": meta["evidence_tier"],
            "score": score,
            "note": note,
            "is_top_pick": (i == 0 and score > 0),
        })

    payload = {
        "goal": goal,
        "personalized": hrv is not None or sleep_score is not None or total_sleep_hours is not None,
        "supplements": supplements,
    }

    return merge_evidence(payload, SUPPLEMENT_EVIDENCE_PROFILE)
