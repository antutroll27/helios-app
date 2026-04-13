"""
HELIOS — Alcohol Sleep Impact Model
Personalized blood alcohol pharmacokinetics, sleep architecture disruption,
optimal cutoff timing, and HRV recovery estimation.

References:
- Pietila, J. et al. (2018) 'Acute effect of alcohol intake on cardiovascular
  autonomic regulation during the first hours of sleep in a large real-world
  sample of Finnish employees', JMIR Mental Health, 5(1), e23.
- Thakkar, M.M. et al. (2015) 'Alcohol disrupts sleep homeostasis',
  Alcohol, 49(4), pp. 299-310.
- He, S. et al. (2019) 'Alcohol and sleep-related problems',
  Current Opinion in Psychology, 30, pp. 117-122.
- Colrain, I.M. et al. (2014) 'Alcohol and the sleeping brain',
  Handbook of Clinical Neurology, 125, pp. 415-431.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

from research.evidence_contract import EvidenceProfile, merge_evidence


@dataclass
class DrinkerProfile:
    """Individual alcohol metabolism profile."""
    body_weight_kg: float = 70.0
    sex: str = "male"              # "male" | "female"
    baseline_rmssd: float = 42.0   # resting HRV in ms (population median)


ALCOHOL_SLEEP_PROFILE = EvidenceProfile(
    evidence_tier="B",
    effect_summary="Drink-count HRV bins plus BAC-informed REM reduction and fragmentation risk",
    population_summary="Oura observational cohorts plus controlled alcohol and sleep literature",
    main_caveat="BAC math is stronger than the sleep-architecture forecast built on top of it",
    uncertainty_factors=["sex", "body mass", "meal timing", "clearance rate", "habitual tolerance"],
    claim_boundary="General next-night risk guidance only",
)


# ─── Alcohol Pharmacokinetics & Sleep Impact Engine ───────────────────────────

class AlcoholModel:
    """
    Widmark-based BAC model with sleep architecture impact predictions.

    Blood alcohol concentration follows the Widmark equation with linear
    elimination at ~0.015 g/dL/h. Sleep impact is derived from Pietila 2018
    (n=4,098 Oura/Firstbeat nights), Thakkar 2015 (sleep homeostasis),
    and Colrain 2014 (sleep architecture dose-response).

    Core equation (Widmark):
        BAC = (drinks * 14g) / (weight_kg * r * 10) - 0.015 * hours
        where r = 0.68 (male) or 0.55 (female)

    This model enables personalized alcohol cutoff recommendations
    and next-day HRV recovery timelines for circadian protocol adjustment.
    """

    # Standard drink = 14g pure ethanol (NIAAA definition)
    GRAMS_PER_DRINK = 14.0

    # Widmark distribution factors
    DISTRIBUTION_FACTOR = {"male": 0.68, "female": 0.55}

    # Linear elimination rate (g/dL per hour)
    ELIMINATION_RATE = 0.015

    # Minimal-impact BAC threshold
    MINIMAL_IMPACT_BAC = 0.02

    @staticmethod
    def _distribution_factor(sex: str) -> float:
        """Return Widmark distribution factor for sex."""
        return AlcoholModel.DISTRIBUTION_FACTOR.get(sex, 0.68)

    def blood_alcohol_content(
        self,
        drinks: float,
        body_weight_kg: float,
        sex: str,
        hours_elapsed: float,
    ) -> dict:
        """
        Calculate blood alcohol concentration using the Widmark equation.

        BAC = (drinks * 14g) / (weight_kg * r * 10) - 0.015 * hours
        where r is the sex-dependent distribution factor.

        Guards:
        - BAC floors at 0.0 (cannot go negative after full clearance).
        - Non-positive drinks or weight return zero BAC.

        Args:
            drinks: Number of standard drinks (1 drink = 14g ethanol).
            body_weight_kg: Body weight in kilograms.
            sex: "male" or "female" (determines distribution factor).
            hours_elapsed: Hours since first drink.

        Returns:
            dict with bac, drinks, hours_to_clearance, advisory.
        """
        # Guard: non-positive inputs
        if drinks <= 0 or body_weight_kg <= 0:
            return {
                "bac": 0.0,
                "drinks": drinks,
                "hours_to_clearance": 0.0,
                "advisory": "No alcohol intake recorded.",
            }

        r = self._distribution_factor(sex)
        peak_bac = (drinks * self.GRAMS_PER_DRINK) / (body_weight_kg * r * 10)
        bac = peak_bac - self.ELIMINATION_RATE * hours_elapsed

        # Guard: floor at zero
        bac = max(bac, 0.0)
        bac = round(bac, 4)

        # Hours until full clearance from current BAC
        hours_to_clearance = round(bac / self.ELIMINATION_RATE, 1) if bac > 0 else 0.0

        # Advisory
        if bac >= 0.08:
            advisory = (
                f"BAC {bac:.3f} — legally impaired in most jurisdictions. "
                f"Significant cognitive and motor impairment. "
                f"~{hours_to_clearance}h until full clearance."
            )
        elif bac >= 0.04:
            advisory = (
                f"BAC {bac:.3f} — mild impairment. "
                f"Sleep quality will be notably affected if consumed near bedtime. "
                f"~{hours_to_clearance}h until full clearance."
            )
        elif bac > 0:
            advisory = (
                f"BAC {bac:.3f} — low level, approaching clearance. "
                f"~{hours_to_clearance}h remaining."
            )
        else:
            advisory = "BAC 0.000 — alcohol fully cleared from bloodstream."

        return {
            "bac": bac,
            "drinks": drinks,
            "hours_to_clearance": hours_to_clearance,
            "advisory": advisory,
        }

    def sleep_impact(
        self,
        drinks: float,
        hours_before_bed: float,
        body_weight_kg: float,
        sex: str,
        baseline_rmssd: float = 42.0,
    ) -> dict:
        """
        Predict alcohol's impact on sleep architecture and HRV.

        Uses BAC at bedtime to estimate:
        - HRV suppression (Pietila 2018, n=4,098 Oura nights):
            1-2 drinks: -9.3% RMSSD
            3-4 drinks: -24.0% RMSSD
            5+ drinks:  -39.2% RMSSD
        - REM suppression (Colrain 2014, Thakkar 2015):
            BAC 0.04-0.06: ~20% REM reduction
            BAC 0.06-0.10: ~30-40% REM reduction
            BAC >0.10:     ~50% REM reduction
        - Deep sleep: sedation increases SWS in first half, but
          +50% awakenings in second half at BAC >0.06 (He 2019)
        - Resting heart rate: ~3-5 bpm increase per 0.02 BAC

        Args:
            drinks: Number of standard drinks consumed.
            hours_before_bed: Hours between last drink and bedtime.
            body_weight_kg: Body weight in kilograms.
            sex: "male" or "female".
            baseline_rmssd: Baseline resting RMSSD in ms (default 42.0).

        Returns:
            dict with bac_at_bedtime, rmssd_pct_change, rem_reduction_pct,
            deep_sleep_change, second_half_awakenings, rhr_increase_bpm,
            advisory.
        """
        # Calculate BAC at bedtime
        bac_result = self.blood_alcohol_content(
            drinks, body_weight_kg, sex, hours_before_bed
        )
        bac = bac_result["bac"]

        # --- HRV impact (Pietila 2018) ---
        if drinks <= 0:
            rmssd_pct_change = 0.0
        elif drinks <= 2:
            rmssd_pct_change = -9.3
        elif drinks <= 4:
            rmssd_pct_change = -24.0
        else:
            rmssd_pct_change = -39.2

        # --- REM suppression (Colrain 2014, Thakkar 2015) ---
        if bac <= 0.0:
            rem_reduction_pct = 0.0
        elif bac < 0.04:
            # Linear interpolation from 0 to 20% across 0.00-0.04
            rem_reduction_pct = round((bac / 0.04) * 20.0, 1)
        elif bac <= 0.06:
            rem_reduction_pct = 20.0
        elif bac <= 0.10:
            # Linear interpolation from 30% to 40% across 0.06-0.10
            fraction = (bac - 0.06) / 0.04
            rem_reduction_pct = round(30.0 + fraction * 10.0, 1)
        else:
            rem_reduction_pct = 50.0

        # --- Deep sleep changes ---
        if bac > 0.02:
            deep_sleep_change = "increased_first_half"
        else:
            deep_sleep_change = "normal"

        # --- Second-half awakenings ---
        if bac > 0.06:
            second_half_awakenings = "+50%"
        elif bac > 0.03:
            second_half_awakenings = "+20-30%"
        elif bac > 0.0:
            second_half_awakenings = "minimal increase"
        else:
            second_half_awakenings = "no change"

        # --- RHR increase (~3-5 bpm per 0.02 BAC) ---
        rhr_increase_bpm = round((bac / 0.02) * 4.0, 1) if bac > 0 else 0.0

        # --- Advisory ---
        if bac >= 0.06:
            advisory = (
                f"BAC {bac:.3f} at bedtime — severe sleep disruption expected. "
                f"Pietila 2018: HRV suppressed {rmssd_pct_change}%, "
                f"REM reduced ~{rem_reduction_pct}%, +50% second-half awakenings "
                f"(Colrain 2014). Expect fragmented sleep and next-day fatigue."
            )
        elif bac >= 0.03:
            advisory = (
                f"BAC {bac:.3f} at bedtime — moderate sleep disruption. "
                f"HRV suppressed {rmssd_pct_change}%, REM reduced ~{rem_reduction_pct}%. "
                f"Deep sleep may increase initially but second half fragmented "
                f"(He 2019, Thakkar 2015)."
            )
        elif bac > 0:
            advisory = (
                f"BAC {bac:.3f} at bedtime — mild impact. "
                f"HRV slightly suppressed ({rmssd_pct_change}%), "
                f"minimal REM disruption. Sleep architecture mostly preserved."
            )
        else:
            advisory = (
                "BAC cleared before bedtime — no direct alcohol impact on tonight's sleep. "
                "HRV may still be slightly suppressed if consumption was heavy "
                "(Pietila 2018)."
            )

        advisory += " This is a citation-informed heuristic and individual response varies."

        method_summary = (
            "Widmark BAC math is the stronger part of the model; the sleep forecast "
            "and HRV effects are heuristic overlays built on top of it."
        )

        return merge_evidence(
            {
            "bac_at_bedtime": bac,
            "rmssd_pct_change": rmssd_pct_change,
            "rem_reduction_pct": rem_reduction_pct,
            "deep_sleep_change": deep_sleep_change,
            "second_half_awakenings": second_half_awakenings,
            "rhr_increase_bpm": rhr_increase_bpm,
            "method_summary": method_summary,
            "model_type": "heuristic",
            "advisory": advisory,
            },
            ALCOHOL_SLEEP_PROFILE,
        )

    def optimal_cutoff(
        self,
        drinks: float,
        body_weight_kg: float,
        sex: str,
        bedtime_hours: float = 23.0,
    ) -> dict:
        """
        Calculate the latest safe time to stop drinking before bed.

        Finds when BAC decays to 0.02 (minimal impact threshold),
        then subtracts from bedtime to get the cutoff time.

        Args:
            drinks: Number of standard drinks planned.
            body_weight_kg: Body weight in kilograms.
            sex: "male" or "female".
            bedtime_hours: Bedtime as hour of day (e.g. 23.0 = 11 PM).

        Returns:
            dict with cutoff_time, hours_before_bed, bac_at_bedtime_if_now,
            advisory.
        """
        # Guard: no drinks
        if drinks <= 0:
            return {
                "cutoff_time": "no restriction",
                "hours_before_bed": 0.0,
                "bac_at_bedtime_if_now": 0.0,
                "advisory": "No alcohol planned — no cutoff needed.",
            }

        r = self._distribution_factor(sex)
        peak_bac = (drinks * self.GRAMS_PER_DRINK) / (body_weight_kg * r * 10)

        # Hours from peak BAC to reach minimal-impact threshold (0.02)
        if peak_bac <= self.MINIMAL_IMPACT_BAC:
            return {
                "cutoff_time": "no restriction",
                "hours_before_bed": 0.0,
                "bac_at_bedtime_if_now": peak_bac,
                "advisory": (
                    f"Peak BAC {peak_bac:.3f} is already at or below the "
                    f"{self.MINIMAL_IMPACT_BAC} minimal-impact threshold — "
                    f"no timing restriction needed."
                ),
            }

        hours_to_threshold = (peak_bac - self.MINIMAL_IMPACT_BAC) / self.ELIMINATION_RATE
        hours_to_threshold = round(hours_to_threshold, 1)

        # Cutoff time = bedtime - hours_to_threshold
        cutoff_hour = bedtime_hours - hours_to_threshold
        # Handle day wraparound
        if cutoff_hour < 0:
            cutoff_hour += 24.0

        # Format as HH:MM
        cutoff_h = int(cutoff_hour)
        cutoff_m = int((cutoff_hour - cutoff_h) * 60)
        cutoff_time = f"{cutoff_h:02d}:{cutoff_m:02d}"

        # BAC at bedtime if drinking right now (0h elapsed)
        bac_at_bedtime_if_now = round(peak_bac, 4)

        # Bedtime formatted
        bed_h = int(bedtime_hours)
        bed_m = int((bedtime_hours - bed_h) * 60)
        bedtime_str = f"{bed_h:02d}:{bed_m:02d}"

        advisory = (
            f"With {drinks} drinks, peak BAC is {peak_bac:.3f}. "
            f"Need {hours_to_threshold}h to decay to {self.MINIMAL_IMPACT_BAC} threshold. "
            f"Last drink by {cutoff_time} for a {bedtime_str} bedtime."
        )

        return {
            "cutoff_time": cutoff_time,
            "hours_before_bed": hours_to_threshold,
            "bac_at_bedtime_if_now": bac_at_bedtime_if_now,
            "advisory": advisory,
        }

    def recovery_timeline(
        self,
        drinks: float,
        body_weight_kg: float,
        sex: str,
    ) -> dict:
        """
        Estimate full physiological recovery timeline after drinking.

        BAC clearance follows linear Widmark elimination (~0.015/h).
        HRV recovery takes longer — Pietila 2018 found autonomic
        function typically returns to baseline by the second night
        post-consumption, regardless of dose.

        Args:
            drinks: Number of standard drinks consumed.
            body_weight_kg: Body weight in kilograms.
            sex: "male" or "female".

        Returns:
            dict with hours_to_bac_zero, nights_to_hrv_recovery, advisory.
        """
        # Guard: no drinks
        if drinks <= 0:
            return {
                "hours_to_bac_zero": 0.0,
                "nights_to_hrv_recovery": 0,
                "advisory": "No alcohol consumed — no recovery needed.",
            }

        r = self._distribution_factor(sex)
        peak_bac = (drinks * self.GRAMS_PER_DRINK) / (body_weight_kg * r * 10)
        hours_to_zero = round(peak_bac / self.ELIMINATION_RATE, 1)

        # HRV recovery (Pietila 2018):
        # Light drinking (1-2): typically 1 night
        # Moderate-heavy (3+): typically 2 nights
        if drinks <= 2:
            nights_to_hrv_recovery = 1
        else:
            nights_to_hrv_recovery = 2

        if drinks >= 5:
            advisory = (
                f"Heavy consumption ({drinks} drinks). Peak BAC {peak_bac:.3f}, "
                f"~{hours_to_zero}h to full clearance. "
                f"HRV typically returns to baseline by night {nights_to_hrv_recovery} "
                f"(Pietila 2018). Consider lighter protocol targets tomorrow — "
                f"cognitive performance may be impaired for 24-36h (Thakkar 2015)."
            )
        elif drinks >= 3:
            advisory = (
                f"Moderate consumption ({drinks} drinks). Peak BAC {peak_bac:.3f}, "
                f"~{hours_to_zero}h to full clearance. "
                f"HRV should recover by night {nights_to_hrv_recovery} (Pietila 2018). "
                f"Tomorrow's morning protocol may need adjustment."
            )
        else:
            advisory = (
                f"Light consumption ({drinks} drinks). Peak BAC {peak_bac:.3f}, "
                f"~{hours_to_zero}h to full clearance. "
                f"HRV recovery expected by next night (Pietila 2018). "
                f"Minimal impact on tomorrow's circadian protocol."
            )

        return {
            "hours_to_bac_zero": hours_to_zero,
            "nights_to_hrv_recovery": nights_to_hrv_recovery,
            "advisory": advisory,
        }


# ─── Example Usage ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = AlcoholModel()

    # Scenario: 3 beers at 8 PM, 80kg male, midnight bedtime
    drinks = 3
    body_weight_kg = 80.0
    sex = "male"
    drinking_hour = 20.0   # 8 PM
    bedtime_hour = 24.0    # midnight
    hours_before_bed = bedtime_hour - drinking_hour  # 4 hours

    print("=" * 60)
    print("HELIOS Alcohol Model — Evening Drinks Example")
    print("=" * 60)
    print(f"Scenario: {drinks} beers at 8 PM, {body_weight_kg}kg {sex}, midnight bedtime")

    # 1. BAC at bedtime (4 hours after drinking)
    bac = model.blood_alcohol_content(drinks, body_weight_kg, sex, hours_before_bed)
    print(f"\n--- BAC at Bedtime ({hours_before_bed}h after drinking) ---")
    print(f"BAC: {bac['bac']:.4f}")
    print(f"Hours to full clearance: {bac['hours_to_clearance']}h")
    print(f"Advisory: {bac['advisory']}")

    # 2. Sleep impact
    impact = model.sleep_impact(drinks, hours_before_bed, body_weight_kg, sex)
    print(f"\n--- Sleep Impact ---")
    print(f"BAC at bedtime: {impact['bac_at_bedtime']:.4f}")
    print(f"HRV (RMSSD) change: {impact['rmssd_pct_change']}%")
    print(f"REM reduction: {impact['rem_reduction_pct']}%")
    print(f"Deep sleep: {impact['deep_sleep_change']}")
    print(f"Second-half awakenings: {impact['second_half_awakenings']}")
    print(f"RHR increase: +{impact['rhr_increase_bpm']} bpm")
    print(f"Advisory: {impact['advisory']}")

    # 3. Optimal cutoff
    cutoff = model.optimal_cutoff(drinks, body_weight_kg, sex, bedtime_hours=24.0)
    print(f"\n--- Optimal Cutoff (BAC < 0.02 at bedtime) ---")
    print(f"Last drink by: {cutoff['cutoff_time']}")
    print(f"Hours needed before bed: {cutoff['hours_before_bed']}h")
    print(f"Peak BAC if drinking now: {cutoff['bac_at_bedtime_if_now']:.4f}")
    print(f"Advisory: {cutoff['advisory']}")

    # 4. Recovery timeline
    recovery = model.recovery_timeline(drinks, body_weight_kg, sex)
    print(f"\n--- Recovery Timeline ---")
    print(f"Hours to BAC zero: {recovery['hours_to_bac_zero']}h")
    print(f"Nights to HRV recovery: {recovery['nights_to_hrv_recovery']}")
    print(f"Advisory: {recovery['advisory']}")
