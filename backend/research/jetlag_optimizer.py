"""
HELIOS — Jet Lag Optimizer
Kronauer/Jewett phase response curve for light-based circadian shifting,
with day-by-day recovery schedule generation.

References:
- Jewett, M.E. et al. (1997) 'Phase-amplitude resetting of the human circadian
  pacemaker via bright light: a further analysis', J Biological Rhythms, 12(4), pp. 319-341.
  (Kronauer mathematical model of the human circadian pacemaker)
- Eastman, C.I. & Burgess, H.J. (2009) 'How to travel the world without jet lag',
  Sleep Medicine Clinics, 4(2), pp. 241-255.
  (Practical PRC application: light timing rules for eastbound/westbound travel)
- Sack, R.L. (2010) 'Jet lag', New England Journal of Medicine, 362(5), pp. 440-447.
  (Clinical review: recovery rate ~1h/day westbound, ~1.5h/day eastbound with light)
- Burgess, H.J. et al. (2003) 'Bright light, dark and melatonin can promote circadian
  adaptation in night shift workers', Sleep Medicine Reviews, 7(5), pp. 407-420.
  (Melatonin timing rules aligned with PRC)
- Roenneberg, T. et al. (2019) 'Chronotype and social jetlag: a (self-) critical
  review', Biology, 8(3), 54.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Optional

from evidence_contract import EvidenceProfile, merge_evidence


JETLAG_EVIDENCE = EvidenceProfile(
    evidence_tier="B",
    effect_summary=(
        "Strategic bright light (>2500 lux) exposure and avoidance can shift the circadian "
        "clock ~1–2h/day; eastbound adaptation is slower than westbound"
    ),
    population_summary=(
        "Eastman & Burgess 2009 review (multiple controlled light studies); "
        "Sack 2010 NEJM clinical review; Burgess 2003 shift-worker cohorts"
    ),
    main_caveat=(
        "PRC is approximated piecewise — individual chronotype and prior light exposure "
        "history affect actual phase shift magnitude"
    ),
    uncertainty_factors=[
        "individual circadian amplitude", "chronotype", "prior light history",
        "melatonin timing compliance", "sleep opportunity windows during travel",
    ],
    claim_boundary=(
        "Use schedule as a guideline — adjust by ±1h based on subjective alertness and "
        "light availability at the destination"
    ),
)


# ─── Constants ────────────────────────────────────────────────────────────────

# Approximate advance/delay per day with optimised light strategy (Sack 2010)
_ADVANCE_RATE_H_PER_DAY = 1.5   # eastbound (phase advance)
_DELAY_RATE_H_PER_DAY   = 1.0   # westbound (phase delay; slower)

# Minimum lux for circadian light therapy (Eastman & Burgess 2009)
BRIGHT_LIGHT_LUX = 2500

# Chronotype offsets from mid-day anchor (hours shift to anchor light window)
_CHRONOTYPE_OFFSET_H = {
    "early": -1.0,
    "mid":    0.0,
    "late":  +1.0,
}


@dataclass
class DayProtocol:
    day: int
    date: date
    direction: str                  # 'advance' | 'delay'
    seek_light_start: str           # local time HH:MM
    seek_light_end: str             # local time HH:MM
    avoid_light_start: str          # local time HH:MM
    avoid_light_end: str            # local time HH:MM
    melatonin_time: Optional[str]   # local time HH:MM or None
    target_sleep: str               # local time HH:MM
    target_wake: str                # local time HH:MM
    shift_achieved_h: float         # cumulative phase shift by end of this day
    remaining_shift_h: float


@dataclass
class JetlagPlan:
    origin_tz: str
    destination_tz: str
    shift_h: float                  # positive = advance (eastbound), negative = delay
    direction: str                  # 'advance' | 'delay'
    n_days_to_adapt: int
    days: list[DayProtocol] = field(default_factory=list)


def _format_time(hour_float: float) -> str:
    """Convert decimal hour to HH:MM string, wrapping at 24h."""
    hour_float = hour_float % 24
    h = int(hour_float)
    m = int((hour_float - h) * 60)
    return f"{h:02d}:{m:02d}"


def generate_jetlag_plan(
    origin_offset_h: float,
    destination_offset_h: float,
    travel_date: date,
    usual_sleep_h: float = 23.0,
    usual_wake_h: float = 7.0,
    chronotype: str = "mid",
    use_melatonin: bool = True,
) -> dict:
    """
    Generate a day-by-day light/dark + melatonin schedule to minimise jet lag.

    Args:
        origin_offset_h: Origin UTC offset in hours (e.g. +7.0 for Bangkok).
        destination_offset_h: Destination UTC offset (e.g. +9.0 for Tokyo).
        travel_date: Date of departure.
        usual_sleep_h: Habitual sleep onset in decimal hours in origin timezone (e.g. 23.0).
        usual_wake_h: Habitual wake time in decimal hours in origin timezone (e.g. 7.0).
        chronotype: 'early' | 'mid' | 'late' — adjusts light window timing.
        use_melatonin: Whether to include melatonin timing recommendations.

    Returns:
        dict with plan details, DayProtocol list, and evidence_profile.
    """
    shift_h = destination_offset_h - origin_offset_h

    # Normalise to [-12, +12] — shortest path around the clock
    if shift_h > 12:
        shift_h -= 24
    elif shift_h < -12:
        shift_h += 24

    if shift_h == 0:
        return merge_evidence(
            {"valid": True, "message": "No time zone shift — no adaptation needed.", "n_days": 0, "days": []},
            JETLAG_EVIDENCE,
        )

    direction = "advance" if shift_h > 0 else "delay"
    abs_shift = abs(shift_h)
    rate = _ADVANCE_RATE_H_PER_DAY if direction == "advance" else _DELAY_RATE_H_PER_DAY
    n_days = max(1, round(abs_shift / rate))

    chrono_offset = _CHRONOTYPE_OFFSET_H.get(chronotype, 0.0)

    # Convert habitual times to destination timezone
    dest_sleep_h = (usual_sleep_h + shift_h) % 24
    dest_wake_h = (usual_wake_h + shift_h) % 24

    days: list[DayProtocol] = []
    shift_per_day = abs_shift / n_days

    for day_idx in range(n_days):
        day_num = day_idx + 1
        shift_so_far = shift_per_day * day_num
        remaining = max(0.0, abs_shift - shift_so_far)
        current_date = travel_date + timedelta(days=day_idx)

        # Fractional adaptation of sleep/wake toward destination times
        frac = day_num / n_days
        sleep_h = (usual_sleep_h + shift_h * frac) % 24
        wake_h = (usual_wake_h + shift_h * frac) % 24

        if direction == "advance":
            # Eastbound: seek morning light, avoid evening light (Eastman 2009)
            light_seek_start = (wake_h - 0.5 + chrono_offset) % 24
            light_seek_end = (wake_h + 3.0 + chrono_offset) % 24
            light_avoid_start = (sleep_h - 4.0) % 24
            light_avoid_end = sleep_h
            melatonin_h = (sleep_h - 0.5) % 24 if use_melatonin else None
        else:
            # Westbound: seek evening light, avoid morning light (Eastman 2009)
            light_seek_start = (sleep_h - 3.0) % 24
            light_seek_end = sleep_h
            light_avoid_start = wake_h
            light_avoid_end = (wake_h + 3.0) % 24
            melatonin_h = None  # melatonin less effective for phase delay

        days.append(DayProtocol(
            day=day_num,
            date=current_date,
            direction=direction,
            seek_light_start=_format_time(light_seek_start),
            seek_light_end=_format_time(light_seek_end),
            avoid_light_start=_format_time(light_avoid_start),
            avoid_light_end=_format_time(light_avoid_end),
            melatonin_time=_format_time(melatonin_h) if melatonin_h is not None else None,
            target_sleep=_format_time(sleep_h),
            target_wake=_format_time(wake_h),
            shift_achieved_h=round(shift_so_far, 2),
            remaining_shift_h=round(remaining, 2),
        ))

    payload = {
        "valid": True,
        "origin_offset_h": origin_offset_h,
        "destination_offset_h": destination_offset_h,
        "shift_h": round(shift_h, 2),
        "direction": direction,
        "n_days_to_adapt": n_days,
        "bright_light_target_lux": BRIGHT_LIGHT_LUX,
        "use_melatonin": use_melatonin,
        "days": [
            {
                "day": d.day,
                "date": d.date.isoformat(),
                "seek_light_start": d.seek_light_start,
                "seek_light_end": d.seek_light_end,
                "avoid_light_start": d.avoid_light_start,
                "avoid_light_end": d.avoid_light_end,
                "melatonin_time": d.melatonin_time,
                "target_sleep": d.target_sleep,
                "target_wake": d.target_wake,
                "shift_achieved_h": d.shift_achieved_h,
                "remaining_shift_h": d.remaining_shift_h,
            }
            for d in days
        ],
    }

    return merge_evidence(payload, JETLAG_EVIDENCE)
