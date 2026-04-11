from backend.chat.prompt_builder import build_system_prompt


def test_prompt_does_not_invent_travel_advisories():
    prompt = build_system_prompt(
        lat=37.7749,
        lng=-122.4194,
        timezone="America/Los_Angeles",
        user_id="user-123",
    )

    assert "travel advisories" not in prompt.lower()
    assert "travel safety" not in prompt.lower()
    assert "factor stress from high-risk destinations" not in prompt.lower()


def test_prompt_treats_geomagnetic_activity_as_uncertain_context():
    prompt = build_system_prompt(
        lat=37.7749,
        lng=-122.4194,
        timezone="America/Los_Angeles",
        user_id="user-123",
    )

    assert "observational context" in prompt.lower()
    assert "individual relevance is uncertain" in prompt.lower()
    assert "cortisol elevation" not in prompt.lower()
    assert "hrv suppression" not in prompt.lower()
