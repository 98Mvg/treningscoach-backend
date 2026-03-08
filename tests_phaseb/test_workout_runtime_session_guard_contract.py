from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"


def test_workout_view_model_tracks_tick_count_separately_from_diagnostics() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private var coachingTickCount: Int = 0" in text
    assert 'print("🔄 Coaching tick #\\(tickNumber)' in text
    assert "AudioPipelineDiagnostics.shared.breathAnalysisCount + 1" not in text


def test_workout_view_model_guards_stale_backend_responses_by_session_generation() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private var continuousSessionGeneration: UUID?" in text
    assert "private func isCurrentCoachingSession(sessionID: String, generation: UUID?) -> Bool" in text
    assert 'print("⚠️ STALE_COACHING_RESPONSE_DROPPED session=' in text
    assert "guard self.isCurrentCoachingSession(sessionID: tickSessionID, generation: tickSessionGeneration) else {" in text


def test_workout_view_model_ignores_same_session_responses_that_arrive_too_late() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "private func isStaleCoachingResponse(" in text
    assert 'print("⚠️ STALE_COACHING_RESPONSE_IGNORED session=' in text


def test_workout_view_model_prefers_synced_or_remote_pack_before_bundle_fallback() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    remote_index = text.index("if allowRemotePackFetch {")
    bundled_index = text.index("if let bundledURL = bundledPackFileURL")
    assert remote_index < bundled_index


def test_workout_session_state_resets_when_continuous_workout_stops() -> None:
    text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "coachingTickCount = 0" in text
    assert "continuousSessionGeneration = nil" in text
    assert "sessionStartTime = nil" in text
    assert "currentPhase = configuredWarmupDuration > 0 ? .warmup : .intense" in text
