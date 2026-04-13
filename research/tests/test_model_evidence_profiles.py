from datetime import datetime

from research.alcohol_model import AlcoholModel
from research.caffeine_model import CaffeineDose, CaffeineModel, CaffeineProfile
from research.light_model import CircadianLightModel


def test_caffeine_sleep_impact_exposes_tier_b_boundary():
    result = CaffeineModel().sleep_impact(
        doses=[CaffeineDose(mg=200, time=datetime(2026, 4, 5, 14, 0))],
        bedtime=datetime(2026, 4, 5, 23, 0),
        profile=CaffeineProfile(),
    )

    profile = result["evidence_profile"]
    assert profile["evidence_tier"] == "B"
    assert "healthy adults" in profile["population_summary"].lower()
    assert "heuristic mapping" in profile["main_caveat"].lower()


def test_light_model_exposes_tier_b_delay_boundary():
    result = CircadianLightModel().melatonin_suppression(100, 2.0)

    profile = result["evidence_profile"]
    assert profile["evidence_tier"] == "B"
    assert "heuristic" in profile["claim_boundary"].lower()
    assert "healthy adults and adolescents" in profile["population_summary"].lower()


def test_alcohol_sleep_impact_marks_bac_math_as_stronger_than_sleep_forecast():
    result = AlcoholModel().sleep_impact(3, 4, 80.0, "male")

    profile = result["evidence_profile"]
    assert profile["evidence_tier"] == "B"
    assert "widmark" in result["method_summary"].lower()
    assert "sleep-architecture forecast" in profile["main_caveat"].lower()
