from research.evidence_contract import EvidenceProfile, merge_evidence


def test_merge_evidence_adds_required_metadata():
    profile = EvidenceProfile(
        evidence_tier="B",
        effect_summary="+16 min total sleep time in insomnia-focused trials",
        population_summary="adults with insomnia symptoms or low magnesium intake",
        main_caveat="effect sizes are population-level and not diagnostic",
        uncertainty_factors=["baseline deficiency", "dose form"],
        claim_boundary="general wellness support only",
    )

    merged = merge_evidence({"model_type": "heuristic"}, profile)

    assert merged["evidence_profile"]["evidence_tier"] == "B"
    assert merged["evidence_profile"]["claim_boundary"] == "general wellness support only"
    assert merged["evidence_profile"]["uncertainty_factors"] == ["baseline deficiency", "dose form"]


def test_evidence_profile_rejects_invalid_tier():
    try:
        EvidenceProfile(
            evidence_tier="D",
            effect_summary="x",
            population_summary="y",
            main_caveat="z",
            uncertainty_factors=[],
            claim_boundary="wellness only",
        )
    except ValueError as exc:
        assert "evidence_tier" in str(exc)
    else:
        raise AssertionError("EvidenceProfile accepted an invalid tier")


def test_evidence_profile_rejects_blank_required_text():
    cases = {
        "effect_summary": "   ",
        "population_summary": "\n",
        "main_caveat": "\t",
        "claim_boundary": " ",
    }

    for field_name, blank_value in cases.items():
        kwargs = dict(
            evidence_tier="B",
            effect_summary="effect",
            population_summary="population",
            main_caveat="caveat",
            uncertainty_factors=["baseline deficiency"],
            claim_boundary="boundary",
        )
        kwargs[field_name] = blank_value

        try:
            EvidenceProfile(**kwargs)
        except ValueError as exc:
            assert field_name in str(exc)
        else:
            raise AssertionError(f"EvidenceProfile accepted blank {field_name}")
