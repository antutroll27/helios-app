"""
HELIOS - Space Weather Biological Impact Model
Translates NOAA space weather data (Kp, solar wind, Bz) into heuristic
biological context and conservative protocol adjustments.

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

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np


@dataclass
class SpaceWeatherReading:
    """Single snapshot of space weather conditions from NOAA SWPC."""

    kp_index: float
    solar_wind_speed: float
    bz: float
    timestamp: datetime


class SpaceWeatherBioModel:
    """
    Maps geomagnetic and solar wind parameters to exploratory biological context.

    The strongest evidence here is observational and population-level, so the
    outputs should be treated as heuristics rather than validated individual
    predictions.
    """

    def kp_hrv_impact(
        self,
        kp_index: float,
        baseline_rmssd: float = 40.0,
        baseline_sdnn: float = 50.0,
    ) -> dict:
        """Estimate HRV changes from population-level associations."""

        kp_index = max(0.0, min(9.0, kp_index))
        if baseline_rmssd <= 0 or baseline_sdnn <= 0:
            return {
                "expected_rmssd": baseline_rmssd,
                "expected_sdnn": baseline_sdnn,
                "delta_rmssd": 0.0,
                "delta_sdnn": 0.0,
                "pct_reduction": 0.0,
                "risk_tier": "unknown",
                "evidence_level": "observational",
                "advisory": "Error: baseline HRV values must be positive.",
            }

        delta_rmssd = -6.125 * kp_index
        delta_sdnn = -3.417 * kp_index
        expected_rmssd = max(5.0, baseline_rmssd + delta_rmssd)
        expected_sdnn = max(5.0, baseline_sdnn + delta_sdnn)
        pct_reduction = abs(delta_rmssd) / baseline_rmssd

        if pct_reduction < 0.15:
            risk_tier = "low"
            advisory = (
                "Quiet geomagnetic conditions. Observational HRV studies do not suggest a "
                "clear concern at this level, and individual relevance is uncertain."
            )
        elif pct_reduction < 0.30:
            risk_tier = "moderate"
            advisory = (
                "Observational HRV studies suggest a moderate association at this Kp range, "
                "but individual relevance is uncertain. Consider conservative recovery basics."
            )
        else:
            risk_tier = "high"
            advisory = (
                "Observational HRV studies suggest a stronger association at this Kp range, "
                "but this remains a heuristic rather than a validated personal prediction."
            )

        return {
            "expected_rmssd": round(expected_rmssd, 1),
            "expected_sdnn": round(expected_sdnn, 1),
            "delta_rmssd": round(delta_rmssd, 1),
            "delta_sdnn": round(delta_sdnn, 1),
            "pct_reduction": round(pct_reduction, 3),
            "risk_tier": risk_tier,
            "evidence_level": "observational",
            "advisory": advisory,
        }

    def kp_melatonin_modifier(self, kp_history: list[tuple[datetime, float]]) -> dict:
        """Estimate melatonin disruption risk from lagged Kp history."""

        if not kp_history:
            return {
                "disruption_risk": None,
                "lag_window_kp_avg": None,
                "readings_in_window": 0,
                "evidence_level": "preliminary",
                "advisory": "Insufficient data - need Kp readings from 15-33h ago.",
            }

        now = kp_history[-1][0]
        window_start = now - timedelta(hours=33)
        window_end = now - timedelta(hours=15)
        readings_in_window = [
            kp for ts, kp in kp_history if window_start <= ts <= window_end
        ]

        if len(readings_in_window) < 3:
            return {
                "disruption_risk": None,
                "lag_window_kp_avg": None,
                "readings_in_window": len(readings_in_window),
                "evidence_level": "preliminary",
                "advisory": "Insufficient data - need at least 3 Kp readings in the 15-33h lag window.",
            }

        avg_kp = float(np.mean(readings_in_window))
        disruption_risk = min(1.0, max(0.0, avg_kp / 7.0))

        if disruption_risk < 0.3:
            advisory = (
                "Low geomagnetic activity in the lag window. Melatonin evidence is preliminary, "
                "so treat this as limited observational context only."
            )
        elif disruption_risk < 0.6:
            advisory = (
                "Moderate geomagnetic activity in the lag window. Preliminary observational "
                "research has reported a possible association with melatonin timing, but "
                "individual relevance is uncertain."
            )
        else:
            advisory = (
                "Elevated geomagnetic activity in the lag window. Preliminary observational "
                "research has reported a possible association with melatonin disruption, but "
                "this is not validated for individual prediction."
            )

        return {
            "disruption_risk": round(disruption_risk, 3),
            "lag_window_kp_avg": round(avg_kp, 2),
            "readings_in_window": len(readings_in_window),
            "evidence_level": "preliminary",
            "evidence_note": "Burch 2008 is preliminary and not independently replicated.",
            "advisory": advisory,
        }

    def kp_cognitive_advisory(self, kp_index: float) -> dict:
        """Provide cognition-related guidance from observational Kp associations."""

        kp_index = max(0.0, min(9.0, kp_index))

        if kp_index < 3:
            impact_tier = "background"
            focus_modifier = 1.0
            advisory = (
                "Limited observational research has not shown a clear concern at this level. "
                "Treat current geomagnetic conditions as background context with uncertain individual relevance."
            )
        elif kp_index < 5:
            impact_tier = "mild"
            focus_modifier = 0.9
            advisory = (
                "Limited observational research has reported mild cognition-related associations "
                "at higher Kp values, but uncertain individual relevance makes this unsuitable as "
                "a personal prediction."
            )
        elif kp_index < 7:
            impact_tier = "moderate"
            focus_modifier = 0.75
            advisory = (
                "Observational research has reported cognition-related associations during more "
                "active geomagnetic periods, but uncertain individual relevance means this should "
                "only guide conservative planning."
            )
        else:
            impact_tier = "elevated"
            focus_modifier = 0.6
            advisory = (
                "Observational research has reported stronger cognition-related associations during "
                "geomagnetic storms, but uncertain individual relevance means this remains exploratory "
                "context rather than a deterministic forecast."
            )

        return {
            "impact_tier": impact_tier,
            "focus_modifier": round(focus_modifier, 2),
            "evidence_level": "observational",
            "advisory": advisory,
        }

    def composite_disruption(self, reading: SpaceWeatherReading) -> dict:
        """
        Build an exploratory composite score from Kp, Bz, and solar wind speed.
        """

        kp_norm = min(1.0, max(0.0, reading.kp_index / 9.0))
        bz_norm = min(1.0, max(0.0, -reading.bz / 25.0))
        wind_norm = min(1.0, max(0.0, (reading.solar_wind_speed - 300) / 700.0))
        composite = 0.5 * kp_norm + 0.3 * bz_norm + 0.2 * wind_norm
        bio_score = round(composite * 10, 1)

        protocol_adjustments: list[str] = []
        if bio_score <= 2:
            advisory = (
                "Space-weather conditions are quiet. No special protocol change is needed for "
                "most users based on this exploratory heuristic."
            )
        elif bio_score <= 4:
            protocol_adjustments.append("Consider 15min earlier wind-down.")
            advisory = (
                "Minor geomagnetic activity is present. This exploratory heuristic suggests a "
                "small recovery adjustment, but it is not validated for individual prediction."
            )
        elif bio_score <= 6:
            protocol_adjustments.append("Advance wind-down 30min.")
            protocol_adjustments.append("Extend morning light exposure 10min.")
            advisory = (
                "Active geomagnetic conditions may justify a more conservative recovery routine, "
                "but this remains an exploratory heuristic and is not validated for individual prediction."
            )
        elif bio_score <= 8:
            protocol_adjustments.append("Advance wind-down 45min.")
            protocol_adjustments.append("Extend morning light exposure 20min.")
            protocol_adjustments.append("Expect reduced focus - use shorter work blocks.")
            advisory = (
                "Geomagnetic storm conditions may justify stronger recovery basics, but this "
                "remains an exploratory heuristic and is not validated for individual prediction."
            )
        else:
            protocol_adjustments.append("Major disruption - prioritize sleep hygiene.")
            protocol_adjustments.append("Avoid demanding cognitive tasks.")
            protocol_adjustments.append("Advance wind-down 45min+.")
            protocol_adjustments.append("Extend morning light exposure 20min+.")
            advisory = (
                "Severe geomagnetic storm conditions justify the most conservative recovery routine "
                "in this exploratory heuristic. It is not validated for individual prediction."
            )

        return {
            "bio_score": bio_score,
            "kp_norm": round(kp_norm, 3),
            "bz_norm": round(bz_norm, 3),
            "wind_norm": round(wind_norm, 3),
            "protocol_adjustments": protocol_adjustments,
            "model_type": "exploratory_heuristic",
            "advisory": advisory,
        }


if __name__ == "__main__":
    model = SpaceWeatherBioModel()
    reading = SpaceWeatherReading(
        kp_index=5.0,
        solar_wind_speed=650.0,
        bz=-12.0,
        timestamp=datetime(2026, 4, 5, 14, 0),
    )

    print("=" * 60)
    print("HELIOS Space Weather Biological Impact Report")
    print(f"Timestamp: {reading.timestamp.strftime('%Y-%m-%d %H:%M UTC')}")
    print(
        f"Kp: {reading.kp_index}  |  Solar Wind: {reading.solar_wind_speed} km/s  |  Bz: {reading.bz} nT"
    )
    print("=" * 60)

    hrv = model.kp_hrv_impact(reading.kp_index)
    print("\n--- HRV Impact (Alabdali 2022) ---")
    print(f"Expected rMSSD: {hrv['expected_rmssd']}ms (delta: {hrv['delta_rmssd']}ms)")
    print(f"Expected SDNN:  {hrv['expected_sdnn']}ms (delta: {hrv['delta_sdnn']}ms)")
    print(f"Reduction: {hrv['pct_reduction']:.1%}  |  Risk: {hrv['risk_tier']}")
    print(f"Advisory: {hrv['advisory']}")

    cog = model.kp_cognitive_advisory(reading.kp_index)
    print("\n--- Cognitive Advisory (Alabdali 2024) ---")
    print(f"Impact: {cog['impact_tier']}  |  Focus modifier: {cog['focus_modifier']}")
    print(f"Advisory: {cog['advisory']}")

    comp = model.composite_disruption(reading)
    print("\n--- Composite Disruption Score ---")
    print(f"Bio Score: {comp['bio_score']} / 10")
    print(
        f"Signals - Kp: {comp['kp_norm']:.2f}  Bz: {comp['bz_norm']:.2f}  Wind: {comp['wind_norm']:.2f}"
    )
    print("Protocol adjustments:")
    for adj in comp["protocol_adjustments"]:
        print(f"  * {adj}")
    print(f"Advisory: {comp['advisory']}")
