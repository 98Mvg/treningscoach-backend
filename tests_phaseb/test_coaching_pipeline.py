from coaching_pipeline import run


class _VoiceStub:
    def __init__(self, should_be_silent=False, reason="no_change"):
        self._should_be_silent = should_be_silent
        self._reason = reason

    def should_stay_silent(self, **kwargs):
        return self._should_be_silent, self._reason


def _never_should_coach(**kwargs):
    return False, "zone_no_change"


def _always_override(**kwargs):
    return True, "max_silence_override"


def _fallback_interval(_phase):
    return 35.0


def test_pipeline_first_breath_wins_with_welcome_owner():
    decision = run(
        is_first_breath=True,
        zone_mode_active=True,
        zone_tick={"events": [], "coach_text": "zone text"},
        breath_quality_state="reliable",
        speech_decision_owner_v2=True,
        unified_zone_router_active=True,
        voice_intelligence=_VoiceStub(),
        should_coach_speak_fn=_never_should_coach,
        apply_max_silence_override_fn=_always_override,
        phase_fallback_interval_seconds_fn=_fallback_interval,
        breath_data={},
        phase="warmup",
        last_coaching="",
        elapsed_seconds=5,
        last_breath=None,
        coaching_history=[],
        training_level="beginner",
        session_id="s1",
        elapsed_since_last=None,
        max_silence_seconds=30.0,
    )

    assert decision.speak is True
    assert decision.owner == "welcome"
    assert decision.reason == "welcome_message"
    assert decision.mark_first_breath_consumed is True
    assert decision.mark_use_welcome_phrase is True


def test_pipeline_zone_owner_bypasses_max_silence_override_when_unified_router_active():
    decision = run(
        is_first_breath=False,
        zone_mode_active=True,
        zone_tick={
            "should_speak": False,
            "primary_event_type": "zone_no_change",
            "reason": "zone_no_change",
            "events": [],
        },
        breath_quality_state="reliable",
        speech_decision_owner_v2=True,
        unified_zone_router_active=True,
        voice_intelligence=_VoiceStub(),
        should_coach_speak_fn=_never_should_coach,
        apply_max_silence_override_fn=_always_override,
        phase_fallback_interval_seconds_fn=_fallback_interval,
        breath_data={},
        phase="intense",
        last_coaching="",
        elapsed_seconds=100,
        last_breath=None,
        coaching_history=[],
        training_level="intermediate",
        session_id="s2",
        elapsed_since_last=90.0,
        max_silence_seconds=30.0,
    )

    assert decision.speak is False
    assert decision.owner == "zone_event"
    assert decision.owner_base == "zone_event"
    assert decision.reason == "zone_no_change"


def test_pipeline_applies_max_silence_override_for_legacy_breath_path():
    decision = run(
        is_first_breath=False,
        zone_mode_active=False,
        zone_tick=None,
        breath_quality_state="reliable",
        speech_decision_owner_v2=True,
        unified_zone_router_active=False,
        voice_intelligence=_VoiceStub(should_be_silent=False),
        should_coach_speak_fn=_never_should_coach,
        apply_max_silence_override_fn=_always_override,
        phase_fallback_interval_seconds_fn=_fallback_interval,
        breath_data={"signal_quality": 0.8},
        phase="intense",
        last_coaching="",
        elapsed_seconds=200,
        last_breath=None,
        coaching_history=[],
        training_level="intermediate",
        session_id="s3",
        elapsed_since_last=90.0,
        max_silence_seconds=30.0,
    )

    assert decision.speak is True
    assert decision.owner == "max_silence_override"
    assert decision.reason == "max_silence_override"
