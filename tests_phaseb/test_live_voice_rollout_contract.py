from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_live_voice_smoke_script_checks_auth_and_voice_session_contract():
    content = _read_text("scripts/smoke_live_voice.sh")
    assert 'FREE_USER_BEARER_TOKEN="${FREE_USER_BEARER_TOKEN:-}"' in content
    assert 'PREMIUM_USER_BEARER_TOKEN="${PREMIUM_USER_BEARER_TOKEN:-}"' in content
    assert 'auth_me_json() {' in content
    assert 'voice_session_json() {' in content
    assert '${BASE_URL}/auth/me' in content
    assert '${BASE_URL}/voice/session' in content
    assert 'CHECK_DAILY_LIMITS="${CHECK_DAILY_LIMITS:-false}"' in content
    assert 'assert payload.get("voice") == "Rex"' in content


def test_live_voice_ops_checklist_documents_required_env_and_script():
    content = _read_text("docs/checklists/phase1-launch-ops-checklist.md")
    assert "## Live Voice Rollout Checklist" in content
    assert "XAI_API_KEY" in content
    assert "XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS=120" in content
    assert "XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS=300" in content
    assert "XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY=3" in content
    assert "./scripts/smoke_live_voice.sh" in content


def test_env_example_matches_free_live_voice_session_policy():
    content = _read_text(".env.example")
    assert "XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS=120" in content
    assert "XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS=300" in content
    assert "XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY=3" in content
