"""
HELIOS — Chronotype Engine
Munich Chronotype Questionnaire (MCTQ) implementation + wearable analysis.

References:
- Roenneberg, T., Wirz-Justice, A. and Merrow, M. (2003) 'Life between clocks:
  daily temporal patterns of human chronotypes', J Biological Rhythms, 18(1), pp. 80-90.
- Roenneberg, T. et al. (2012) 'Social jetlag and obesity', Current Biology, 22(10), pp. 939-943.
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional


@dataclass
class SleepLog:
    """Single night of sleep data — from wearable or manual entry."""
    date: str
    sleep_onset: datetime
    wake_time: datetime
    total_sleep_min: int
    deep_sleep_min: Optional[int] = None
    rem_sleep_min: Optional[int] = None
    hrv_avg: Optional[float] = None
    skin_temp_delta: Optional[float] = None
    resting_hr: Optional[float] = None
    sleep_score: Optional[int] = None
    source: str = "manual"  # "oura" | "fitbit" | "garmin" | "samsung" | "manual"


@dataclass
class ProtocolLog:
    """What HELIOS recommended vs what actually happened."""
    date: str
    recommended_sleep: datetime
    actual_sleep: datetime
    recommended_wake: datetime
    actual_wake: datetime
    kp_index: float
    disruption_score: int
    social_jet_lag_min: int


# ─── Munich Chronotype Questionnaire (MCTQ) ──────────────────────────────────

class ChronotypeEngine:
    """
    Implements the MCTQ algorithm to derive chronotype from sleep timing data.

    The core metric is MSF (Mid-Sleep on Free Days) — the midpoint of sleep
    on days without alarm constraints. This is the most validated non-invasive
    marker of internal circadian phase.

    Chronotype distribution (Roenneberg 2003):
    - Population MSF follows a near-Gaussian distribution
    - Mean MSF ≈ 4:00-5:00 (varies by age, sex, latitude)
    - Standard deviation ≈ 1.5 hours
    """

    @staticmethod
    def mid_sleep(onset: datetime, wake: datetime) -> datetime:
        """
        Calculate the midpoint of a sleep episode.
        Handles overnight sleep (onset PM, wake AM).
        """
        duration = (wake - onset).total_seconds()
        if duration < 0:
            duration += 86400  # add 24h if crossing midnight
        return onset + timedelta(seconds=duration / 2)

    @staticmethod
    def sleep_duration_hours(onset: datetime, wake: datetime) -> float:
        """Sleep duration in hours, handling midnight crossing."""
        duration = (wake - onset).total_seconds()
        if duration < 0:
            duration += 86400
        return duration / 3600

    def calculate_msf(self, free_day_onset: datetime, free_day_wake: datetime) -> datetime:
        """
        MSF = Mid-Sleep on Free Days.
        The gold-standard MCTQ metric for chronotype determination.
        """
        return self.mid_sleep(free_day_onset, free_day_wake)

    def calculate_msf_sc(
        self,
        free_onset: datetime,
        free_wake: datetime,
        work_onset: datetime,
        work_wake: datetime,
    ) -> datetime:
        """
        MSFsc = MSF corrected for sleep debt.

        On free days, people often oversleep to compensate for work-day
        sleep debt. MSFsc corrects for this by subtracting half the
        difference between free-day and work-day sleep duration.

        This is the recommended metric for chronotype assessment.
        """
        sd_free = self.sleep_duration_hours(free_onset, free_wake)
        sd_work = self.sleep_duration_hours(work_onset, work_wake)
        avg_sleep = (sd_free + sd_work) / 2

        msf = self.calculate_msf(free_onset, free_wake)

        if sd_free > avg_sleep:
            correction = timedelta(hours=(sd_free - avg_sleep) / 2)
            return msf - correction
        return msf

    def social_jet_lag_hours(
        self,
        work_onset: datetime,
        work_wake: datetime,
        free_onset: datetime,
        free_wake: datetime,
    ) -> float:
        """
        Social Jet Lag (SJL) in hours.

        The absolute difference between mid-sleep on work days and free days.
        SJL > 1h is clinically significant.
        SJL > 2h is associated with increased metabolic and cardiovascular risk.
        """
        msw = self.mid_sleep(work_onset, work_wake)
        msf = self.mid_sleep(free_onset, free_wake)

        # Compare time-of-day only
        msw_min = msw.hour * 60 + msw.minute
        msf_min = msf.hour * 60 + msf.minute
        diff = abs(msf_min - msw_min)
        if diff > 720:
            diff = 1440 - diff
        return diff / 60

    def chronotype_label(self, msf_hour: float) -> str:
        """
        Maps MSF (in decimal hours) to a chronotype label.
        Based on Roenneberg (2003) population distribution.
        """
        if msf_hour < 2.5:
            return "Extreme Early"
        if msf_hour < 3.5:
            return "Moderate Early"
        if msf_hour < 4.5:
            return "Intermediate"
        if msf_hour < 5.5:
            return "Moderate Late"
        if msf_hour < 6.5:
            return "Late"
        return "Extreme Late"

    def chronotype_from_logs(self, logs: list[SleepLog], work_days: Optional[set[int]] = None) -> dict:
        """
        Derive chronotype from a collection of sleep logs.

        Args:
            logs: List of SleepLog entries (minimum 7 days recommended)
            work_days: Set of weekday indices (0=Monday) that are work days

        Returns:
            dict with chronotype analysis results
        """
        if work_days is None:
            work_days = {0, 1, 2, 3, 4}

        if len(logs) < 3:
            return {"error": "Need at least 3 days of data", "confidence": "low"}

        work_logs = [l for l in logs if datetime.strptime(l.date, "%Y-%m-%d").weekday() in work_days]
        free_logs = [l for l in logs if datetime.strptime(l.date, "%Y-%m-%d").weekday() not in work_days]

        if not work_logs or not free_logs:
            return {"error": "Need both work and free day data", "confidence": "low"}

        # Average work-day timing
        avg_work_onset = self._average_time([l.sleep_onset for l in work_logs])
        avg_work_wake = self._average_time([l.wake_time for l in work_logs])

        # Average free-day timing
        avg_free_onset = self._average_time([l.sleep_onset for l in free_logs])
        avg_free_wake = self._average_time([l.wake_time for l in free_logs])

        # Core metrics
        msf = self.calculate_msf(avg_free_onset, avg_free_wake)
        msf_sc = self.calculate_msf_sc(avg_free_onset, avg_free_wake, avg_work_onset, avg_work_wake)
        sjl = self.social_jet_lag_hours(avg_work_onset, avg_work_wake, avg_free_onset, avg_free_wake)

        msf_hour = msf_sc.hour + msf_sc.minute / 60

        return {
            "chronotype": self.chronotype_label(msf_hour),
            "msf": msf.strftime("%H:%M"),
            "msf_sc": msf_sc.strftime("%H:%M"),
            "social_jet_lag_hours": round(sjl, 1),
            "sjl_risk": "low" if sjl < 1 else "moderate" if sjl < 2 else "high",
            "avg_work_sleep": avg_work_onset.strftime("%H:%M"),
            "avg_work_wake": avg_work_wake.strftime("%H:%M"),
            "avg_free_sleep": avg_free_onset.strftime("%H:%M"),
            "avg_free_wake": avg_free_wake.strftime("%H:%M"),
            "confidence": "high" if len(logs) >= 14 else "moderate" if len(logs) >= 7 else "low",
            "data_days": len(logs),
        }

    @staticmethod
    def _average_time(times: list[datetime]) -> datetime:
        """Average a list of datetimes by circular mean of time-of-day."""
        if not times:
            return datetime.now().replace(hour=0, minute=0)
        angles = [((t.hour * 60 + t.minute) / 1440) * 2 * np.pi for t in times]
        sin_avg = np.mean(np.sin(angles))
        cos_avg = np.mean(np.cos(angles))
        avg_angle = np.arctan2(sin_avg, cos_avg)
        if avg_angle < 0:
            avg_angle += 2 * np.pi
        avg_minutes = int((avg_angle / (2 * np.pi)) * 1440) % 1440
        return times[0].replace(hour=avg_minutes // 60, minute=avg_minutes % 60, second=0)


# ─── Protocol Effectiveness Scoring ──────────────────────────────────────────

class ProtocolScorer:
    """
    Scores how well the HELIOS protocol worked based on sleep outcomes.

    This closes the feedback loop: recommend → measure → adjust.
    Currently only available in clinical chronobiology research settings.
    HELIOS makes it accessible to anyone with a wearable.
    """

    def effectiveness_score(self, protocol: ProtocolLog, sleep: SleepLog) -> dict:
        """
        Multi-dimensional effectiveness score.

        Returns 0.0-1.0 per dimension and an overall composite score.
        """
        scores = {}

        # 1. Sleep timing accuracy (did they hit the target?)
        target_min = protocol.recommended_sleep.hour * 60 + protocol.recommended_sleep.minute
        actual_min = sleep.sleep_onset.hour * 60 + sleep.sleep_onset.minute
        diff = abs(target_min - actual_min)
        if diff > 720:
            diff = 1440 - diff
        scores["timing_accuracy"] = max(0, 1 - (diff / 60))  # 1h off = 0

        # 2. Sleep duration adequacy (7-9h is optimal for adults)
        optimal_min = 480  # 8h
        duration_diff = abs(sleep.total_sleep_min - optimal_min)
        scores["duration"] = max(0, 1 - (duration_diff / 120))

        # 3. HRV vs baseline (if available)
        if sleep.hrv_avg and sleep.hrv_avg > 0:
            # Higher HRV = better recovery. Normalize against population avg ~40ms
            scores["hrv"] = min(sleep.hrv_avg / 60, 1.0)

        # 4. Deep sleep proportion (target: >15% of total)
        if sleep.deep_sleep_min is not None and sleep.total_sleep_min > 0:
            deep_pct = sleep.deep_sleep_min / sleep.total_sleep_min
            scores["deep_sleep"] = min(deep_pct / 0.20, 1.0)  # 20% = perfect score

        # 5. REM proportion (target: >20% of total)
        if sleep.rem_sleep_min is not None and sleep.total_sleep_min > 0:
            rem_pct = sleep.rem_sleep_min / sleep.total_sleep_min
            scores["rem_sleep"] = min(rem_pct / 0.25, 1.0)  # 25% = perfect score

        # Composite
        if scores:
            scores["composite"] = round(float(np.mean(list(scores.values()))), 3)
        else:
            scores["composite"] = 0.5  # no data

        return scores

    def trend_analysis(self, history: list[dict]) -> dict:
        """
        Analyze protocol effectiveness over time.
        Input: list of daily effectiveness scores (from effectiveness_score).
        """
        if len(history) < 3:
            return {"trend": "insufficient_data", "days": len(history)}

        composites = [h.get("composite", 0.5) for h in history]

        # Simple linear regression for trend
        x = np.arange(len(composites))
        slope = np.polyfit(x, composites, 1)[0]

        return {
            "trend": "improving" if slope > 0.01 else "declining" if slope < -0.01 else "stable",
            "slope_per_day": round(float(slope), 4),
            "current_score": round(composites[-1], 3),
            "7d_average": round(float(np.mean(composites[-7:])), 3) if len(composites) >= 7 else None,
            "best_day": round(max(composites), 3),
            "worst_day": round(min(composites), 3),
            "days_tracked": len(history),
        }


# ─── Circadian Phase Estimator ───────────────────────────────────────────────

class CircadianPhaseEstimator:
    """
    Estimates circadian phase markers from wearable data.

    Uses skin temperature, HRV, and activity patterns as proxies
    for core body temperature rhythm — the gold standard for
    circadian phase assessment in clinical settings.

    Reference:
    - Refinetti, R. (2006) Circadian Physiology, 2nd ed. CRC Press.
    - Martinez-Nicolas, A. et al. (2011) 'Circadian monitoring as aging
      predictor', Scientific Reports.
    """

    def estimate_cbt_minimum(self, skin_temps: list[tuple[datetime, float]]) -> Optional[datetime]:
        """
        Estimate core body temperature minimum (CBTmin) from skin temperature.

        CBTmin typically occurs ~2h before habitual wake time.
        Skin temperature is anti-phase to core temp (rises when core drops).
        So skin temp MAXIMUM ≈ CBTmin.

        This is the most important circadian phase marker:
        - Light before CBTmin → phase delay
        - Light after CBTmin → phase advance
        """
        if len(skin_temps) < 24:
            return None

        # Find the maximum skin temperature (= CBTmin proxy)
        max_temp = max(skin_temps, key=lambda x: x[1])
        return max_temp[0]

    def dim_light_melatonin_onset_estimate(
        self,
        avg_sleep_onset: datetime,
        chronotype: str = "intermediate"
    ) -> datetime:
        """
        Estimate DLMO (Dim Light Melatonin Onset) from sleep timing.

        DLMO typically occurs 2-3 hours before habitual sleep onset.
        This is the clinical gold standard for circadian phase, but
        requires salivary melatonin assay. We estimate from behavior.

        Chronotype adjustment:
        - Early types: DLMO ~2h before sleep
        - Intermediate: ~2.5h before sleep
        - Late types: ~3h before sleep
        """
        offsets = {
            "Extreme Early": 1.5,
            "Moderate Early": 2.0,
            "Intermediate": 2.5,
            "Moderate Late": 3.0,
            "Late": 3.0,
            "Extreme Late": 3.5,
            # Simplified labels from user store
            "early": 2.0,
            "intermediate": 2.5,
            "late": 3.0,
        }
        offset_hours = offsets.get(chronotype, 2.5)
        return avg_sleep_onset - timedelta(hours=offset_hours)


# ─── Example Usage ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine = ChronotypeEngine()

    # Example: night owl digital nomad in Da Nang
    work_onset = datetime(2026, 3, 28, 1, 30)   # sleeps at 1:30 AM on work nights
    work_wake = datetime(2026, 3, 28, 9, 0)      # wakes at 9:00 AM
    free_onset = datetime(2026, 3, 29, 3, 0)     # sleeps at 3:00 AM on weekends
    free_wake = datetime(2026, 3, 29, 11, 30)    # wakes at 11:30 AM

    msf = engine.calculate_msf(free_onset, free_wake)
    sjl = engine.social_jet_lag_hours(work_onset, work_wake, free_onset, free_wake)
    msf_hour = msf.hour + msf.minute / 60
    chrono = engine.chronotype_label(msf_hour)

    print(f"Mid-Sleep Free Days (MSF): {msf.strftime('%H:%M')}")
    print(f"Chronotype: {chrono}")
    print(f"Social Jet Lag: {sjl:.1f} hours")
    print(f"Risk Level: {'low' if sjl < 1 else 'moderate' if sjl < 2 else 'HIGH'}")

    # Estimate DLMO
    estimator = CircadianPhaseEstimator()
    dlmo = estimator.dim_light_melatonin_onset_estimate(free_onset, chrono)
    print(f"Estimated DLMO: {dlmo.strftime('%H:%M')}")
