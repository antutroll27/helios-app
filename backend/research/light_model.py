"""
HELIOS — Circadian Light Model
Melanopic EDI zones, melatonin suppression prediction, screen/lamp impact assessment.

References:
- Brown, T.M. et al. (2022) 'Recommendations for daytime, evening, and nighttime
  indoor light exposure to best support physiology, sleep, and wakefulness in
  healthy adults', PLOS Biology, 20(3), e3001571.
- Gimenez, M.C. et al. (2022) 'The dose-response relationship between light
  intensity and melatonin suppression in humans', J Pineal Research, 72(3), e12786.
- Nagare, R. et al. (2019) 'Effect of exposure duration and light spectra on
  nighttime melatonin suppression in adolescents and adults', J Biol Rhythms,
  34(2), pp. 178-189.
- West, K.E. et al. (2011) 'Blue light from light-emitting diodes elicits a
  dose-dependent suppression of melatonin in humans', J Appl Physiol, 110(3),
  pp. 619-626.
- Spitschan, M. et al. (2023) 'Melanopic and visual display characteristics of
  electronic devices', Commun Biol, 6, 228.
- Mouland, J.W. et al. (2025) 'Domestic lighting and melatonin suppression',
  Sci Reports, 15, 29882.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

from evidence_contract import EvidenceProfile, merge_evidence


@dataclass
class LightReading:
    """Single light exposure measurement."""
    melanopic_edi_lux: float
    duration_hours: float = 1.0
    source: str = "outdoor"  # "outdoor" | "screen" | "indoor_cool" | "indoor_warm"


@dataclass
class LightProfile:
    """User light sensitivity profile for age-adjusted models."""
    age: int = 30
    light_sensitive: bool = False  # user override for higher sensitivity


LIGHT_MELATONIN_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="Estimated melatonin suppression and onset delay under melanopic exposure",
    population_summary="Controlled lab light-exposure studies in healthy adults and adolescents",
    main_caveat="Suppression is modeled from dose-response curves and individual delay varies",
    uncertainty_factors=["age", "sensitivity", "duration", "spectral composition"],
    claim_boundary="Heuristic for light-risk planning, not an exact personal forecast",
)


# ─── Circadian Light Model ──────────────────────────────────────────────────

class CircadianLightModel:
    """
    Implements circadian light science for HELIOS protocol generation.

    Core model: 4-parameter logistic melatonin suppression (Gimenez 2022)
    with age adjustment (Nagare 2019) and consensus light zone thresholds
    (Brown 2022).
    """

    # ED50 values by exposure duration (Gimenez 2022)
    _ED50_TABLE = {0.5: 600, 1.0: 350, 2.0: 120, 3.0: 43, 4.0: 15}

    # Device melanopic EDI lookup (Spitschan 2023)
    _DEVICE_EDI = {
        "phone": 80,
        "tablet": 100,
        "laptop": 60,
        "tv": 30,
        "e-reader": 20,
    }

    # Lamp suppression rates % (Mouland 2025)
    _LAMP_SUPPRESSION = {
        "cool_led": 12.3,
        "cool_cfl": 12.1,
        "warm_led": 3.6,
        "warm_cfl": 2.6,
        "incandescent": 1.5,
    }

    def light_zone(self, melanopic_edi: float, hours_to_sleep: float) -> dict:
        """
        Determine circadian light zone based on Brown 2022 consensus thresholds.

        Zones:
        - Daytime (>3h to sleep): target >= 250 melanopic EDI lux
        - Evening (0-3h to sleep): target <= 10 melanopic EDI lux
        - Sleep (should be asleep): target <= 1 melanopic EDI lux

        Args:
            melanopic_edi: Current melanopic EDI in lux
            hours_to_sleep: Hours until target sleep time (negative = past bedtime)

        Returns:
            dict with zone, threshold, compliance, current_edi, advisory
        """
        if hours_to_sleep > 3:
            zone = "daytime"
            threshold = 250
            compliant = melanopic_edi >= threshold
            if compliant:
                advisory = "Good daytime light exposure. Bright light supports circadian alerting."
            else:
                advisory = (
                    f"Low daytime light ({melanopic_edi:.0f} lux). "
                    f"Aim for >= {threshold} melanopic EDI lux — step outside or use a bright light."
                )
        elif hours_to_sleep > 0:
            zone = "evening"
            threshold = 10
            compliant = melanopic_edi <= threshold
            if compliant:
                advisory = "Good evening dimming. Low light supports melatonin onset."
            else:
                advisory = (
                    f"Evening light too bright ({melanopic_edi:.0f} lux). "
                    f"Dim to <= {threshold} melanopic EDI lux to protect melatonin."
                )
        else:
            zone = "sleep"
            threshold = 1
            compliant = melanopic_edi <= threshold
            if compliant:
                advisory = "Dark sleep environment. Optimal for melatonin and sleep consolidation."
            else:
                advisory = (
                    f"Light exposure during sleep window ({melanopic_edi:.0f} lux). "
                    f"Aim for <= {threshold} melanopic EDI lux — use blackout curtains."
                )

        return {
            "zone": zone,
            "threshold": threshold,
            "compliance": compliant,
            "current_edi": melanopic_edi,
            "advisory": advisory,
        }

    def _interpolate_ed50(self, duration_h: float) -> float:
        """
        Log-linear interpolation of ED50 from Gimenez 2022 lookup table.

        For durations outside the 0.5-4.0h range, clamp to nearest value.
        """
        durations = sorted(self._ED50_TABLE.keys())
        ed50_values = [self._ED50_TABLE[d] for d in durations]

        # Clamp to range
        if duration_h <= durations[0]:
            return ed50_values[0]
        if duration_h >= durations[-1]:
            return ed50_values[-1]

        # Find surrounding points
        for i in range(len(durations) - 1):
            if durations[i] <= duration_h <= durations[i + 1]:
                # Log-linear interpolation
                log_ed50_low = np.log(ed50_values[i])
                log_ed50_high = np.log(ed50_values[i + 1])
                t = (duration_h - durations[i]) / (durations[i + 1] - durations[i])
                return float(np.exp(log_ed50_low + t * (log_ed50_high - log_ed50_low)))

        return ed50_values[-1]  # fallback

    def _age_factor(self, profile: Optional[LightProfile]) -> float:
        """
        Age-dependent melanopic sensitivity multiplier (Nagare 2019).

        Children have clearer lenses (more blue transmission),
        elderly have yellowed lenses (less blue transmission).
        """
        if profile is None:
            return 1.0

        if profile.age < 1 or profile.age > 120:
            return 1.0  # invalid age, use default

        factor = 1.0
        if profile.age < 18:
            factor = 1.5
        elif profile.age > 65:
            factor = 0.7

        if profile.light_sensitive:
            factor *= 1.3

        return factor

    def melatonin_suppression(
        self,
        melanopic_edi: float,
        duration_h: float,
        profile: Optional[LightProfile] = None,
    ) -> dict:
        """
        Predict melatonin suppression using 4-parameter logistic model.

        Model (Gimenez 2022):
            suppression = a + (c - a) / (1 + (ED50 / edi)^d)

        Parameters:
            a = 0.0  (floor, no suppression at zero light)
            c = 0.65 (ceiling, ~65% max suppression per West 2011)
            d = 1.2  (Hill coefficient / steepness)
            ED50 varies by exposure duration

        Age adjustment (Nagare 2019):
            <18 years:  effective EDI * 1.5 (clearer lens)
            >65 years:  effective EDI * 0.7 (yellowed lens)
            light_sensitive: additional * 1.3

        Args:
            melanopic_edi: Melanopic EDI in lux
            duration_h: Exposure duration in hours
            profile: Optional LightProfile for age/sensitivity adjustment

        Returns:
            dict with suppression_pct, onset_delay_min, ed50_used, age_factor, advisory
        """
        a = 0.0
        c = 0.65
        d = 1.2

        age_f = self._age_factor(profile)
        effective_edi = melanopic_edi * age_f

        ed50 = self._interpolate_ed50(duration_h)

        # 4-parameter logistic
        if effective_edi <= 0:
            suppression = 0.0
        else:
            suppression = a + (c - a) / (1 + (ed50 / effective_edi) ** d)

        suppression_pct = round(suppression * 100, 1)

        # Onset delay mapping: 65% suppression ~ 90min delay
        onset_delay_min = round(suppression_pct * 1.38, 1)

        # Advisory
        if suppression_pct < 10:
            advisory = (
                "rough risk estimate: minimal melatonin suppression under this model. "
                "Sleep effects may be small, but individual sensitivity varies."
            )
        elif suppression_pct < 30:
            advisory = (
                f"rough risk estimate: moderate suppression ({suppression_pct:.0f}%) with "
                f"an approximate {onset_delay_min:.0f} min sleep-onset delay. "
                "This is a heuristic, not a validated personal forecast."
            )
        else:
            advisory = (
                f"rough risk estimate: higher suppression ({suppression_pct:.0f}%) with "
                f"an approximate {onset_delay_min:.0f} min sleep-onset delay. "
                "Treat this as a heuristic and dim lights if the exposure is avoidable."
            )

        return merge_evidence(
            {
            "suppression_pct": suppression_pct,
            "onset_delay_min": onset_delay_min,
            "ed50_used": round(ed50, 1),
            "age_factor": round(age_f, 2),
            "model_type": "heuristic",
            "advisory": advisory,
            },
            LIGHT_MELATONIN_PROFILE,
        )

    def screen_impact(
        self,
        device: str,
        duration_h: float,
        hours_before_bed: float,
        profile: Optional[LightProfile] = None,
    ) -> dict:
        """
        Predict melatonin suppression from screen use (Spitschan 2023).

        Uses device-specific melanopic EDI values and feeds them through
        the Gimenez suppression model.

        Args:
            device: Device type ("phone", "tablet", "laptop", "tv", "e-reader")
            duration_h: Usage duration in hours
            hours_before_bed: Hours before target bedtime
            profile: Optional LightProfile for age/sensitivity adjustment

        Returns:
            dict with device, device_melanopic_edi, suppression_pct,
            onset_delay_min, advisory
        """
        device_edi = self._DEVICE_EDI.get(device.lower(), 60)

        suppression = self.melatonin_suppression(device_edi, duration_h, profile)

        if hours_before_bed <= 0:
            advisory = (
                f"You are using a {device} during your sleep window. "
                f"Any screen light now directly suppresses melatonin and disrupts sleep."
            )
        else:
            advisory = suppression["advisory"]

        return {
            "device": device,
            "device_melanopic_edi": device_edi,
            "suppression_pct": suppression["suppression_pct"],
            "onset_delay_min": suppression["onset_delay_min"],
            "advisory": advisory,
        }

    def lighting_risk(self, lamp_type: str, blue_filter: bool = False) -> dict:
        """
        Assess melatonin suppression risk of indoor lighting (Mouland 2025).

        Args:
            lamp_type: Lamp type ("cool_led", "cool_cfl", "warm_led",
                       "warm_cfl", "incandescent")
            blue_filter: Whether a blue-light filter is applied (halves suppression)

        Returns:
            dict with lamp_type, suppression_pct, risk_level,
            blue_filter_applied, advisory
        """
        suppression = self._LAMP_SUPPRESSION.get(lamp_type.lower(), 5.0)

        if blue_filter:
            suppression *= 0.5

        if suppression > 10:
            risk_level = "high"
        elif suppression >= 5:
            risk_level = "moderate"
        else:
            risk_level = "low"

        # Advisory
        if risk_level == "high":
            advisory = (
                f"{lamp_type.replace('_', ' ').title()} has high melanopic impact "
                f"({suppression:.1f}% suppression). Switch to warm lighting in the evening."
            )
        elif risk_level == "moderate":
            advisory = (
                f"{lamp_type.replace('_', ' ').title()} has moderate melanopic impact "
                f"({suppression:.1f}% suppression). Consider dimming or adding a blue filter."
            )
        else:
            advisory = (
                f"{lamp_type.replace('_', ' ').title()} has low melanopic impact "
                f"({suppression:.1f}% suppression). Acceptable for evening use."
            )

        return {
            "lamp_type": lamp_type,
            "suppression_pct": round(suppression, 1),
            "risk_level": risk_level,
            "blue_filter_applied": blue_filter,
            "advisory": advisory,
        }

    def daily_light_dose(self, readings: list[LightReading]) -> dict:
        """
        Calculate cumulative daily light dose from multiple readings.

        Separates daytime (outdoor + indoor) from evening (screen) exposure
        and checks if the daytime dose meets the minimum guideline of
        250 melanopic lux-hours.

        Args:
            readings: List of LightReading entries across the day

        Returns:
            dict with total_melanopic_lux_hours, daytime_dose, evening_dose,
            sufficient, advisory
        """
        daytime_dose = 0.0
        evening_dose = 0.0

        for r in readings:
            lux_hours = r.melanopic_edi_lux * r.duration_hours
            if r.source == "screen":
                evening_dose += lux_hours
            else:
                daytime_dose += lux_hours

        total = daytime_dose + evening_dose
        sufficient = daytime_dose >= 250

        if sufficient:
            advisory = (
                f"Daytime light dose adequate ({daytime_dose:.0f} lux-hours). "
                f"Good circadian entrainment signal."
            )
        else:
            advisory = (
                f"Daytime light dose low ({daytime_dose:.0f} lux-hours). "
                f"Aim for >= 250 melanopic lux-hours — prioritize morning outdoor light."
            )

        if evening_dose > 100:
            advisory += (
                f" Evening screen dose is high ({evening_dose:.0f} lux-hours). "
                f"Reduce screen time or use night mode."
            )

        return {
            "total_melanopic_lux_hours": round(total, 1),
            "daytime_dose": round(daytime_dose, 1),
            "evening_dose": round(evening_dose, 1),
            "sufficient": sufficient,
            "advisory": advisory,
        }


# ─── Example Usage ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = CircadianLightModel()

    # 1. Light zone check: 500 lux at 6h before bed
    print("=== Light Zone ===")
    zone = model.light_zone(500, hours_to_sleep=6)
    print(f"Zone: {zone['zone']}, Threshold: {zone['threshold']} lux")
    print(f"Compliant: {zone['compliance']}")
    print(f"Advisory: {zone['advisory']}")

    # 2. Screen impact: 2h tablet at 3h before bed, 25-year-old
    print("\n=== Screen Impact (25-year-old) ===")
    profile_25 = LightProfile(age=25)
    impact = model.screen_impact("tablet", duration_h=2.0, hours_before_bed=3.0, profile=profile_25)
    print(f"Device: {impact['device']}, EDI: {impact['device_melanopic_edi']} lux")
    print(f"Suppression: {impact['suppression_pct']}%")
    print(f"Onset delay: {impact['onset_delay_min']} min")
    print(f"Advisory: {impact['advisory']}")

    # 3. Screen impact: same for a 16-year-old (show age sensitivity)
    print("\n=== Screen Impact (16-year-old) ===")
    profile_16 = LightProfile(age=16)
    impact_teen = model.screen_impact("tablet", duration_h=2.0, hours_before_bed=3.0, profile=profile_16)
    print(f"Device: {impact_teen['device']}, EDI: {impact_teen['device_melanopic_edi']} lux")
    print(f"Suppression: {impact_teen['suppression_pct']}% (age factor: higher sensitivity)")
    print(f"Onset delay: {impact_teen['onset_delay_min']} min")
    print(f"Advisory: {impact_teen['advisory']}")

    # 4. Lighting risk: cool LED with and without blue filter
    print("\n=== Lighting Risk ===")
    risk_no_filter = model.lighting_risk("cool_led", blue_filter=False)
    risk_filter = model.lighting_risk("cool_led", blue_filter=True)
    print(f"Cool LED (no filter): {risk_no_filter['suppression_pct']}% — {risk_no_filter['risk_level']}")
    print(f"Cool LED (blue filter): {risk_filter['suppression_pct']}% — {risk_filter['risk_level']}")

    # 5. Daily light dose
    print("\n=== Daily Light Dose ===")
    readings = [
        LightReading(melanopic_edi_lux=10000, duration_hours=0.5, source="outdoor"),   # morning walk
        LightReading(melanopic_edi_lux=200, duration_hours=8.0, source="indoor_cool"),  # office
        LightReading(melanopic_edi_lux=100, duration_hours=2.0, source="screen"),       # evening tablet
    ]
    dose = model.daily_light_dose(readings)
    print(f"Total: {dose['total_melanopic_lux_hours']} lux-hours")
    print(f"Daytime: {dose['daytime_dose']} lux-hours")
    print(f"Evening: {dose['evening_dose']} lux-hours")
    print(f"Sufficient: {dose['sufficient']}")
    print(f"Advisory: {dose['advisory']}")
