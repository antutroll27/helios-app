"""
HELIOS — Breathwork HRV Response Model
Personalized breathwork technique selection, HRV response prediction, and session planning.

References:
- Laborde, S. et al. (2022) 'Effects of slow-paced breathing on heart rate variability:
  a meta-analysis', Neuroscience & Biobehavioral Reviews, 138, 104711.
- Zaccaro, A. et al. (2018) 'How breath-control can change your life: a systematic
  review on psycho-physiological correlates of slow breathing', Frontiers in Human
  Neuroscience, 12, 353.
- Van Diest, I. et al. (2014) 'Inhalation/exhalation ratio modulates the effect of
  slow breathing on heart rate variability and relaxation', Applied Psychophysiology
  and Biofeedback, 39(3-4), pp. 171-180.
- Lehrer, P.M. & Gevirtz, R. (2014) 'Heart rate variability biofeedback: how and
  why does it work?', Frontiers in Psychology, 5, 756.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

from research.evidence_contract import EvidenceProfile, merge_evidence


@dataclass
class BreathworkSession:
    """Single breathwork session parameters."""
    technique: str              # 'resonance', 'box', '4-7-8', 'coherent'
    breaths_per_min: float      # respiratory rate
    duration_min: float         # session length in minutes
    inhale_exhale_ratio: float  # e.g. 0.5 = 1:2, 1.0 = 1:1


# ─── Technique Defaults ──────────────────────────────────────────────────────────

TECHNIQUE_DEFAULTS = {
    "resonance": {
        "default_bpm": 5.5,
        "rmssd_range": (20, 50),      # ms increase during session
        "duration_scale": {5: 0.15, 10: 0.25, 20: 0.35},  # duration -> pct increase
        "lf_hf_during": 0.8,
        "description": "Slow breathing at ~5.5 bpm to maximize baroreflex gain",
    },
    "box": {
        "default_bpm": 3.75,
        "rmssd_range": (15, 25),
        "duration_scale": {5: 0.10, 10: 0.18, 20: 0.25},
        "lf_hf_during": 1.0,
        "description": "Equal inhale-hold-exhale-hold pattern (Navy SEALs)",
    },
    "4-7-8": {
        "default_bpm": 3.16,
        "rmssd_range": (30, 40),
        "duration_scale": {5: 0.20, 10: 0.30, 20: 0.38},
        "lf_hf_during": 0.6,
        "description": "Extended exhale pattern for parasympathetic activation",
    },
    "coherent": {
        "default_bpm": 6.0,
        "rmssd_range": (15, 20),
        "duration_scale": {5: 0.10, 10: 0.15, 20: 0.22},
        "lf_hf_during": 0.9,
        "description": "Equal 5s inhale / 5s exhale for cardiac coherence",
    },
}


BREATHWORK_EVIDENCE_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="Short-term parasympathetic and HRV-oriented protocol estimates",
    population_summary="Acute breathwork studies in healthy or stressed adults",
    main_caveat="Acute response is variable and should not be treated as a personal biometric prediction",
    uncertainty_factors=["technique familiarity", "baseline stress", "measurement noise"],
    claim_boundary="Protocol guidance for same-day regulation only",
)


# ─── Breathwork HRV Response Engine ──────────────────────────────────────────────

class BreathworkModel:
    """
    Breathwork HRV response model based on slow-breathing meta-analyses.

    Slow breathing (< 10 bpm) consistently increases vagal tone measured
    by rMSSD and shifts LF/HF ratio toward parasympathetic dominance.
    The magnitude depends on technique, duration, breathing rate, and
    inhale:exhale ratio.

    Core mechanisms (Lehrer & Gevirtz 2014):
    - Baroreflex stimulation at ~0.1 Hz (resonance frequency)
    - Vagal afferent activation via slow diaphragmatic breathing
    - RSA amplification when breathing rate matches cardiovascular oscillations

    This model predicts during-session and post-session HRV changes
    to guide HELIOS protocol timing and technique selection.
    """

    @staticmethod
    def _interpolate_duration_scale(duration_min: float, scale_map: dict) -> float:
        """
        Interpolate the rMSSD percentage increase based on session duration.

        Uses linear interpolation between known duration breakpoints.
        Clamps to nearest boundary for out-of-range durations.
        """
        durations = sorted(scale_map.keys())
        values = [scale_map[d] for d in durations]

        if duration_min <= durations[0]:
            return values[0]
        if duration_min >= durations[-1]:
            return values[-1]

        # Find bracketing durations and interpolate
        for i in range(len(durations) - 1):
            if durations[i] <= duration_min <= durations[i + 1]:
                t = (duration_min - durations[i]) / (durations[i + 1] - durations[i])
                return values[i] + t * (values[i + 1] - values[i])

        return values[-1]

    @staticmethod
    def _ratio_multiplier(inhale_exhale_ratio: float) -> float:
        """
        Scale HRV effect by inhale:exhale ratio.

        Van Diest 2014: 1:2 ratio (~0.5) produces ~40% rMSSD increase,
        while 1:1 ratio (~1.0) produces ~25%. Longer exhales enhance
        parasympathetic activation via prolonged vagal engagement.

        Linear interpolation between 1:1 (1.0) and 1:2 (0.5).
        Clamped to [0.3, 1.5] for physiological plausibility.
        """
        ratio = np.clip(inhale_exhale_ratio, 0.3, 1.5)

        # At ratio=0.5 (1:2): multiplier=1.0 (reference, ~40% effect)
        # At ratio=1.0 (1:1): multiplier=0.625 (~25% effect = 25/40)
        multiplier = 1.0 - 0.75 * (ratio - 0.5)
        return float(np.clip(multiplier, 0.5, 1.2))

    def hrv_response(
        self,
        technique: str,
        breaths_per_min: float,
        duration_min: float,
        inhale_exhale_ratio: float = 0.5,
        baseline_rmssd: float = 42.0,
    ) -> dict:
        """
        Predict HRV response to a breathwork session.

        Calculates during-session rMSSD increase and post-session residual
        based on technique, duration, breathing rate, and exhale ratio.

        During-session rMSSD increases (Laborde 2022 meta-analysis):
        - Resonance (5.5 bpm): +20-50ms, scales with duration
        - Box (3.75 bpm): +15-25ms
        - 4-7-8 (3.16 bpm): +30-40ms (harder to sustain)
        - Coherent (6.0 bpm): +15-20ms

        Inhale:exhale ratio effect (Van Diest 2014):
        - 1:2 ratio -- ~40% rMSSD increase (reference)
        - 1:1 ratio -- ~25% rMSSD increase

        Post-session residual: +8-15ms rMSSD for 1-4 hours.
        LF/HF shifts from ~2.5 (sympathetic) to ~0.8 (parasympathetic).

        Args:
            technique: One of 'resonance', 'box', '4-7-8', 'coherent'.
            breaths_per_min: Respiratory rate in breaths per minute.
            duration_min: Session duration in minutes.
            inhale_exhale_ratio: Inhale/exhale time ratio (0.5 = 1:2).
            baseline_rmssd: Resting rMSSD in milliseconds (default 42ms).

        Returns:
            dict with during_rmssd_ms, during_rmssd_pct_increase,
            post_rmssd_delta_ms, post_duration_hours, lf_hf_during,
            optimal_rate_bpm, advisory.
        """
        def build_result(payload: dict) -> dict:
            return merge_evidence(payload, BREATHWORK_EVIDENCE_PROFILE)

        # Guard: unknown technique
        if technique not in TECHNIQUE_DEFAULTS:
            return build_result(
                {
                    "during_rmssd_ms": baseline_rmssd,
                    "during_rmssd_pct_increase": 0.0,
                    "post_rmssd_delta_ms": 0.0,
                    "post_duration_hours": 0.0,
                    "lf_hf_during": 2.5,
                    "optimal_rate_bpm": 5.5,
                    "model_type": "heuristic",
                    "advisory": (
                        f"Unknown technique '{technique}'. "
                        f"Supported: resonance, box, 4-7-8, coherent."
                    ),
                }
            )

        # Guard: non-positive values
        if duration_min <= 0 or breaths_per_min <= 0 or baseline_rmssd <= 0:
            return build_result(
                {
                    "during_rmssd_ms": baseline_rmssd,
                    "during_rmssd_pct_increase": 0.0,
                    "post_rmssd_delta_ms": 0.0,
                    "post_duration_hours": 0.0,
                    "lf_hf_during": 2.5,
                    "optimal_rate_bpm": 5.5,
                    "model_type": "heuristic",
                    "advisory": "Error: duration, breaths_per_min, and baseline_rmssd must be positive.",
                }
            )

        tech = TECHNIQUE_DEFAULTS[technique]

        # 1. Duration-scaled percentage increase
        pct_increase = self._interpolate_duration_scale(duration_min, tech["duration_scale"])

        # 2. Inhale:exhale ratio modifier (Van Diest 2014)
        ratio_mult = self._ratio_multiplier(inhale_exhale_ratio)
        pct_increase *= ratio_mult

        # 3. Breathing rate deviation penalty
        # Optimal effect at the technique's default rate; deviations reduce efficacy
        optimal_bpm = tech["default_bpm"]
        rate_deviation = abs(breaths_per_min - optimal_bpm) / optimal_bpm
        rate_penalty = max(0.5, 1.0 - rate_deviation * 0.5)
        pct_increase *= rate_penalty

        # 4. Calculate absolute rMSSD values
        during_rmssd = baseline_rmssd * (1.0 + pct_increase)
        during_rmssd = round(during_rmssd, 1)
        pct_increase_final = round(pct_increase * 100, 1)

        # 5. Post-session residual (Laborde 2022)
        # +8-15ms for 1-4 hours, scales with session duration
        post_delta_base = 8.0 + min(duration_min / 20.0, 1.0) * 7.0  # 8-15ms range
        post_delta = round(post_delta_base * ratio_mult * rate_penalty, 1)
        post_hours = round(1.0 + min(duration_min / 10.0, 1.0) * 3.0, 1)  # 1-4 hours

        # 6. LF/HF ratio during session
        lf_hf_during = tech["lf_hf_during"]

        # 7. Advisory
        rmssd_delta_ms = round(during_rmssd - baseline_rmssd, 1)
        if pct_increase_final >= 25:
            quality = "strong"
        elif pct_increase_final >= 15:
            quality = "moderate"
        else:
            quality = "mild"

        advisory = (
            f"rough estimate: {quality} HRV response of about +{rmssd_delta_ms}ms rMSSD "
            f"({pct_increase_final}% increase) during {duration_min}min {technique} breathing "
            f"at {breaths_per_min} bpm. Post-session residual may be about +{post_delta}ms "
            f"for ~{post_hours}h (Laborde 2022). This is a citation-informed heuristic, "
            f"not a validated personal prediction."
        )

        return build_result(
            {
                "during_rmssd_ms": during_rmssd,
                "during_rmssd_pct_increase": pct_increase_final,
                "post_rmssd_delta_ms": post_delta,
                "post_duration_hours": post_hours,
                "lf_hf_during": lf_hf_during,
                "optimal_rate_bpm": optimal_bpm,
                "model_type": "heuristic",
                "advisory": advisory,
            }
        )

    def find_resonance_frequency(self, resting_hr: float = 70) -> dict:
        """
        Estimate individual resonance breathing frequency.

        Resonance frequency is the breathing rate that maximizes heart rate
        variability by aligning respiratory and cardiovascular oscillations
        at ~0.1 Hz (Lehrer & Gevirtz 2014).

        Population default: ~6.0 bpm (0.1 Hz).
        Range: 4.5-6.5 bpm, varies by body size and lung capacity.
        Estimation heuristic: slightly slower for higher resting HR,
        as elevated RHR suggests lower cardiovascular fitness and
        potentially shifted baroreflex dynamics.

        Formula: resonance ≈ 6.0 - (resting_hr - 60) × 0.02

        Args:
            resting_hr: Resting heart rate in bpm (default 70).

        Returns:
            dict with estimated_resonance_bpm, range_low, range_high,
            cycle_seconds, advisory.
        """
        # Guard: physiologically implausible RHR
        if resting_hr <= 0:
            return {
                "estimated_resonance_bpm": 6.0,
                "range_low": 4.5,
                "range_high": 6.5,
                "cycle_seconds": 10.0,
                "advisory": "Error: resting_hr must be positive.",
            }

        # Simple estimation (Lehrer & Gevirtz 2014)
        estimated = 6.0 - (resting_hr - 60) * 0.02
        estimated = float(np.clip(estimated, 4.5, 6.5))
        estimated = round(estimated, 2)

        cycle_seconds = round(60.0 / estimated, 1)

        # Confidence range: ±0.5 bpm around estimate
        range_low = round(max(4.5, estimated - 0.5), 2)
        range_high = round(min(6.5, estimated + 0.5), 2)

        # Advisory
        if resting_hr < 60:
            fitness_note = "Low RHR suggests good cardiovascular fitness"
        elif resting_hr > 80:
            fitness_note = "Elevated RHR — regular practice may lower it over weeks"
        else:
            fitness_note = "Normal RHR range"

        advisory = (
            f"Estimated resonance frequency: {estimated} bpm "
            f"({cycle_seconds}s per breath cycle). "
            f"Likely range: {range_low}-{range_high} bpm. "
            f"{fitness_note}. "
            f"Precise resonance requires biofeedback testing, but this estimate "
            f"is a good starting point (Lehrer & Gevirtz 2014)."
        )

        return {
            "estimated_resonance_bpm": estimated,
            "range_low": range_low,
            "range_high": range_high,
            "cycle_seconds": cycle_seconds,
            "advisory": advisory,
        }

    def session_recommendation(
        self,
        goal: str,
        time_available_min: float = 10,
        time_of_day_hours: Optional[float] = None,
        current_stress: str = "moderate",
    ) -> dict:
        """
        Recommend a breathwork session based on goal, available time, and context.

        Maps goals to optimal techniques (Zaccaro 2018):
        - 'calm': Wind-down / anxiety reduction -- 4-7-8 or resonance
        - 'focus': Pre-work cognitive preparation -- coherent breathing
        - 'recovery': Post-exercise parasympathetic rebound -- resonance
        - 'sleep': Pre-bed vagal activation -- 4-7-8

        Adjusts for time of day and stress level.

        Args:
            goal: One of 'calm', 'focus', 'recovery', 'sleep'.
            time_available_min: Minutes available for the session (default 10).
            time_of_day_hours: Hour of day in 24h format (e.g., 22.0 for 10 PM).
            current_stress: 'low', 'moderate', or 'high'.

        Returns:
            dict with technique, breaths_per_min, duration_min, inhale_s,
            hold_s, exhale_s, expected_rmssd_change_pct, advisory.
        """
        # Guard: unknown goal
        goal_map = {
            "calm": {
                "technique": "4-7-8",
                "bpm": 3.16,
                "inhale": 4, "hold": 7, "exhale": 8,
                "ratio": 0.5,
            },
            "focus": {
                "technique": "coherent",
                "bpm": 6.0,
                "inhale": 5, "hold": 0, "exhale": 5,
                "ratio": 1.0,
            },
            "recovery": {
                "technique": "resonance",
                "bpm": 5.5,
                "inhale": 4, "hold": 0, "exhale": 7,
                "ratio": 0.57,
            },
            "sleep": {
                "technique": "4-7-8",
                "bpm": 3.16,
                "inhale": 4, "hold": 7, "exhale": 8,
                "ratio": 0.5,
            },
        }

        if goal not in goal_map:
            return merge_evidence(
                {
                    "technique": "resonance",
                    "breaths_per_min": 5.5,
                    "duration_min": 10,
                    "inhale_s": 5,
                    "hold_s": 0,
                    "exhale_s": 6,
                    "expected_rmssd_change_pct": 0.0,
                    "advisory": (
                        f"Unknown goal '{goal}'. "
                        f"Supported: calm, focus, recovery, sleep."
                    ),
                    "model_type": "heuristic",
                },
                BREATHWORK_EVIDENCE_PROFILE,
            )

        rec = goal_map[goal]

        # Adjust duration to available time
        duration = min(time_available_min, 20)  # cap at 20min
        duration = max(duration, 3)              # minimum useful session

        # Time-of-day adjustments
        if time_of_day_hours is not None:
            # Evening/night: prefer slower, more parasympathetic techniques
            if time_of_day_hours >= 20 and goal != "sleep":
                rec = goal_map["calm"]  # override to calming technique at night
            # Morning: if goal is focus, slightly faster rate
            elif time_of_day_hours < 8 and goal == "focus":
                rec["bpm"] = 6.0  # keep coherent but ensure alertness

        # Stress-level adjustments
        stress_multiplier = {"low": 0.8, "moderate": 1.0, "high": 1.2}
        stress_mult = stress_multiplier.get(current_stress, 1.0)

        # Higher stress -- longer session recommended
        if current_stress == "high" and duration < 15:
            duration = min(time_available_min, 15)

        # Estimate rMSSD change using the model
        tech = TECHNIQUE_DEFAULTS[rec["technique"]]
        pct = self._interpolate_duration_scale(duration, tech["duration_scale"])
        ratio_mult = self._ratio_multiplier(rec["ratio"])
        expected_pct = round(pct * ratio_mult * 100 * stress_mult, 1)

        # Build timing description
        if rec["hold"] > 0:
            pattern = f"{rec['inhale']}s inhale -- {rec['hold']}s hold -- {rec['exhale']}s exhale"
        else:
            pattern = f"{rec['inhale']}s inhale -- {rec['exhale']}s exhale"

        # Advisory
        goal_descriptions = {
            "calm": "anxiety reduction and parasympathetic activation",
            "focus": "cognitive clarity via cardiac coherence",
            "recovery": "post-exercise parasympathetic rebound",
            "sleep": "pre-sleep vagal activation and melatonin support",
        }
        goal_desc = goal_descriptions.get(goal, goal)

        stress_note = ""
        if current_stress == "high":
            stress_note = " Extended duration recommended for high stress."

        advisory = (
            f"Recommended: {duration}min {rec['technique']} breathing ({pattern}) "
            f"for {goal_desc}. Expected rMSSD increase: ~{expected_pct}% "
            f"(Zaccaro 2018).{stress_note}"
        )

        return merge_evidence(
            {
                "technique": rec["technique"],
                "breaths_per_min": rec["bpm"],
                "duration_min": duration,
                "inhale_s": rec["inhale"],
                "hold_s": rec["hold"],
                "exhale_s": rec["exhale"],
                "expected_rmssd_change_pct": expected_pct,
                "model_type": "heuristic",
                "advisory": advisory,
            },
            BREATHWORK_EVIDENCE_PROFILE,
        )


# ─── Example Usage ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = BreathworkModel()

    print("=" * 60)
    print("HELIOS Breathwork HRV Model — Examples")
    print("=" * 60)

    # 1. 10-min resonance breathing session (5.5 bpm, 1:2 ratio), baseline rMSSD 38
    response = model.hrv_response(
        technique="resonance",
        breaths_per_min=5.5,
        duration_min=10,
        inhale_exhale_ratio=0.5,
        baseline_rmssd=38.0,
    )
    print(f"\n--- 10-min Resonance Breathing (5.5 bpm, 1:2 ratio, baseline 38ms) ---")
    print(f"During-session rMSSD: {response['during_rmssd_ms']}ms")
    print(f"rMSSD increase: +{response['during_rmssd_pct_increase']}%")
    print(f"Post-session residual: +{response['post_rmssd_delta_ms']}ms for ~{response['post_duration_hours']}h")
    print(f"LF/HF during session: {response['lf_hf_during']} (resting ~2.5)")
    print(f"Optimal rate: {response['optimal_rate_bpm']} bpm")
    print(f"Advisory: {response['advisory']}")

    # 2. Find resonance frequency for RHR 65
    resonance = model.find_resonance_frequency(resting_hr=65)
    print(f"\n--- Resonance Frequency (RHR = 65 bpm) ---")
    print(f"Estimated resonance: {resonance['estimated_resonance_bpm']} bpm")
    print(f"Range: {resonance['range_low']}-{resonance['range_high']} bpm")
    print(f"Cycle length: {resonance['cycle_seconds']}s per breath")
    print(f"Advisory: {resonance['advisory']}")

    # 3. Session recommendation for 'sleep' goal, 15 min available, 10 PM
    rec = model.session_recommendation(
        goal="sleep",
        time_available_min=15,
        time_of_day_hours=22.0,
        current_stress="moderate",
    )
    print(f"\n--- Session Recommendation (sleep, 15min, 10 PM) ---")
    print(f"Technique: {rec['technique']}")
    print(f"Rate: {rec['breaths_per_min']} bpm")
    print(f"Duration: {rec['duration_min']}min")
    if rec['hold_s'] > 0:
        print(f"Pattern: {rec['inhale_s']}s inhale -> {rec['hold_s']}s hold -> {rec['exhale_s']}s exhale")
    else:
        print(f"Pattern: {rec['inhale_s']}s inhale -> {rec['exhale_s']}s exhale")
    print(f"Expected rMSSD change: +{rec['expected_rmssd_change_pct']}%")
    print(f"Advisory: {rec['advisory']}")
