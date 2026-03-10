from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_backend_main_is_compatibility_shim():
    content = _read_text("backend/main.py")
    assert "from main import app" in content
    assert "Compatibility backend entrypoint" in content


def test_backend_start_backend_uses_root_runtime():
    content = _read_text("backend/start_backend.sh")
    assert 'python3 "$ROOT_DIR/main.py"' in content


def test_release_check_runs_source_of_truth_guard():
    content = _read_text("scripts/release_check.sh")
    assert "./scripts/check_root_runtime.sh" in content
    assert "generate_codebase_guide.py --check" in content


def test_release_check_uses_curl_timeouts_for_prod_probes():
    content = _read_text("scripts/release_check.sh")
    assert 'CURL_CONNECT_TIMEOUT="${CURL_CONNECT_TIMEOUT:-10}"' in content
    assert 'CURL_MAX_TIME="${CURL_MAX_TIME:-20}"' in content
    assert 'curl_checked() {' in content
    assert '--connect-timeout "${CURL_CONNECT_TIMEOUT}" --max-time "${CURL_MAX_TIME}"' in content


def test_backend_runtime_modules_are_wrappers():
    files = [
        "auth.py",
        "auth_routes.py",
        "brain_router.py",
        "breath_analyzer.py",
        "breathing_timeline.py",
        "coaching_pipeline.py",
        "chat_routes.py",
        "coaching_engine.py",
        "coaching_intelligence.py",
        "config.py",
        "database.py",
        "elevenlabs_tts.py",
        "locale_config.py",
        "norwegian_phrase_quality.py",
        "persona_manager.py",
        "running_personalization.py",
        "session_manager.py",
        "strategic_brain.py",
        "user_memory.py",
        "voice_intelligence.py",
        "web_routes.py",
        "zone_event_motor.py",
    ]
    for file in files:
        content = _read_text(f"backend/{file}")
        assert "Compatibility wrapper for root" in content
        assert "from __future__ import annotations" in content


def test_backend_brain_modules_are_wrappers():
    files = [
        "base_brain.py",
        "claude_brain.py",
        "gemini_brain.py",
        "grok_brain.py",
        "openai_brain.py",
    ]
    for file in files:
        content = _read_text(f"backend/brains/{file}")
        assert "Compatibility wrapper for root `brains/" in content
        assert "from __future__ import annotations" in content
