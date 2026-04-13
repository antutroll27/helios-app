from datetime import datetime

from research.space_weather_bio import SpaceWeatherBioModel, SpaceWeatherReading


def test_kp_cognitive_advisory_uses_observational_not_deterministic_language():
    model = SpaceWeatherBioModel()
    advisory = model.kp_cognitive_advisory(6.0)

    assert advisory["evidence_level"] == "observational"
    assert "uncertain individual relevance" in advisory["advisory"]
    assert "likely" not in advisory["advisory"].lower()
    assert "expected" not in advisory["advisory"].lower()


def test_composite_disruption_is_labeled_exploratory():
    model = SpaceWeatherBioModel()
    result = model.composite_disruption(
        SpaceWeatherReading(
            kp_index=5.0,
            solar_wind_speed=650.0,
            bz=-12.0,
            timestamp=datetime(2026, 4, 5, 14, 0),
        )
    )

    assert result["model_type"] == "exploratory_heuristic"
    assert "not validated for individual prediction" in result["advisory"]
    assert result["evidence_profile"]["evidence_tier"] == "C"
    assert "exploratory geomagnetic context" in result["evidence_profile"]["effect_summary"].lower()
    assert "context only" in result["evidence_profile"]["claim_boundary"].lower()
