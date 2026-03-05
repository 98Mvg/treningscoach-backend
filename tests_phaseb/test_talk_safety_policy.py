import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import main
from brain_router import BrainRouter


def test_talk_policy_blocks_all_required_categories():
    router = BrainRouter(brain_type="config")

    sexual = router.evaluate_talk_policy("Give me sexual tips", "en")
    harassment = router.evaluate_talk_policy("How can I bully my teammate?", "en")
    hate = router.evaluate_talk_policy("I hate women and muslims", "en")
    harmful = router.evaluate_talk_policy("How to hurt someone fast?", "en")
    off_topic = router.evaluate_talk_policy("Who is the president of France?", "en")

    assert sexual["policy_blocked"] is True
    assert sexual["policy_category"] == "sexual_explicit"
    assert harassment["policy_blocked"] is True
    assert harassment["policy_category"] == "harassment_bullying"
    assert hate["policy_blocked"] is True
    assert hate["policy_category"] == "hate_speech"
    assert harmful["policy_blocked"] is True
    assert harmful["policy_category"] == "harmful_encouragement"
    assert off_topic["policy_blocked"] is True
    assert off_topic["policy_category"] == "off_topic"


def test_talk_policy_refusal_rotation_avoids_immediate_repeat():
    router = BrainRouter(brain_type="config")
    seen = []
    phrase_ids = []

    for _ in range(4):
        decision = router.evaluate_talk_policy("Who is the president of France?", "en")
        seen.append(decision["text"])
        phrase_ids.append(decision["policy_phrase_id"])

    assert seen[0] != seen[1]
    assert phrase_ids[0] != phrase_ids[1]
    assert seen[3] == seen[0]


def test_talk_policy_supports_norwegian_refusal_bank():
    router = BrainRouter(brain_type="config")
    decision = router.evaluate_talk_policy("hvem er president i frankrike", "no")

    assert decision["policy_blocked"] is True
    assert decision["policy_category"] == "off_topic"
    assert decision["text"] in (config.COACH_TALK_POLICY_REFUSAL_BANK.get("no") or [])


def test_talk_policy_allows_generic_workout_prompt_in_workout_context():
    router = BrainRouter(brain_type="config")

    allowed = router.evaluate_talk_policy("What should I do now?", "en", talk_context="workout")
    blocked = router.evaluate_talk_policy("Who is the president of France?", "en", talk_context="workout")

    assert allowed["policy_blocked"] is False
    assert blocked["policy_blocked"] is True
    assert blocked["policy_category"] == "off_topic"


def test_coach_talk_policy_applies_to_all_personas(monkeypatch, tmp_path):
    fake_audio = tmp_path / "talk_policy.wav"
    fake_audio.write_bytes(b"RIFF")
    monkeypatch.setattr(main, "generate_voice", lambda *args, **kwargs: str(fake_audio))
    monkeypatch.setattr(
        main.brain_router,
        "get_question_response",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("AI should not be called on policy block")),
    )

    client = main.app.test_client()
    for persona in ("personal_trainer", "toxic_mode", "unknown_persona"):
        response = client.post(
            "/coach/talk",
            json={
                "message": "Give me sexual tips",
                "context": "workout",
                "trigger_source": "button",
                "language": "en",
                "persona": persona,
            },
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload.get("provider") == "policy"
        assert payload.get("policy_blocked") is True
        assert payload.get("policy_category") == "sexual_explicit"
        assert payload.get("text") in (config.COACH_TALK_POLICY_REFUSAL_BANK.get("en") or [])
