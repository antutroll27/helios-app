"""
HELIOS — Space Weather Biological Impact Model
Translates NOAA space weather data (Kp, solar wind, Bz) into biological
impact predictions with actionable protocol adjustments.

References:
- Alabdali, S. et al. (2022) 'Geomagnetic activity and heart rate variability:
  a cross-sectional study of 809 subjects', Sci Total Environ, 838, 156067.
- McCraty, R. et al. (2018) 'Long-term study of heart rate variability responses
  to changes in the solar and geomagnetic environment', Scientific Reports, 8, 2663.
- Burch, J.B. et al. (2008) 'Geomagnetic activity and human melatonin metabolite
  excretion', Neuroscience Letters, 438, pp. 76-79.
- Alabdali, S. et al. (2024) 'Geomagnetic disturbances and cognitive function',
  Environ Int, 185, 108526.
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional


@dataclass
class SpaceWeatherReading:
    """Single snapshot of space weather conditions from NOAA SWPC."""
    kp_index: float           # Planetary K-index (0-9)
    solar_wind_speed: float   # km/s
    bz: float                 # nT, negative = southward = more geoeffective
    timestamp: datetime


# ─── Space Weather Biological Impact Model ──────────────────────────────────

class SpaceWeatherBioModel:
    """
    Maps geomagnetic and solar wind parameters to predicted biological effects.

    Based on epidemiological studies showing statistically significant
    associations between geomagnetic activity and autonomic nervous system
    function, melatonin production, and cognitive performance.

    Key finding (Alabdali 2022, n=809):
    - rMSSD decreased by 14.7ms across the interquartile Kp range (25th-75th
      percentile, ~2.4 Kp units), indicating reduced parasympathetic tone
      during geomagnetic disturbances.
    - SDNN decreased by 8.2ms over the same range.
    """

    def kp_hrv_impact(
        self,
        kp_index: float,
        baseline_rmssd: float = 40.0,
        baseline_sdnn: float = 50.0,
    ) -> dict:
        """
        Predict HRV changes based on current Kp index.

        Linear model derived from Alabdali 2022:
        - Per 2.4 Kp units (IQR): -14.7ms rMSSD, -8.2ms SDNN
        - Per 1 Kp unit: -6.125ms rMSSD, -3.417ms SDNN
        - Anchored at Kp=0 (quiet conditions)

        Args:
            kp_index: Current planetary K-index (0-9)
            baseline_rmssd: User's baseline rMSSD in ms (default 40)
            baseline_sdnn: User's baseline SDNN in ms (default 50)

        Returns:
            dict with expected values, deltas, percent reduction, risk tier
        """
        # Input validation
        kp_index = max(0.0, min(9.0, kp_index))
        if baseline_rmssd <= 0 or baseline_sdnn <= 0:
            return {
                "expected_rmssd": baseline_rmssd,
                "expected_sdnn": baseline_sdnn,
                "delta_rmssd": 0.0,
                "delta_sdnn": 0.0,
                "pct_reduction": 0.0,
                "risk_tier": "unknown",
                "advisory": "Error: baseline HRV values must be positive.",
            }

        # Per-unit Kp scaling factors
        delta_rmssd_per_kp = -6.125   # ms per Kp unit
        delta_sdnn_per_kp = -3.417    # ms per Kp unit

        delta_rmssd = delta_rmssd_per_kp * kp_index
        delta_sdnn = delta_sdnn_per_kp * kp_index

        expected_rmssd = max(5.0, baseline_rmssd + delta_rmssd)
        expected_sdnn = max(5.0, baseline_sdnn + delta_sdnn)

        pct_reduction = abs(delta_rmssd) / baseline_rmssd

        if pct_reduction < 0.15:
            risk_tier = "low"
            advisory = "Geomagnetic conditions nominal — no HRV impact expected."
        elif pct_reduction < 0.30:
            risk_tier = "moderate"
            advisory = (
                "Moderate HRV suppression expected. Consider stress-reduction "
                "practices and avoid intense training."
            )
        else:
            risk_tier = "high"
            advisory = (
                "Significant HRV suppression likely (Alabdali 2022). Prioritize "
                "recovery, avoid high-intensity exercise, extend wind-down routine."
            )

        return {
            "expected_rmssd": round(expected_rmssd, 1),
            "expected_sdnn": round(expected_sdnn, 1),
            "delta_rmssd": round(delta_rmssd, 1),
            "delta_sdnn": round(delta_sdnn, 1),
            "pct_reduction": round(pct_reduction, 3),
            "risk_tier": risk_tier,
            "advisory": advisory,
        }

    def kp_melatonin_modifier(
        self,
        kp_history: list[tuple[datetime, float]],
    ) -> dict:
        """
        Estimate melatonin disruption risk from lagged Kp history.

        Burch et al. (2008) found that geomagnetic disturbances affect
        melatonin metabolite excretion with a 15-33 hour lag. This method
        filters Kp readings to that window and estimates disruption risk.

        Args:
            kp_history: List of (timestamp, kp_index) tuples, most recent last

        Returns:
            dict with disruption_risk (0-1 or None), lag window stats, advisory
        """
        if not kp_history:
            return {
                "disruption_risk": None,
                "lag_window_kp_avg": None,
                "readings_in_window": 0,
                "advisory": "Insufficient data — need Kp readings from 15-33h ago.",
            }

        now = kp_history[-1][0]
        window_start = now - timedelta(hours=33)
        window_end = now - timedelta(hours=15)

        readings_in_window = [
            kp for ts, kp in kp_history
            if window_start <= ts <= window_end
        ]

        if len(readings_in_window) < 3:
            return {
                "disruption_risk": None,
                "lag_window_kp_avg": None,
                "readings_in_window": len(readings_in_window),
                "advisory": "Insufficient data — need at least 3 Kp readings in the 15-33h lag window.",
            }

        avg_kp = float(np.mean(readings_in_window))
        disruption_risk = min(1.0, max(0.0, avg_kp / 7.0))

        if disruption_risk < 0.3:
            advisory = "Low melatonin disruption risk from prior geomagnetic activity."
        elif disruption_risk < 0.6:
            advisory = (
                "Moderate melatonin disruption risk (Burch 2008). Consider "
                "supplemental dim-light exposure in the evening."
            )
        else:
            advisory = (
                "High melatonin disruption risk from geomagnetic storm 15-33h ago. "
                "Prioritize dark environment, consider melatonin timing adjustment."
            )

        return {
            "disruption_risk": round(disruption_risk, 3),
            "lag_window_kp_avg": round(avg_kp, 2),
            "readings_in_window": len(readings_in_window),
            "advisory": advisory,
        }

    def kp_cognitive_advisory(self, kp_index: float) -> dict:
        """
        Cognitive impact advisory based on Kp index.

        Alabdali et al. (2024) found statistically significant associations
        between geomagnetic activity and cognitive function, with effects
        emerging at Kp >= 3 and becoming pronounced at Kp >= 5.

        Args:
            kp_index: Current planetary K-index (0-9)

        Returns:
            dict with impact tier, focus modifier (0-1), and advisory
        """
        kp_index = max(0.0, min(9.0, kp_index))

        if kp_index < 3:
            impact_tier = "none"
            focus_modifier = 1.0
            advisory = "No cognitive impact expected at current geomagnetic activity."
        elif kp_index < 5:
            impact_tier = "mild"
            focus_modifier = 0.9
            advisory = (
                "Mild cognitive effects possible (Alabdali 2024). Schedule "
                "demanding tasks for your peak circadian window."
            )
        elif kp_index < 7:
            impact_tier = "moderate"
            focus_modifier = 0.75
            advisory = (
                "Moderate cognitive impact expected. Consider shorter focus blocks "
                "with more frequent breaks. Avoid complex decision-making if possible."
            )
        else:
            impact_tier = "significant"
            focus_modifier = 0.6
            advisory = (
                "Significant cognitive disruption likely during geomagnetic storm "
                "(Alabdali 2024). Defer critical decisions, extend break intervals, "
                "prioritize routine tasks."
            )

        return {
            "impact_tier": impact_tier,
            "focus_modifier": round(focus_modifier, 2),
            "advisory": advisory,
        }

    def composite_disruption(self, reading: SpaceWeatherReading) -> dict:
        """
        Composite biological disruption score from all space weather signals.

        Normalizes Kp, Bz, and solar wind speed to 0-1 range and combines
        with empirically-informed weights:
        - Kp index (0.5): strongest epidemiological evidence
        - Bz component (0.3): southward IMF = more geoeffective
        - Solar wind speed (0.2): modulates storm intensity

        Args:
            reading: SpaceWeatherReading with current conditions

        Returns:
            dict with bio_score (0-10), normalized signals, protocol adjustments
        """
        # Normalize each signal to 0-1
        kp_norm = min(1.0, max(0.0, reading.kp_index / 9.0))
        bz_norm = min(1.0, max(0.0, -reading.bz / 25.0))
        wind_norm = min(1.0, max(0.0, (reading.solar_wind_speed - 300) / 700.0))

        # Weighted composite
        composite = 0.5 * kp_norm + 0.3 * bz_norm + 0.2 * wind_norm
        bio_score = round(composite * 10, 1)

        # Protocol adjustments based on score tiers
        protocol_adjustments = []
        if bio_score <= 2:
            advisory = "Space weather quiet — no protocol adjustments needed."
        elif bio_score <= 4:
            protocol_adjustments.append("Consider 15min earlier wind-down.")
            advisory = "Minor geomagnetic activity — slight protocol adjustment recommended."
        elif bio_score <= 6:
            protocol_adjustments.append("Advance wind-down 30min.")
            protocol_adjustments.append("Extend morning light exposure 10min.")
            advisory = (
                "Active geomagnetic conditions — moderate protocol adjustments "
                "to protect circadian alignment."
            )
        elif bio_score <= 8:
            protocol_adjustments.append("Advance wind-down 45min.")
            protocol_adjustments.append("Extend morning light exposure 20min.")
            protocol_adjustments.append("Expect reduced focus — use shorter work blocks.")
            advisory = (
                "Geomagnetic storm in progress — significant protocol adjustments "
                "recommended (McCraty 2018)."
            )
        else:
            protocol_adjustments.append("Major disruption — prioritize sleep hygiene.")
            protocol_adjustments.append("Avoid demanding cognitive tasks.")
            protocol_adjustments.append("Advance wind-down 45min+.")
            protocol_adjustments.append("Extend morning light exposure 20min+.")
            advisory = (
                "Severe geomagnetic storm — major biological disruption expected. "
                "Prioritize recovery and sleep hygiene above all else."
            )

        return {
            "bio_score": bio_score,
            "kp_norm": round(kp_norm, 3),
            "bz_norm": round(bz_norm, 3),
            "wind_norm": round(wind_norm, 3),
            "protocol_adjustments": protocol_adjustments,
            "advisory": advisory,
        }


# ─── Example Usage ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = SpaceWeatherBioModel()

    # Example: Kp 5 minor storm with elevated solar wind and southward Bz
    reading = SpaceWeatherReading(
        kp_index=5.0,
        solar_wind_speed=650.0,
        bz=-12.0,
        timestamp=datetime(2026, 4, 5, 14, 0),
    )

    print("=" * 60)
    print("HELIOS Space Weather Biological Impact Report")
    print(f"Timestamp: {reading.timestamp.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Kp: {reading.kp_index}  |  Solar Wind: {reading.solar_wind_speed} km/s  |  Bz: {reading.bz} nT")
    print("=" * 60)

    # HRV Impact
    hrv = model.kp_hrv_impact(reading.kp_index)
    print(f"\n--- HRV Impact (Alabdali 2022) ---")
    print(f"Expected rMSSD: {hrv['expected_rmssd']}ms (delta: {hrv['delta_rmssd']}ms)")
    print(f"Expected SDNN:  {hrv['expected_sdnn']}ms (delta: {hrv['delta_sdnn']}ms)")
    print(f"Reduction: {hrv['pct_reduction']:.1%}  |  Risk: {hrv['risk_tier']}")
    print(f"Advisory: {hrv['advisory']}")

    # Cognitive Advisory
    cog = model.kp_cognitive_advisory(reading.kp_index)
    print(f"\n--- Cognitive Advisory (Alabdali 2024) ---")
    print(f"Impact: {cog['impact_tier']}  |  Focus modifier: {cog['focus_modifier']}")
    print(f"Advisory: {cog['advisory']}")

    # Composite Disruption
    comp = model.composite_disruption(reading)
    print(f"\n--- Composite Disruption Score ---")
    print(f"Bio Score: {comp['bio_score']} / 10")
    print(f"Signals — Kp: {comp['kp_norm']:.2f}  Bz: {comp['bz_norm']:.2f}  Wind: {comp['wind_norm']:.2f}")
    print(f"Protocol adjustments:")
    for adj in comp['protocol_adjustments']:
        print(f"  • {adj}")
    print(f"Advisory: {comp['advisory']}")
