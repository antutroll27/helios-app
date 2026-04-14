from backend.chat.prompt_builder import build_system_prompt


def test_prompt_does_not_invent_travel_advisories():
    prompt = build_system_prompt(
        lat=37.7749,
        lng=-122.4194,
        timezone="America/Los_Angeles",
        user_id="user-123",
    )
    lower_prompt = prompt.lower()

    assert "travel advisories" not in lower_prompt
    assert "travel safety" not in lower_prompt
    assert "factor stress from high-risk destinations" not in lower_prompt


def test_prompt_treats_geomagnetic_activity_as_uncertain_context():
    prompt = build_system_prompt(
        lat=37.7749,
        lng=-122.4194,
        timezone="America/Los_Angeles",
        user_id="user-123",
    )
    lower_prompt = prompt.lower()

    assert "observational context" in lower_prompt
    assert "individual relevance is uncertain" in lower_prompt
    assert "cortisol elevation" not in lower_prompt
    assert "hrv suppression" not in lower_prompt


def test_prompt_uses_real_context_values_instead_of_na_placeholders():
    prompt = build_system_prompt(
        lat=51.5,
        lng=-0.12,
        timezone="Europe/London",
        user_id="user-123",
        user_sleep_time="22:45",
        user_chronotype="late",
        solar_context={
            "phase": "Night",
            "elevation": -12.5,
            "sunrise": "06:08",
            "sunset": "19:47",
            "solar_noon": "12:58",
        },
        space_weather_context={
            "kp_index": 4.0,
            "label": "Active",
            "bz": -6.0,
            "solar_wind": 520,
            "advisory": "Observational context only",
        },
        environment_context={
            "uv_index": 0,
            "temperature": 18,
            "night_temp": 12,
            "aqi": 38,
            "humidity": 74,
        },
        protocol_context={
            "wake_window": "07:00-07:30",
            "caffeine_cutoff": "14:30",
            "peak_focus": "15:00-18:00",
            "wind_down": "21:30",
            "sleep_target": "22:45",
        },
    )
    lower_prompt = prompt.lower()

    assert "Elevation: -12.5" in prompt
    assert "Kp Index: 4.0 (Active)" in prompt
    assert "Temperature: 18" in prompt
    assert "Wake Window: 07:00-07:30" in prompt
    assert "Usual sleep time: 22:45" in prompt
    assert "data loading..." not in lower_prompt
    assert "n/a" not in lower_prompt


def test_prompt_uses_real_context_values_with_nested_user_context():
    prompt = build_system_prompt(
        lat=51.5,
        lng=-0.12,
        timezone="Europe/London",
        user_id="user-123",
        user_sleep_time="22:45",
        user_chronotype="late",
        solar_context={
            "phase": "Night",
            "elevation": -12.5,
            "sunrise": "06:08",
            "sunset": "19:47",
            "solar_noon": "12:58",
        },
        space_weather_context={
            "kp_index": 4.0,
            "label": "Active",
            "bz": -6.0,
            "solar_wind": 520,
            "advisory": "Observational context only",
        },
        environment_context={
            "uv_index": 0,
            "temperature": 18,
            "night_temp": 12,
            "aqi": 38,
            "humidity": 74,
        },
        protocol_context={
            "wake_window": "07:00",
            "caffeine_cutoff": "14:30",
            "peak_focus": "15:00-18:00",
            "wind_down": "21:30",
            "sleep_target": "22:45",
        },
        user_context={
            "sleep_time": "22:45",
            "chronotype": "late",
        },
    )
    lower_prompt = prompt.lower()

    assert "Elevation: -12.5" in prompt
    assert "Kp Index: 4.0 (Active)" in prompt
    assert "ADVISORY: Observational context only" in prompt
    assert "Wake Window: 07:00" in prompt
    assert "Usual sleep time: 22:45" in prompt
    assert "data loading..." not in lower_prompt
    assert "n/a" not in lower_prompt


def test_prompt_uses_unknown_for_missing_nested_context():
    prompt = build_system_prompt(
        lat=51.5,
        lng=-0.12,
        timezone="Europe/London",
        user_id="user-123",
    )
    lower_prompt = prompt.lower()

    assert "Unknown" in prompt
    assert "data loading..." not in lower_prompt
