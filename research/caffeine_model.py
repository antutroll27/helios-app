"""
HELIOS — Caffeine Pharmacokinetics Model
Personalized caffeine metabolism, sleep impact, and optimal cutoff timing.

References:
- Chinoy, E.D. et al. (2024) 'Caffeine timing and sleep: a dose-response analysis',
  SLEEP, 48, zsae230.
- Nehlig, A. et al. (2022) 'Interindividual differences in caffeine metabolism and
  factors driving caffeine consumption', Front Pharmacol, 12, 752826.
- Lin, Y.-S. et al. (2022) 'Steady-state caffeine accumulation and metabolite profiles',
  Front Nutrition, 8, 787225.
- Retey, J.V. et al. (2007) 'A genetic variation in the adenosine A2A receptor gene
  (ADORA2A) contributes to individual sensitivity to caffeine effects on sleep',
  Psychopharmacology, 190(4), pp. 271-273.
- Nehlig, A. (2018) 'Interindividual differences in caffeine metabolism and factors
  driving caffeine consumption', Genes Brain Behav, 17(6), e12462.
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class CaffeineProfile:
    """Individual caffeine metabolism profile — from genotype or self-report."""
    half_life_h: float = 5.0         # population default (Nehlig 2022)
    genotype: str = "unknown"        # CYP1A2: "fast" | "slow" | "unknown"
    sensitivity: str = "unknown"     # ADORA2A: "sensitive" | "insensitive" | "unknown"
    smoker: bool = False             # halves half-life (Nehlig 2022)
    oral_contraceptive: bool = False # doubles half-life


@dataclass
class CaffeineDose:
    """Single caffeine intake event."""
    mg: float
    time: datetime


# ─── Caffeine Pharmacokinetics Engine ───────────────────────────────────────────

class CaffeineModel:
    """
    First-order elimination model for caffeine pharmacokinetics.

    Caffeine follows well-characterized first-order kinetics with a
    population mean half-life of ~5 hours, but individual variation
    ranges from 1.5-9.5 hours depending on CYP1A2 genotype, smoking
    status, oral contraceptive use, and liver function.

    Core equation:
        remaining = dose * 0.5^(elapsed_hours / half_life)

    This model enables personalized caffeine cutoff recommendations
    instead of the generic "no coffee after 2pm" advice.
    """

    @staticmethod
    def personalized_half_life(profile: CaffeineProfile) -> float:
        """
        Calculate effective caffeine half-life based on individual factors.

        Modifiers (Nehlig 2022):
        - CYP1A2 fast metabolizer: ~3.0h (AA genotype)
        - CYP1A2 slow metabolizer: ~7.0h (AC/CC genotype)
        - Smoking: 0.5x (CYP1A2 induction by PAHs)
        - Oral contraceptives: 2.0x (CYP1A2 inhibition)

        Returns:
            Effective half-life in hours.
        """
        # Start with genotype-adjusted base
        genotype_map = {
            "fast": 3.0,
            "slow": 7.0,
            "unknown": profile.half_life_h,
        }
        half_life = genotype_map.get(profile.genotype, profile.half_life_h)

        # Apply modifiers multiplicatively
        if profile.smoker:
            half_life *= 0.5
        if profile.oral_contraceptive:
            half_life *= 2.0

        return half_life

    def remaining_caffeine(
        self,
        doses: list[CaffeineDose],
        target_time: datetime,
        profile: CaffeineProfile,
    ) -> dict:
        """
        Calculate total remaining caffeine at a target time.

        Uses first-order elimination kinetics summed across all doses.
        Guards against empty lists, non-positive doses, and future doses.

        Args:
            doses: List of caffeine intake events.
            target_time: When to calculate remaining caffeine.
            profile: Individual metabolism profile.

        Returns:
            dict with remaining_mg, per_dose_breakdown, advisory.
        """
        if not doses:
            return {
                "remaining_mg": 0.0,
                "per_dose_breakdown": [],
                "advisory": "No caffeine tracked.",
            }

        half_life = self.personalized_half_life(profile)
        breakdown = []
        total_remaining = 0.0

        for dose in doses:
            # Guard: skip non-positive doses
            if dose.mg <= 0:
                continue
            # Guard: skip doses after target time
            elapsed_h = (target_time - dose.time).total_seconds() / 3600
            if elapsed_h < 0:
                continue

            remaining = dose.mg * (0.5 ** (elapsed_h / half_life))
            total_remaining += remaining
            breakdown.append({
                "dose_mg": dose.mg,
                "time": dose.time.strftime("%H:%M"),
                "elapsed_h": round(elapsed_h, 1),
                "remaining_mg": round(remaining, 1),
            })

        total_remaining = round(total_remaining, 1)

        # Generate advisory
        if total_remaining > 100:
            advisory = (
                f"{total_remaining}mg remaining — significant level. "
                f"Expect sleep onset delay and reduced deep sleep."
            )
        elif total_remaining > 50:
            advisory = (
                f"{total_remaining}mg remaining — moderate level. "
                f"May affect sleep quality in sensitive individuals."
            )
        else:
            advisory = (
                f"{total_remaining}mg remaining — minimal level. "
                f"Unlikely to significantly affect sleep."
            )

        return {
            "remaining_mg": total_remaining,
            "per_dose_breakdown": breakdown,
            "advisory": advisory,
        }

    def sleep_impact(
        self,
        doses: list[CaffeineDose],
        bedtime: datetime,
        profile: CaffeineProfile,
    ) -> dict:
        """
        Predict caffeine impact on sleep quality at bedtime.

        Thresholds derived from Chinoy et al. (2024):
        - >100mg remaining: significant impact (+25min latency)
        - 50-100mg remaining: moderate impact (+12min latency)
        - <50mg remaining: minimal impact (+0min latency)

        ADORA2A-sensitive individuals (Retey 2007) use lower thresholds:
        - >75mg: significant, 35-75mg: moderate

        Returns:
            dict with impact_level, remaining_mg, sleep_latency_increase_min,
            fragmentation_risk, advisory.
        """
        result = self.remaining_caffeine(doses, bedtime, profile)
        remaining_mg = result["remaining_mg"]

        # Determine thresholds based on ADORA2A sensitivity
        is_sensitive = profile.sensitivity == "sensitive"

        if is_sensitive:
            sig_threshold = 75.0
            mod_threshold = 35.0
        else:
            sig_threshold = 100.0
            mod_threshold = 50.0

        # Classify impact
        if remaining_mg > sig_threshold:
            impact_level = "significant"
            latency_increase = 25
            fragmentation_risk = "high"
            advisory = (
                f"{remaining_mg}mg caffeine at bedtime — significant sleep disruption expected. "
                f"Chinoy 2024: +{latency_increase}min sleep onset latency, increased awakenings, "
                f"reduced slow-wave sleep."
            )
        elif remaining_mg > mod_threshold:
            impact_level = "moderate"
            latency_increase = 12
            fragmentation_risk = "moderate"
            advisory = (
                f"{remaining_mg}mg caffeine at bedtime — moderate impact expected. "
                f"May increase sleep onset by ~{latency_increase}min with mild fragmentation."
            )
        else:
            impact_level = "minimal"
            latency_increase = 0
            fragmentation_risk = "low"
            advisory = (
                f"{remaining_mg}mg caffeine at bedtime — minimal impact expected. "
                f"Below threshold for clinically significant sleep disruption."
            )

        if is_sensitive and remaining_mg > mod_threshold:
            advisory += " (ADORA2A-sensitive: using lower thresholds per Retey 2007)"

        return {
            "impact_level": impact_level,
            "remaining_mg": remaining_mg,
            "sleep_latency_increase_min": latency_increase,
            "fragmentation_risk": fragmentation_risk,
            "advisory": advisory,
        }

    def optimal_cutoff(
        self,
        bedtime: datetime,
        profile: CaffeineProfile,
        target_remaining_mg: float = 50.0,
        dose_mg: float = 200.0,
    ) -> dict:
        """
        Calculate the latest safe caffeine intake time before bed.

        Back-solves the elimination equation:
            hours_needed = half_life * log2(dose_mg / target_remaining_mg)
            cutoff_time = bedtime - hours_needed

        Calculates cutoffs for standard dose sizes (100mg, 200mg, 400mg).

        Args:
            bedtime: Target bedtime.
            profile: Individual metabolism profile.
            target_remaining_mg: Max acceptable caffeine at bedtime (default 50mg).
            dose_mg: Primary dose to recommend cutoff for (default 200mg).

        Returns:
            dict with cutoff_times, recommended, advisory.
        """
        half_life = self.personalized_half_life(profile)

        # Guard: invalid dose
        if dose_mg <= 0:
            return {
                "cutoff_times": {},
                "recommended": None,
                "advisory": "Error: dose_mg must be positive.",
            }

        standard_doses = [100, 200, 400]
        if dose_mg not in standard_doses:
            standard_doses.append(dose_mg)
            standard_doses.sort()

        cutoff_times = {}
        for d in standard_doses:
            # Guard: dose already below target
            if d <= target_remaining_mg:
                cutoff_times[f"{d}mg"] = "no restriction needed"
                continue

            hours_needed = half_life * math.log2(d / target_remaining_mg)
            cutoff_dt = bedtime - timedelta(hours=hours_needed)
            cutoff_times[f"{d}mg"] = cutoff_dt.strftime("%H:%M")

        # Recommended cutoff for the specified dose
        if dose_mg <= target_remaining_mg:
            recommended = "no restriction needed"
            advisory = (
                f"A {dose_mg}mg dose is already at or below the {target_remaining_mg}mg target — "
                f"no timing restriction needed."
            )
        else:
            hours_needed = half_life * math.log2(dose_mg / target_remaining_mg)
            cutoff_dt = bedtime - timedelta(hours=hours_needed)
            recommended = cutoff_dt.strftime("%H:%M")
            advisory = (
                f"With a {half_life:.1f}h half-life, a {dose_mg}mg dose needs "
                f"{hours_needed:.1f}h to decay to {target_remaining_mg}mg. "
                f"Last coffee by {recommended} for a {bedtime.strftime('%H:%M')} bedtime."
            )

        return {
            "cutoff_times": cutoff_times,
            "recommended": recommended,
            "half_life_h": half_life,
            "advisory": advisory,
        }

    def steady_state(
        self,
        daily_doses: list[CaffeineDose],
        profile: CaffeineProfile,
        days: int = 7,
    ) -> dict:
        """
        Simulate multi-day caffeine accumulation to steady state.

        Repeated daily dosing causes residual caffeine to accumulate
        until elimination rate matches intake rate (Lin 2022).
        This is clinically relevant for habitual consumers.

        Args:
            daily_doses: Doses consumed each day (times relative to day start).
            profile: Individual metabolism profile.
            days: Number of days to simulate (default 7).

        Returns:
            dict with peak_mg, trough_mg, accumulation_factor, days_to_clear,
            advisory.
        """
        if not daily_doses:
            return {
                "peak_mg": 0.0,
                "trough_mg": 0.0,
                "accumulation_factor": 1.0,
                "days_to_clear": 0,
                "advisory": "No daily caffeine intake specified.",
            }

        half_life = self.personalized_half_life(profile)

        # Normalize dose times to hours within a day (0-24)
        dose_schedule = []
        for dose in daily_doses:
            if dose.mg <= 0:
                continue
            hour_of_day = dose.time.hour + dose.time.minute / 60
            dose_schedule.append((hour_of_day, dose.mg))

        if not dose_schedule:
            return {
                "peak_mg": 0.0,
                "trough_mg": 0.0,
                "accumulation_factor": 1.0,
                "days_to_clear": 0,
                "advisory": "No valid caffeine doses to simulate.",
            }

        dose_schedule.sort(key=lambda x: x[0])

        # Simulate hour-by-hour for N days
        # Track caffeine level at each hour
        hours_total = days * 24
        levels = np.zeros(hours_total)
        current_level = 0.0

        for h in range(hours_total):
            day_hour = h % 24

            # Apply decay from previous hour
            if h > 0:
                current_level = current_level * (0.5 ** (1.0 / half_life))

            # Add any doses at this hour
            for dose_hour, dose_mg in dose_schedule:
                if abs(day_hour - dose_hour) < 0.5:  # within 30min window
                    current_level += dose_mg

            levels[h] = current_level

        # Extract metrics from the last simulated day
        last_day_levels = levels[-24:]
        peak_mg = round(float(np.max(last_day_levels)), 1)
        trough_mg = round(float(np.min(last_day_levels)), 1)

        # Accumulation factor: peak on last day vs single-day peak
        first_day_peak = float(np.max(levels[:24]))
        accumulation_factor = round(peak_mg / first_day_peak, 2) if first_day_peak > 0 else 1.0

        # Days to clear: how many days of zero intake to reach <5mg
        clear_level = peak_mg
        days_to_clear = 0
        while clear_level > 5.0 and days_to_clear < 30:
            clear_level *= 0.5 ** (24.0 / half_life)
            days_to_clear += 1

        # Advisory
        if accumulation_factor > 1.3:
            advisory = (
                f"Significant accumulation detected (factor {accumulation_factor}x). "
                f"Peak steady-state: {peak_mg}mg, trough: {trough_mg}mg. "
                f"Consider reducing afternoon doses to lower baseline (Lin 2022)."
            )
        else:
            advisory = (
                f"Minimal accumulation (factor {accumulation_factor}x). "
                f"Peak: {peak_mg}mg, trough: {trough_mg}mg. "
                f"Daily intake clears adequately between doses."
            )

        return {
            "peak_mg": peak_mg,
            "trough_mg": trough_mg,
            "accumulation_factor": accumulation_factor,
            "days_to_clear": days_to_clear,
            "advisory": advisory,
        }


# ─── Example Usage ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = CaffeineModel()

    # Night owl digital nomad in Da Nang — 1AM bedtime
    profile = CaffeineProfile(
        genotype="unknown",
        sensitivity="unknown",
        smoker=False,
        oral_contraceptive=False,
    )

    bedtime = datetime(2026, 4, 5, 1, 0)  # 1:00 AM

    doses = [
        CaffeineDose(mg=200, time=datetime(2026, 4, 4, 10, 0)),   # 10:00 AM coffee
        CaffeineDose(mg=200, time=datetime(2026, 4, 4, 14, 0)),   # 2:00 PM coffee
        CaffeineDose(mg=100, time=datetime(2026, 4, 4, 19, 0)),   # 7:00 PM tea
    ]

    print("=" * 60)
    print("HELIOS Caffeine Model — Night Owl Example")
    print("=" * 60)

    # 1. Remaining caffeine at bedtime
    remaining = model.remaining_caffeine(doses, bedtime, profile)
    print(f"\n--- Remaining Caffeine at {bedtime.strftime('%H:%M')} ---")
    print(f"Total: {remaining['remaining_mg']}mg")
    for entry in remaining["per_dose_breakdown"]:
        print(f"  {entry['dose_mg']}mg @ {entry['time']} -> {entry['remaining_mg']}mg ({entry['elapsed_h']}h elapsed)")
    print(f"Advisory: {remaining['advisory']}")

    # 2. Sleep impact
    impact = model.sleep_impact(doses, bedtime, profile)
    print(f"\n--- Sleep Impact ---")
    print(f"Impact level: {impact['impact_level']}")
    print(f"Sleep latency increase: +{impact['sleep_latency_increase_min']}min")
    print(f"Fragmentation risk: {impact['fragmentation_risk']}")
    print(f"Advisory: {impact['advisory']}")

    # 3. Optimal cutoff
    cutoff = model.optimal_cutoff(bedtime, profile, target_remaining_mg=50, dose_mg=200)
    print(f"\n--- Optimal Cutoff (target <50mg at bedtime) ---")
    print(f"Half-life: {cutoff['half_life_h']:.1f}h")
    print(f"Recommended cutoff (200mg): {cutoff['recommended']}")
    for dose_label, time_str in cutoff["cutoff_times"].items():
        print(f"  {dose_label}: last intake by {time_str}")
    print(f"Advisory: {cutoff['advisory']}")

    # 4. Steady state (7-day simulation)
    steady = model.steady_state(doses, profile, days=7)
    print(f"\n--- Steady State (7-day simulation) ---")
    print(f"Peak: {steady['peak_mg']}mg")
    print(f"Trough: {steady['trough_mg']}mg")
    print(f"Accumulation factor: {steady['accumulation_factor']}x")
    print(f"Days to clear (<5mg): {steady['days_to_clear']}")
    print(f"Advisory: {steady['advisory']}")
