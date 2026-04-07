"""
HELIOS — Napping Science Model
Evidence-based nap recommendations, duration effects, and post-nap protocols.

References:
- Rosekind, M.R. et al. (1995) 'The cost of poor sleep: workplace productivity
  loss and associated costs', J Sleep Research, 4(S2), pp. 62-66.
  (NASA nap study: 26-min nap → +54% alertness, +34% performance)
- Dutheil, F. et al. (2021) 'Nap duration and health: a meta-analysis of
  observational studies', Int J Environ Res Public Health, 18(19), 10212.
- Milner, C.E. & Cote, K.A. (2009) 'Benefits of napping in healthy adults:
  impact of nap length, time of day, age, and experience with napping',
  Sleep Medicine Reviews, 13(2), pp. 145-154.
- Lovato, N. & Lack, L. (2010) 'The effects of napping on cognitive functioning',
  Progress in Brain Research, 185, pp. 155-166.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


# ─── Duration Effects Lookup (Dutheil 2021 meta-analysis) ─────────────────────

@dataclass
class NapDurationProfile:
    """Empirical effects for a given nap duration from Dutheil 2021."""
    duration_min: int
    alertness_boost_min: int
    inertia_min_low: int
    inertia_min_high: int
    includes_sws: bool
    includes_rem: bool
    cognitive_benefit: str


NAP_PROFILES = {
    10: NapDurationProfile(
        duration_min=10,
        alertness_boost_min=155,
        inertia_min_low=0,
        inertia_min_high=1,
        includes_sws=False,
        includes_rem=False,
        cognitive_benefit="Improved alertness and vigilance with near-zero inertia.",
    ),
    20: NapDurationProfile(
        duration_min=20,
        alertness_boost_min=185,
        inertia_min_low=2,
        inertia_min_high=5,
        includes_sws=False,
        includes_rem=False,
        cognitive_benefit="Enhanced alertness and reaction time; minimal inertia.",
    ),
    26: NapDurationProfile(
        duration_min=26,
        alertness_boost_min=180,
        inertia_min_low=5,
        inertia_min_high=10,
        includes_sws=False,
        includes_rem=False,
        cognitive_benefit="NASA protocol: +54% alertness, +34% performance (Rosekind 1995).",
    ),
    30: NapDurationProfile(
        duration_min=30,
        alertness_boost_min=210,
        inertia_min_low=10,
        inertia_min_high=15,
        includes_sws=True,
        includes_rem=False,
        cognitive_benefit="Declarative memory benefit begins; moderate inertia risk.",
    ),
    60: NapDurationProfile(
        duration_min=60,
        alertness_boost_min=360,
        inertia_min_low=15,
        inertia_min_high=30,
        includes_sws=True,
        includes_rem=False,
        cognitive_benefit="Strong declarative memory consolidation via SWS (Lovato & Lack 2010).",
    ),
    90: NapDurationProfile(
        duration_min=90,
        alertness_boost_min=480,
        inertia_min_low=5,
        inertia_min_high=10,
        includes_sws=True,
        includes_rem=True,
        cognitive_benefit="Full sleep cycle with REM — creativity, procedural memory, emotional regulation.",
    ),
}


# ─── Goal-Based Duration Mapping ──────────────────────────────────────────────

GOAL_DURATIONS = {
    "alertness": {"min": 10, "max": 20, "default": 20},
    "memory": {"min": 60, "max": 60, "default": 60},
    "creativity": {"min": 90, "max": 90, "default": 90},
    "recovery": {"min": 90, "max": 90, "default": 90},
}


# ─── Napping Science Engine ──────────────────────────────────────────────────

class NapModel:
    """
    Evidence-based napping recommendation engine.

    Integrates circadian trough timing (post-lunch dip at 13:00-15:00),
    goal-specific durations from Dutheil 2021 meta-analysis, the NASA
    26-minute nap protocol (Rosekind 1995), and post-nap inertia
    countermeasures from Milner & Cote (2009).

    Core heuristics:
    - Optimal nap window: 13:00-15:00 (circadian trough)
    - Latest safe nap: bedtime - 6 hours (avoids night sleep impairment)
    - Should-nap threshold: awake > 6h AND in window AND sleep debt > 0
    - Night sleep impact: naps after 15:00, each hour later = -3-5% efficiency
    """

    @staticmethod
    def recommendation(
        current_time_hours: float,
        wake_time_hours: float,
        sleep_time_hours: float,
        hours_awake: float,
        sleep_debt_hours: float = 0.0,
        goal: str = "alertness",
    ) -> dict:
        """
        Generate a personalized nap recommendation.

        Uses circadian trough timing, sleep pressure, and goal-specific
        durations to decide whether, when, and how long to nap.

        NASA nap special (Rosekind 1995): if goal='alertness' and
        sleep_debt > 2h, recommend exactly 26 min for the scientifically
        validated +54% alertness, +34% performance boost.

        Night sleep impact (Milner & Cote 2009): naps after 15:00
        reduce evening sleep efficiency by 3-5% per hour past 15:00.

        Args:
            current_time_hours: Current time in decimal hours (0-24).
            wake_time_hours: Wake time in decimal hours.
            sleep_time_hours: Bedtime in decimal hours (can be >24 for next-day).
            hours_awake: Hours since waking.
            sleep_debt_hours: Accumulated sleep debt in hours (default 0).
            goal: 'alertness' | 'memory' | 'creativity' | 'recovery'.

        Returns:
            dict with should_nap, optimal_nap_time_hours, recommended_duration_min,
            expected_alertness_boost_hours, sleep_inertia_risk_min,
            night_sleep_impact_pct, latest_safe_nap_hours, advisory.
        """
        # Validate goal
        if goal not in GOAL_DURATIONS:
            return {
                "should_nap": False,
                "optimal_nap_time_hours": None,
                "recommended_duration_min": 0,
                "expected_alertness_boost_hours": 0.0,
                "sleep_inertia_risk_min": 0,
                "night_sleep_impact_pct": 0.0,
                "latest_safe_nap_hours": None,
                "advisory": f"Error: unknown goal '{goal}'. Use: alertness, memory, creativity, recovery.",
            }

        # Normalize sleep_time to be after current_time
        effective_sleep_time = sleep_time_hours
        if effective_sleep_time < current_time_hours:
            effective_sleep_time += 24.0

        # Latest safe nap: bedtime - 6 hours
        latest_safe_nap = effective_sleep_time - 6.0

        # Optimal nap window: 13:00-15:00 (circadian trough)
        nap_window_start = 13.0
        nap_window_end = 15.0

        # Determine optimal nap time (center of available window)
        if current_time_hours <= nap_window_end and latest_safe_nap >= nap_window_start:
            # Window is available
            opt_start = max(current_time_hours, nap_window_start)
            opt_end = min(latest_safe_nap, nap_window_end)
            if opt_start <= opt_end:
                optimal_nap_time = round((opt_start + opt_end) / 2, 1)
            else:
                optimal_nap_time = round(opt_start, 1)
        elif current_time_hours < nap_window_start and latest_safe_nap >= nap_window_start:
            optimal_nap_time = 13.0
        else:
            # Window has passed or not available — use current time if before cutoff
            optimal_nap_time = round(min(current_time_hours, latest_safe_nap), 1)

        # Should-nap heuristic
        in_window = nap_window_start <= current_time_hours <= nap_window_end
        before_cutoff = current_time_hours <= latest_safe_nap
        should_nap = (hours_awake > 6.0) and in_window and (sleep_debt_hours > 0) and before_cutoff

        # Duration by goal
        goal_config = GOAL_DURATIONS[goal]
        recommended_duration = goal_config["default"]

        # NASA nap special: alertness + high sleep debt → 26 min
        if goal == "alertness" and sleep_debt_hours > 2.0:
            recommended_duration = 26

        # Look up duration effects
        closest_profile_key = min(NAP_PROFILES.keys(), key=lambda k: abs(k - recommended_duration))
        profile = NAP_PROFILES[closest_profile_key]

        expected_alertness_boost_hours = round(profile.alertness_boost_min / 60.0, 1)
        sleep_inertia_risk_min = profile.inertia_min_high

        # Night sleep impact: naps after 15:00, each hour later = -3-5% efficiency
        if current_time_hours > 15.0 and before_cutoff:
            hours_past_3pm = current_time_hours - 15.0
            # Average of 3-5% → 4% per hour
            night_sleep_impact_pct = round(hours_past_3pm * 4.0, 1)
        else:
            night_sleep_impact_pct = 0.0

        # Cap impact
        night_sleep_impact_pct = min(night_sleep_impact_pct, 25.0)

        # Generate advisory
        if not should_nap:
            reasons = []
            if hours_awake <= 6.0:
                reasons.append(f"only {hours_awake:.1f}h awake (need >6h)")
            if not in_window:
                reasons.append(f"outside optimal window (13:00-15:00)")
            if sleep_debt_hours <= 0:
                reasons.append("no sleep debt detected")
            if not before_cutoff:
                reasons.append(f"past latest safe nap time ({latest_safe_nap:.1f}h)")
            advisory = f"Nap not recommended — {'; '.join(reasons)}."
        elif recommended_duration == 26:
            advisory = (
                f"NASA nap protocol recommended: 26 min for +54% alertness, +34% performance "
                f"(Rosekind 1995). Sleep debt of {sleep_debt_hours:.1f}h detected. "
                f"Optimal time: {optimal_nap_time:.1f}h ({_format_time(optimal_nap_time)})."
            )
        elif goal == "memory":
            advisory = (
                f"60-min SWS nap recommended for declarative memory consolidation "
                f"(Lovato & Lack 2010). Expect {sleep_inertia_risk_min}-min inertia on waking. "
                f"Optimal time: {_format_time(optimal_nap_time)}."
            )
        elif goal == "creativity":
            advisory = (
                f"90-min full-cycle nap recommended — includes REM for creative insight "
                f"and divergent thinking (Milner & Cote 2009). "
                f"Optimal time: {_format_time(optimal_nap_time)}."
            )
        elif goal == "recovery":
            advisory = (
                f"90-min recovery nap recommended — full sleep cycle with SWS + REM. "
                f"Best for significant sleep debt ({sleep_debt_hours:.1f}h). "
                f"Optimal time: {_format_time(optimal_nap_time)}."
            )
        else:
            advisory = (
                f"{recommended_duration}-min nap recommended for {goal}. "
                f"Optimal time: {_format_time(optimal_nap_time)}. "
                f"Alertness boost: ~{expected_alertness_boost_hours}h (Dutheil 2021)."
            )

        if night_sleep_impact_pct > 0 and should_nap:
            advisory += (
                f" Warning: napping now may reduce tonight's sleep efficiency "
                f"by ~{night_sleep_impact_pct:.0f}% (Milner & Cote 2009)."
            )

        return {
            "should_nap": should_nap,
            "optimal_nap_time_hours": optimal_nap_time,
            "recommended_duration_min": recommended_duration,
            "expected_alertness_boost_hours": expected_alertness_boost_hours,
            "sleep_inertia_risk_min": sleep_inertia_risk_min,
            "night_sleep_impact_pct": night_sleep_impact_pct,
            "latest_safe_nap_hours": round(latest_safe_nap, 1),
            "advisory": advisory,
        }

    @staticmethod
    def duration_effects(duration_min: int) -> dict:
        """
        Look up empirical effects for a given nap duration.

        Data from Dutheil et al. (2021) meta-analysis of nap duration
        and cognitive outcomes, supplemented by Rosekind et al. (1995)
        for the 26-minute NASA protocol.

        Interpolates between known profiles for non-standard durations.

        Args:
            duration_min: Nap duration in minutes.

        Returns:
            dict with alertness_boost_min, sleep_inertia_min, includes_sws,
            includes_rem, cognitive_benefit, advisory.
        """
        # Guard: non-positive duration
        if duration_min <= 0:
            return {
                "alertness_boost_min": 0,
                "sleep_inertia_min": 0,
                "includes_sws": False,
                "includes_rem": False,
                "cognitive_benefit": "None.",
                "advisory": "Error: duration must be positive.",
            }

        # Exact match
        if duration_min in NAP_PROFILES:
            p = NAP_PROFILES[duration_min]
            inertia_avg = (p.inertia_min_low + p.inertia_min_high) // 2

            advisory = (
                f"{duration_min}-min nap: ~{p.alertness_boost_min} min alertness boost, "
                f"{p.inertia_min_low}-{p.inertia_min_high} min inertia risk. "
                f"{p.cognitive_benefit}"
            )

            return {
                "alertness_boost_min": p.alertness_boost_min,
                "sleep_inertia_min": inertia_avg,
                "includes_sws": p.includes_sws,
                "includes_rem": p.includes_rem,
                "cognitive_benefit": p.cognitive_benefit,
                "advisory": advisory,
            }

        # Interpolate between nearest known profiles
        known = sorted(NAP_PROFILES.keys())
        if duration_min < known[0]:
            # Below minimum — scale down from 10-min profile
            p = NAP_PROFILES[known[0]]
            scale = duration_min / known[0]
            boost = int(p.alertness_boost_min * scale)
            advisory = (
                f"{duration_min}-min nap: very short, estimated ~{boost} min alertness boost. "
                f"Consider at least 10 min for reliable benefits (Dutheil 2021)."
            )
            return {
                "alertness_boost_min": boost,
                "sleep_inertia_min": 0,
                "includes_sws": False,
                "includes_rem": False,
                "cognitive_benefit": "Minimal — duration below studied threshold.",
                "advisory": advisory,
            }

        if duration_min > known[-1]:
            # Above maximum — use 90-min profile with warning
            p = NAP_PROFILES[known[-1]]
            advisory = (
                f"{duration_min}-min nap: exceeds one full sleep cycle (90 min). "
                f"May cause significant inertia if waking mid-cycle. "
                f"Consider limiting to 90 min or 180 min (two full cycles)."
            )
            return {
                "alertness_boost_min": p.alertness_boost_min,
                "sleep_inertia_min": (p.inertia_min_low + p.inertia_min_high) // 2,
                "includes_sws": True,
                "includes_rem": True,
                "cognitive_benefit": p.cognitive_benefit,
                "advisory": advisory,
            }

        # Find bounding profiles
        lower_key = max(k for k in known if k <= duration_min)
        upper_key = min(k for k in known if k >= duration_min)
        p_low = NAP_PROFILES[lower_key]
        p_high = NAP_PROFILES[upper_key]

        # Linear interpolation factor
        if upper_key == lower_key:
            t = 0.0
        else:
            t = (duration_min - lower_key) / (upper_key - lower_key)

        boost = int(p_low.alertness_boost_min + t * (p_high.alertness_boost_min - p_low.alertness_boost_min))
        inertia = int(
            ((p_low.inertia_min_low + p_low.inertia_min_high) / 2)
            + t * (((p_high.inertia_min_low + p_high.inertia_min_high) / 2)
                   - ((p_low.inertia_min_low + p_low.inertia_min_high) / 2))
        )

        includes_sws = p_low.includes_sws or p_high.includes_sws
        includes_rem = p_low.includes_rem or p_high.includes_rem

        advisory = (
            f"{duration_min}-min nap (interpolated): ~{boost} min alertness boost, "
            f"~{inertia} min inertia. Falls between {lower_key}-min and {upper_key}-min "
            f"studied durations (Dutheil 2021)."
        )

        return {
            "alertness_boost_min": boost,
            "sleep_inertia_min": inertia,
            "includes_sws": includes_sws,
            "includes_rem": includes_rem,
            "cognitive_benefit": f"Interpolated between {lower_key}-min and {upper_key}-min profiles.",
            "advisory": advisory,
        }

    @staticmethod
    def post_nap_protocol(
        nap_duration_min: int,
        wake_method: str = "natural",
    ) -> dict:
        """
        Generate post-nap inertia countermeasure protocol.

        For naps with >5 min inertia risk, recommends either:
        1. "Coffee nap" — consume caffeine immediately before napping;
           caffeine takes ~20 min to absorb, so it kicks in as you wake
           (Milner & Cote 2009).
        2. Bright light exposure — >5000 lux for 5 min post-nap to
           suppress residual melatonin and accelerate cortical arousal.

        Args:
            nap_duration_min: Planned or completed nap duration in minutes.
            wake_method: 'natural' | 'alarm' | 'coffee_nap'.

        Returns:
            dict with inertia_countermeasure, countermeasure_timing,
            expected_inertia_cleared_min, advisory.
        """
        # Guard: non-positive duration
        if nap_duration_min <= 0:
            return {
                "inertia_countermeasure": "none",
                "countermeasure_timing": "N/A",
                "expected_inertia_cleared_min": 0,
                "advisory": "Error: nap duration must be positive.",
            }

        # Find closest duration profile for inertia estimate
        closest_key = min(NAP_PROFILES.keys(), key=lambda k: abs(k - nap_duration_min))
        profile = NAP_PROFILES[closest_key]
        inertia_risk = profile.inertia_min_high

        if inertia_risk <= 5:
            # Low inertia — no special countermeasure needed
            return {
                "inertia_countermeasure": "none needed",
                "countermeasure_timing": "N/A",
                "expected_inertia_cleared_min": inertia_risk,
                "advisory": (
                    f"A {nap_duration_min}-min nap has low inertia risk "
                    f"({profile.inertia_min_low}-{profile.inertia_min_high} min). "
                    f"No special countermeasure required — alertness returns quickly."
                ),
            }

        # High inertia risk — recommend countermeasures
        if wake_method == "coffee_nap":
            countermeasure = "coffee nap (caffeine before sleep)"
            timing = "Consume 100-200mg caffeine immediately before lying down"
            cleared_min = max(1, inertia_risk - 10)
            advisory = (
                f"Coffee nap protocol: drink coffee then nap for {nap_duration_min} min. "
                f"Caffeine absorbs in ~20 min (Milner & Cote 2009), reaching peak effect "
                f"as you wake. Expected inertia reduced from {inertia_risk} min to ~{cleared_min} min."
            )
        else:
            # Default: bright light
            countermeasure = "bright light exposure (>5000 lux)"
            timing = "Immediately upon waking, expose to bright light for 5 min"
            cleared_min = max(2, inertia_risk - 8)
            advisory = (
                f"A {nap_duration_min}-min nap carries {profile.inertia_min_low}-{profile.inertia_min_high} min "
                f"inertia risk. Bright light >5000 lux for 5 min post-nap suppresses "
                f"residual melatonin and accelerates cortical arousal. "
                f"Expected inertia reduced to ~{cleared_min} min. "
                f"Alternative: try a 'coffee nap' — consume caffeine before sleeping "
                f"(set wake_method='coffee_nap')."
            )

        return {
            "inertia_countermeasure": countermeasure,
            "countermeasure_timing": timing,
            "expected_inertia_cleared_min": cleared_min,
            "advisory": advisory,
        }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _format_time(decimal_hours: float) -> str:
    """Convert decimal hours (e.g., 14.5) to HH:MM string."""
    h = int(decimal_hours) % 24
    m = int((decimal_hours % 1) * 60)
    return f"{h:02d}:{m:02d}"


# ─── Example Usage ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = NapModel()

    print("=" * 60)
    print("HELIOS Nap Model — Example Scenarios")
    print("=" * 60)

    # 1. It's 2 PM, woke at 7 AM (7h awake), 1h sleep debt, goal=alertness
    print("\n--- Scenario 1: Afternoon alertness nap ---")
    rec = model.recommendation(
        current_time_hours=14.0,
        wake_time_hours=7.0,
        sleep_time_hours=23.0,
        hours_awake=7.0,
        sleep_debt_hours=1.0,
        goal="alertness",
    )
    print(f"Should nap: {rec['should_nap']}")
    print(f"Optimal nap time: {_format_time(rec['optimal_nap_time_hours'])}")
    print(f"Recommended duration: {rec['recommended_duration_min']} min")
    print(f"Alertness boost: ~{rec['expected_alertness_boost_hours']}h")
    print(f"Inertia risk: {rec['sleep_inertia_risk_min']} min")
    print(f"Night sleep impact: {rec['night_sleep_impact_pct']}%")
    print(f"Latest safe nap: {_format_time(rec['latest_safe_nap_hours'])}")
    print(f"Advisory: {rec['advisory']}")

    # 2. Duration effects comparison: 10 vs 26 vs 90 min
    print("\n--- Scenario 2: Duration effects comparison ---")
    for dur in [10, 26, 90]:
        effects = model.duration_effects(dur)
        print(f"\n  {dur}-min nap:")
        print(f"    Alertness boost: {effects['alertness_boost_min']} min")
        print(f"    Sleep inertia: {effects['sleep_inertia_min']} min")
        print(f"    Includes SWS: {effects['includes_sws']}")
        print(f"    Includes REM: {effects['includes_rem']}")
        print(f"    Cognitive benefit: {effects['cognitive_benefit']}")
        print(f"    Advisory: {effects['advisory']}")

    # 3. Post-nap protocol for a 60-min nap
    print("\n--- Scenario 3: Post-nap protocol (60-min nap) ---")
    protocol = model.post_nap_protocol(nap_duration_min=60, wake_method="natural")
    print(f"Countermeasure: {protocol['inertia_countermeasure']}")
    print(f"Timing: {protocol['countermeasure_timing']}")
    print(f"Expected inertia cleared: {protocol['expected_inertia_cleared_min']} min")
    print(f"Advisory: {protocol['advisory']}")

    # Bonus: coffee nap variant
    print("\n--- Scenario 3b: Coffee nap protocol (60-min nap) ---")
    protocol_coffee = model.post_nap_protocol(nap_duration_min=60, wake_method="coffee_nap")
    print(f"Countermeasure: {protocol_coffee['inertia_countermeasure']}")
    print(f"Timing: {protocol_coffee['countermeasure_timing']}")
    print(f"Expected inertia cleared: {protocol_coffee['expected_inertia_cleared_min']} min")
    print(f"Advisory: {protocol_coffee['advisory']}")
