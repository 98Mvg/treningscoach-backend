from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_audio_pack_tools_exist():
    assert (REPO_ROOT / "tools" / "generate_audio_pack.py").exists()
    assert (REPO_ROOT / "tools" / "select_core_bundle.py").exists()


def test_requirements_include_boto3_for_r2_upload():
    requirements = _read("requirements.txt")
    assert "boto3" in requirements


def test_env_examples_expose_r2_audio_pack_keys():
    expected = [
        "R2_BUCKET_NAME=",
        "R2_ACCOUNT_ID=",
        "R2_ACCESS_KEY_ID=",
        "R2_SECRET_ACCESS_KEY=",
        "R2_PUBLIC_URL=",
        "AUDIO_PACK_VERSION=",
    ]
    for file in [".env.example", "backend/.env.example"]:
        content = _read(file)
        for key in expected:
            assert key in content


def test_config_exposes_r2_audio_pack_settings():
    content = _read("config.py")
    assert "R2_BUCKET_NAME" in content
    assert "R2_ACCOUNT_ID" in content
    assert "R2_ACCESS_KEY_ID" in content
    assert "R2_SECRET_ACCESS_KEY" in content
    assert "R2_PUBLIC_URL" in content
    assert "AUDIO_PACK_VERSION" in content


def test_workout_event_router_is_local_first_not_audio_url_gated():
    content = _read("TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift")
    assert "if response.audioURL == nil" not in content
    assert 'return (false, "event_router_no_audio")' not in content
    assert "playCoachAudio(" in content
    assert "localPackFileURL(" in content
    assert "downloadAudioPackFileIfNeeded(" in content


def test_dynamic_countdown_phrase_ids_bypass_local_pack_and_use_backend_tts():
    content = _read("TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift")
    assert 'utteranceID?.hasSuffix(".dynamic") == true' in content
    assert 'reason=dynamic_phrase' in content


def test_workout_event_mapping_uses_phrase_catalog_ids():
    content = _read("TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift")
    expected_ids = [
        "zone.phase.warmup.1",
        "zone.main_started.1",
        "zone.phase.cooldown.1",
        "zone.workout_finished.1",
        "zone.in_zone.default.1",
        "zone.above.default.1",
        "zone.below.default.1",
        "zone.countdown.30",
        "zone.countdown.15",
        "zone.countdown.5",
        "zone.countdown.start",
        "zone.countdown.halfway.dynamic",
        "zone.countdown.session_halfway.dynamic",
        "zone.hr_poor_timing.1",
        "zone.structure.work.1",
        "zone.structure.recovery.1",
        "zone.structure.steady.1",
        "zone.structure.finish.1",
    ]
    for phrase_id in expected_ids:
        assert phrase_id in content


def test_workout_event_mapping_uses_zone_silence_for_low_urgency_instruction():
    content = _read("TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift")
    assert 'case "max_silence_go_by_feel":' in content
    assert 'case "max_silence_breath_guide":' in content
    assert '"zone.silence.work.1"' in content
    assert '"zone.silence.rest.1"' in content
    assert '"zone.silence.default.1"' in content


def test_workout_event_mapping_covers_no_hr_structure_instruction():
    content = _read("TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift")
    assert 'case "hr_structure_mode_notice":' in content
    assert 'case "structure_instruction_work":' in content
    assert 'case "structure_instruction_recovery":' in content
    assert 'case "structure_instruction_steady":' in content
    assert 'case "structure_instruction_finish":' in content
    assert '"zone.hr_poor_timing.1"' in content
    assert '"zone.structure.work.1"' in content
    assert '"zone.structure.recovery.1"' in content
    assert '"zone.structure.steady.1"' in content
    assert '"zone.structure.finish.1"' in content


def test_workout_event_mapping_uses_staged_motivation_fallbacks():
    content = _read("TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift")
    assert '"interval.motivate.s2.1"' in content
    assert '"easy_run.motivate.s2.1"' in content


def test_workout_event_router_suppresses_new_cues_while_audio_is_playing():
    content = _read("TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift")
    assert "audioPlayer?.isPlaying == true" in content
    assert 'return (false, "event_router_audio_playing")' in content


def test_audio_pipeline_has_speech_transcript_stage():
    content = _read("TreningsCoach/TreningsCoach/Services/AudioPipelineDiagnostics.swift")
    assert 'case speechTranscript = "SPEECH"' in content
    assert "func logSpeech(" in content


def test_workout_local_pack_is_persona_scoped_and_toxic_guarded():
    content = _read("TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift")
    assert "activeAudioPersonaKey" in content
    assert "isLocalPackAllowed(for:" in content
    assert 'utteranceID.hasPrefix("toxic.")' in content
    assert ".appendingPathComponent(personaKey, isDirectory: true)" in content
