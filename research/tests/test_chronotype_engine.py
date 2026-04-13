from datetime import datetime, timedelta

from research.chronotype_engine import ChronotypeEngine, SleepLog


def make_sleep_log(
    date_str: str,
    onset_hour: int,
    onset_minute: int,
    wake_hour: int,
    wake_minute: int,
    alarm_used=None,
    source: str = "manual",
) -> SleepLog:
    base = datetime.strptime(date_str, "%Y-%m-%d")
    sleep_onset = base.replace(hour=onset_hour, minute=onset_minute)
    wake_time = base.replace(hour=wake_hour, minute=wake_minute)
    if wake_time <= sleep_onset:
        wake_time += timedelta(days=1)

    total_sleep_min = int((wake_time - sleep_onset).total_seconds() // 60)
    return SleepLog(
        date=date_str,
        sleep_onset=sleep_onset,
        wake_time=wake_time,
        total_sleep_min=total_sleep_min,
        alarm_used=alarm_used,
        source=source,
    )


def test_chronotype_prefers_alarm_flags_when_available():
    engine = ChronotypeEngine()
    logs = [
        make_sleep_log("2026-04-06", 23, 0, 7, 0, alarm_used=True),
        make_sleep_log("2026-04-07", 0, 15, 9, 30, alarm_used=False),
        make_sleep_log("2026-04-08", 23, 10, 7, 5, alarm_used=True),
        make_sleep_log("2026-04-09", 0, 20, 9, 20, alarm_used=False),
        make_sleep_log("2026-04-11", 23, 20, 6, 50, alarm_used=True),
        make_sleep_log("2026-04-12", 0, 30, 9, 40, alarm_used=False),
    ]

    result = engine.chronotype_from_logs(logs, work_days={0, 1, 2, 3, 4})

    assert "error" not in result
    assert result["day_classification"] == {
        "method": "alarm_used",
        "work_count": 3,
        "free_count": 3,
    }
    assert result["confidence"] == "moderate"
    assert result["confidence_score"] == 0.65
    assert result["data_sufficiency"] == "minimum"
    assert result["wearable_support"] == "missing"


def test_chronotype_reports_low_confidence_for_irregular_schedule():
    engine = ChronotypeEngine()
    logs = [
        make_sleep_log("2026-04-06", 22, 0, 6, 0),
        make_sleep_log("2026-04-07", 0, 30, 9, 30),
        make_sleep_log("2026-04-08", 21, 45, 5, 45),
        make_sleep_log("2026-04-09", 2, 45, 10, 45),
        make_sleep_log("2026-04-10", 23, 15, 7, 15),
        make_sleep_log("2026-04-11", 1, 30, 10, 30),
        make_sleep_log("2026-04-12", 3, 30, 11, 30),
        make_sleep_log("2026-04-13", 0, 45, 8, 45),
    ]

    result = engine.chronotype_from_logs(logs, work_days={0, 1, 2, 3, 4})

    assert result["day_classification"]["method"] == "declared_work_days"
    assert result["confidence"] == "low"
    assert result["confidence_score"] == 0.35
    assert result["data_sufficiency"] == "limited"
    assert "Irregular schedule reduces chronotype confidence." in result["warnings"]


def test_chronotype_returns_error_without_reliable_free_day_proxy():
    engine = ChronotypeEngine()
    logs = [
        make_sleep_log("2026-04-06", 23, 0, 7, 0),
        make_sleep_log("2026-04-07", 23, 10, 7, 10),
        make_sleep_log("2026-04-08", 23, 20, 7, 0),
        make_sleep_log("2026-04-09", 23, 15, 7, 5),
        make_sleep_log("2026-04-10", 23, 5, 7, 15),
        make_sleep_log("2026-04-11", 23, 10, 7, 5),
    ]

    result = engine.chronotype_from_logs(logs, work_days=None)

    assert result["error"] == "No reliable free-day proxy"
    assert result["confidence"] == "low"
    assert result["confidence_score"] == 0.35
    assert result["data_sufficiency"] == "minimum"
    assert result["day_classification"] == {
        "method": "none",
        "work_count": 0,
        "free_count": 0,
    }
