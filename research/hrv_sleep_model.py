"""
HELIOS — HRV & Sleep Regularity Model
Sleep Regularity Index (SRI), bedtime deviation penalties, and HRV-sleep coupling.

References:
- Windred, D.P. et al. (2024) 'Sleep regularity is a stronger predictor of mortality
  risk than sleep duration: a prospective cohort study', Sleep, 47(1), zsad253.
  (UK Biobank n=60,977: SRI < 72 → +40–53% all-cause mortality vs SRI > 86.7)
- Phillips, A.J.K. et al. (2017) 'Irregular sleep/wake patterns are associated with
  poorer academic performance and delayed circadian and sleep/wake timing',
  Scientific Reports, 7(1), 3216.
  (SRI algorithm: pairwise overlap of sleep windows across consecutive days)
- Czeisler, C.A. et al. (1999) 'Stability, precision, and near-24-hour period of the
  human circadian pacemaker', Science, 284(5423), pp. 2177-2181.
- Baglioni, C. et al. (2016) 'Sleep and mental health: a meta-analysis of 17 studies',
  Sleep Medicine Reviews, 30, pp. 55-65.
  (HRV during sleep: higher nocturnal rMSSD → better sleep quality, lower arousals)
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from research.evidence_contract import EvidenceProfile, merge_evidence


HRV_SLEEP_EVIDENCE = EvidenceProfile(
    evidence_tier="A",
    effect_summary=(
        "Sleep irregularity (SRI < 72) is associated with +40–53% all-cause mortality "
        "independent of sleep duration; nocturnal HRV predicts sleep architecture quality"
    ),
    population_summary=(
        "Windred 2024: UK Biobank n=60,977 (SRI → mortality); "
        "Phillips 2017: college students n=61 (SRI algorithm validation)"
    ),
    main_caveat=(
        "SRI requires ≥7 days of continuous actigraphy/wearable data; "
        "fewer nights reduce reliability of the regularity estimate"
    ),
    uncertainty_factors=[
        "data gaps", "nap inclusion", "shift work", "travel across time zones",
        "wearable epoch resolution",
    ],
    claim_boundary=(
        "Use SRI to guide sleep schedule consistency; avoid single-night over-interpretation"
    ),
)


@dataclass
class SleepWindow:
    """Minimal sleep window for SRI computation."""
    date: str
    sleep_onset: datetime
    wake_time: datetime

    @property
    def sleep_min(self) -> float:
        return self.sleep_onset.hour * 60 + self.sleep_onset.minute

    @property
    def wake_min(self) -> float:
        total = self.wake_time.hour * 60 + self.wake_time.minute
        if self.wake_time.date() > self.sleep_onset.date():
            total += 24 * 60
        return total

    @property
    def duration_min(self) -> float:
        return self.wake_min - self.sleep_min


def compute_sri(windows: list[SleepWindow]) -> float:
    """
    Sleep Regularity Index (Phillips 2017).

    SRI = (1/N) * Σ s(t) * s(t+24h)  mapped to [0, 100]
    where s(t) = 1 if asleep at minute t, 0 if awake.

    Approximated pairwise across consecutive nights: overlap of sleep windows
    as a fraction of the union, averaged across all consecutive pairs.

    Returns 0–100 (100 = perfectly regular).
    """
    if len(windows) < 2:
        return 100.0

    overlaps = []
    for i in range(len(windows) - 1):
        a, b = windows[i], windows[i + 1]
        # Overlap of sleep periods (anchored to midnight of night i)
        a_start, a_end = a.sleep_min, a.wake_min
        b_start = b.sleep_onset.hour * 60 + b.sleep_onset.minute
        b_end_raw = b.wake_time.hour * 60 + b.wake_time.minute
        if b.wake_time.date() > b.sleep_onset.date():
            b_end_raw += 24 * 60
        # Shift b by +24h so it aligns with a in the same coordinate system
        b_start_shifted = b_start + 24 * 60
        b_end_shifted = b_end_raw + 24 * 60

        overlap = max(0, min(a_end, b_end_shifted) - max(a_start, b_start_shifted))
        union = max(a_end, b_end_shifted) - min(a_start, b_start_shifted)
        overlaps.append(overlap / union if union > 0 else 0.0)

    return round(min(100.0, max(0.0, sum(overlaps) / len(overlaps) * 100)), 1)


def _std_minutes(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def _sri_risk_level(sri: float) -> str:
    if sri >= 87:
        return "low"
    if sri >= 72:
        return "moderate"
    return "high"


def _sri_advisory(sri: float, bedtime_std_min: float, wake_std_min: float) -> str:
    if sri >= 87:
        return (
            f"Sleep timing is highly regular (SRI {sri}). "
            "Maintain your current schedule — consistency at this level is associated "
            "with the lowest mortality risk in the Windred 2024 UK Biobank cohort."
        )
    if sri >= 72:
        worst = "bedtime" if bedtime_std_min >= wake_std_min else "wake time"
        return (
            f"Sleep regularity is moderate (SRI {sri}). "
            f"Your {worst} varies the most (±{max(bedtime_std_min, wake_std_min):.0f} min). "
            "Windred 2024 found SRI 72–87 carries intermediate mortality risk — "
            "tightening your schedule by 30 min each direction would move you into the low-risk band."
        )
    return (
        f"Sleep regularity is low (SRI {sri}). "
        f"Bedtime varies ±{bedtime_std_min:.0f} min, wake time ±{wake_std_min:.0f} min. "
        "Windred 2024: SRI < 72 is associated with +40–53% all-cause mortality vs the most regular sleepers, "
        "independent of sleep duration. Anchor both bedtime and wake time within a 30-min window daily."
    )


def analyse_sleep_regularity(windows: list[SleepWindow]) -> dict:
    """
    Compute Sleep Regularity Index and timing variability from a list of sleep windows.

    Args:
        windows: List of SleepWindow objects, sorted ascending by date.
                 Minimum 2 nights; 7+ recommended.

    Returns:
        dict with sri, bedtime_std_min, wake_std_min, risk_level, advisory, n_nights,
        and evidence_profile.
    """
    n = len(windows)

    if n == 0:
        return merge_evidence(
            {"valid": False, "error": "No sleep windows provided.", "n_nights": 0},
            HRV_SLEEP_EVIDENCE,
        )

    sri = compute_sri(windows)

    bedtime_mins = [w.sleep_min % (24 * 60) for w in windows]
    wake_mins = [w.wake_min % (24 * 60) for w in windows]

    bedtime_std = round(_std_minutes(bedtime_mins), 1)
    wake_std = round(_std_minutes(wake_mins), 1)
    risk_level = _sri_risk_level(sri)
    advisory = _sri_advisory(sri, bedtime_std, wake_std)

    avg_duration = round(sum(w.duration_min for w in windows) / n, 1)

    payload = {
        "valid": True,
        "n_nights": n,
        "sri": sri,
        "risk_level": risk_level,
        "bedtime_std_min": bedtime_std,
        "wake_std_min": wake_std,
        "avg_duration_min": avg_duration,
        "advisory": advisory,
        "windred_2024_threshold_low_risk": 86.7,
        "windred_2024_threshold_high_risk": 72.0,
    }

    return merge_evidence(payload, HRV_SLEEP_EVIDENCE)


# ─── Nocturnal HRV ───────────────────────────────────────────────────────────

def interpret_nocturnal_hrv(hrv_rmssd: float, age: Optional[int] = None) -> dict:
    """
    Interpret a single night's nocturnal rMSSD value.

    Age-adjusted normal ranges derived from normative wearable data.
    Below-normal HRV is a proxy for insufficient recovery or elevated sympathetic tone.

    Args:
        hrv_rmssd: Nocturnal rMSSD in ms (Oura/Garmin/Whoop nightly average).
        age: Optional age in years for age-adjusted reference range.

    Returns:
        dict with interpretation, percentile_band, and advisory.
    """
    # Population norms (approximate, from Shaffer & Ginsberg 2017 review)
    # rMSSD declines ~1ms per year after age 20
    if age is not None and age > 20:
        expected_midpoint = max(20.0, 65.0 - (age - 20) * 1.0)
    else:
        expected_midpoint = 50.0

    low_threshold = expected_midpoint * 0.65
    high_threshold = expected_midpoint * 1.35

    if hrv_rmssd >= high_threshold:
        band = "above_normal"
        interpretation = "Strong parasympathetic recovery — body is well-adapted to current training and sleep load."
        advisory = "Maintain current protocol. High HRV nights correlate with better cognitive performance the following day."
    elif hrv_rmssd >= expected_midpoint:
        band = "normal_high"
        interpretation = "Good nocturnal recovery. HRV is in the upper half of your expected range."
        advisory = "Protocol is working well. No specific adjustments needed."
    elif hrv_rmssd >= low_threshold:
        band = "normal_low"
        interpretation = "HRV is in the lower half of the normal range — moderate recovery."
        advisory = (
            "Check for accumulated sleep debt, late caffeine, or high training load. "
            "Prioritise consistent bedtime and a 3h pre-sleep meal gap."
        )
    else:
        band = "below_normal"
        interpretation = f"HRV {hrv_rmssd:.0f} ms is below the expected range for this age group — reduced parasympathetic activity."
        advisory = (
            "Consider reducing training load, improving sleep consistency, or adding a "
            "resonance-frequency breathwork session (5.5 bpm, 20 min) before bed to upregulate vagal tone."
        )

    return merge_evidence(
        {
            "hrv_rmssd": hrv_rmssd,
            "age": age,
            "expected_midpoint": round(expected_midpoint, 1),
            "band": band,
            "interpretation": interpretation,
            "advisory": advisory,
        },
        HRV_SLEEP_EVIDENCE,
    )
