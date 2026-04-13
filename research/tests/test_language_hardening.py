from datetime import datetime

from research.alcohol_model import AlcoholModel
from research.breathwork_model import BreathworkModel
from research.caffeine_model import CaffeineDose, CaffeineModel, CaffeineProfile
from research.light_model import CircadianLightModel
from research.nap_model import NapModel


def test_alcohol_sleep_impact_is_labeled_heuristic():
    result = AlcoholModel().sleep_impact(3, 4, 80.0, "male")
    assert result["model_type"] == "heuristic"
    assert "individual response varies" in result["advisory"]
    assert result["evidence_profile"]["evidence_tier"] == "B"
    assert "widmark" in result["method_summary"].lower()


def test_breathwork_response_does_not_claim_validated_personal_prediction():
    result = BreathworkModel().hrv_response("resonance", 5.5, 10, baseline_rmssd=38.0)
    assert result["model_type"] == "heuristic"
    assert "rough estimate" in result["advisory"]
    assert result["evidence_profile"]["evidence_tier"] == "B"
    assert "acute response" in result["evidence_profile"]["main_caveat"].lower()
    assert "personal biometric prediction" in result["evidence_profile"]["main_caveat"].lower()


def test_breathwork_invalid_parameters_preserve_evidence_contract():
    result = BreathworkModel().hrv_response("resonance", 5.5, 0, baseline_rmssd=38.0)
    assert result["model_type"] == "heuristic"
    assert result["evidence_profile"]["evidence_tier"] == "B"
    assert "must be positive" in result["advisory"].lower()


def test_caffeine_cutoff_uses_default_conservative_language():
    result = CaffeineModel().optimal_cutoff(
        datetime(2026, 4, 5, 23, 0), CaffeineProfile(), dose_mg=200
    )
    assert "default conservative estimate" in result["advisory"]
    assert "guarantee" not in result["advisory"].lower()


def test_caffeine_sleep_impact_keeps_heuristic_boundary():
    result = CaffeineModel().sleep_impact(
        [CaffeineDose(mg=200, time=datetime(2026, 4, 5, 14, 0))],
        datetime(2026, 4, 5, 23, 0),
        CaffeineProfile(),
    )
    assert result["evidence_profile"]["evidence_tier"] == "B"
    assert "latency" in result["evidence_profile"]["effect_summary"].lower()
    assert "fragmentation" in result["evidence_profile"]["effect_summary"].lower()
    assert "healthy adults" in result["evidence_profile"]["population_summary"].lower()
    assert "heuristic mapping" in result["evidence_profile"]["main_caveat"].lower()


def test_light_model_uses_risk_band_language():
    result = CircadianLightModel().melatonin_suppression(100, 2.0)
    assert result["model_type"] == "heuristic"
    assert "rough risk estimate" in result["advisory"]
    assert "heuristic" in result["evidence_profile"]["claim_boundary"].lower()


def test_nap_recommendation_does_not_treat_study_results_as_universal():
    result = NapModel().recommendation(
        14.0, 7.0, 23.0, 7.0, sleep_debt_hours=3.0, goal="alertness"
    )
    assert "study-specific" in result["advisory"]
    assert "universal" not in result["advisory"].lower()
    assert result["evidence_profile"]["evidence_tier"] == "B"
    assert "study-specific" in result["evidence_profile"]["main_caveat"].lower()
