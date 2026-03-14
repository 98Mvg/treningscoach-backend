import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import database


def test_brain_priority_env_override(monkeypatch):
    monkeypatch.setenv("BRAIN_PRIORITY", "grok,openai,gemini,claude")
    monkeypatch.setenv("ACTIVE_BRAIN", "grok")
    monkeypatch.setenv("USE_PRIORITY_ROUTING", "true")

    importlib.reload(config)

    assert config.BRAIN_PRIORITY == ["grok", "openai", "gemini", "claude"]
    assert config.ACTIVE_BRAIN == "grok"
    assert config.USE_PRIORITY_ROUTING is True


def test_timeout_and_threshold_json_overrides(monkeypatch):
    monkeypatch.setenv("BRAIN_TIMEOUTS_JSON", '{"grok": 5.5, "openai": 2.2}')
    monkeypatch.setenv("BRAIN_SLOW_THRESHOLDS_JSON", '{"grok": 7.0}')
    monkeypatch.setenv("BRAIN_MODE_TIMEOUTS_JSON", '{"realtime_coach": {"grok": 4.6}}')

    importlib.reload(config)

    assert config.BRAIN_TIMEOUTS["grok"] == 5.5
    assert config.BRAIN_TIMEOUTS["openai"] == 2.2
    assert config.BRAIN_SLOW_THRESHOLDS["grok"] == 7.0
    assert config.BRAIN_MODE_TIMEOUTS["realtime_coach"]["grok"] == 4.6


def test_latency_strategy_env_overrides(monkeypatch):
    monkeypatch.setenv("LATENCY_FAST_FALLBACK_ENABLED", "false")
    monkeypatch.setenv("LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS", "3.4")
    monkeypatch.setenv("LATENCY_FAST_FALLBACK_MIN_CALLS", "5")
    monkeypatch.setenv("LATENCY_FAST_FALLBACK_COOLDOWN_SECONDS", "18")

    importlib.reload(config)

    assert config.LATENCY_FAST_FALLBACK_ENABLED is False
    assert config.LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS == 3.4
    assert config.LATENCY_FAST_FALLBACK_MIN_CALLS == 5
    assert config.LATENCY_FAST_FALLBACK_COOLDOWN_SECONDS == 18.0


def test_zone_layer_env_overrides(monkeypatch):
    monkeypatch.setenv("ZONE_EVENT_LLM_REWRITE_ENABLED", "true")
    monkeypatch.setenv("ZONE_EVENT_LLM_REWRITE_TIMEOUT_SECONDS", "1.1")
    monkeypatch.setenv("ZONE_EVENT_LLM_REWRITE_MAX_WORDS", "12")
    monkeypatch.setenv("ZONE_PERSONALIZATION_ENABLED", "false")
    monkeypatch.setenv("ZONE_PERSONALIZATION_MAX_RECOVERY_SAMPLES", "18")

    importlib.reload(config)

    assert config.ZONE_EVENT_LLM_REWRITE_ENABLED is True
    assert config.ZONE_EVENT_LLM_REWRITE_TIMEOUT_SECONDS == 1.1
    assert config.ZONE_EVENT_LLM_REWRITE_MAX_WORDS == 12
    assert config.ZONE_PERSONALIZATION_ENABLED is False
    assert config.ZONE_PERSONALIZATION_MAX_RECOVERY_SAMPLES == 18


def test_launch_lock_env_overrides(monkeypatch):
    monkeypatch.setenv("DEFAULT_LANGUAGE", "no")
    monkeypatch.setenv("MIN_SIGNAL_QUALITY_TO_FORCE", "0.2")
    monkeypatch.setenv("COACHING_VALIDATION_ENFORCE", "true")
    monkeypatch.setenv("BREATHING_TIMELINE_ENFORCE", "false")
    monkeypatch.setenv("USE_HYBRID_BRAIN", "false")

    importlib.reload(config)

    assert config.DEFAULT_LANGUAGE == "no"
    assert config.MIN_SIGNAL_QUALITY_TO_FORCE == 0.2
    assert config.COACHING_VALIDATION_ENFORCE is True
    assert config.BREATHING_TIMELINE_ENFORCE is False
    assert config.USE_HYBRID_BRAIN is False


def test_monetization_free_mode_lock(monkeypatch):
    monkeypatch.setenv("APP_FREE_MODE", "true")
    monkeypatch.setenv("BILLING_ENABLED", "true")
    monkeypatch.setenv("PREMIUM_SURFACES_ENABLED", "true")

    importlib.reload(config)

    assert config.APP_FREE_MODE is True
    # Free mode must hard-lock paid surfaces off, regardless of env intent.
    assert config.BILLING_ENABLED is False
    assert config.PREMIUM_SURFACES_ENABLED is False


def test_monetization_can_be_enabled_later(monkeypatch):
    monkeypatch.setenv("APP_FREE_MODE", "false")
    monkeypatch.setenv("BILLING_ENABLED", "true")
    monkeypatch.setenv("PREMIUM_SURFACES_ENABLED", "true")

    importlib.reload(config)

    assert config.APP_FREE_MODE is False
    assert config.BILLING_ENABLED is True
    assert config.PREMIUM_SURFACES_ENABLED is True


def test_coach_score_version_env_override(monkeypatch):
    monkeypatch.setenv("COACH_SCORE_VERSION", "shadow")
    monkeypatch.setenv("SPEECH_DECISION_OWNER_V2", "false")
    importlib.reload(config)
    assert config.COACH_SCORE_VERSION == "shadow"
    assert config.SPEECH_DECISION_OWNER_V2 is False

    monkeypatch.setenv("COACH_SCORE_VERSION", "invalid")
    importlib.reload(config)
    assert config.COACH_SCORE_VERSION == "cs_v2"


def test_talk_safety_flags_env_override(monkeypatch):
    monkeypatch.setenv("TALK_STT_ENABLED", "true")
    monkeypatch.setenv("COACH_TALK_STRICT_SAFETY_ENABLED", "false")
    monkeypatch.setenv("COACH_TALK_POLICY_ROTATE_ENABLED", "false")
    monkeypatch.setenv("TALK_STT_QUOTA_COOLDOWN_SECONDS", "120")

    importlib.reload(config)

    assert config.TALK_STT_ENABLED is True
    assert config.COACH_TALK_STRICT_SAFETY_ENABLED is False
    assert config.COACH_TALK_POLICY_ROTATE_ENABLED is False
    assert config.TALK_STT_QUOTA_COOLDOWN_SECONDS == 120.0
    assert isinstance(config.COACH_TALK_POLICY_REFUSAL_BANK.get("en"), list)
    assert isinstance(config.COACH_TALK_POLICY_REFUSAL_BANK.get("no"), list)


def test_xai_voice_agent_env_override(monkeypatch):
    monkeypatch.setenv("XAI_VOICE_AGENT_ENABLED", "true")
    monkeypatch.setenv("XAI_VOICE_AGENT_MODEL", "grok-voice-latest")
    monkeypatch.setenv("XAI_VOICE_AGENT_REGION", "us-east-1")
    monkeypatch.setenv("XAI_VOICE_AGENT_VOICE", "Rex")
    monkeypatch.setenv("XAI_VOICE_AGENT_MAX_SESSION_SECONDS", "420")
    monkeypatch.setenv("XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS", "90")
    monkeypatch.setenv("XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS", "480")
    monkeypatch.setenv("XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY", "3")
    monkeypatch.setenv("XAI_VOICE_AGENT_PREMIUM_SESSIONS_PER_DAY", "12")
    monkeypatch.setenv("XAI_VOICE_AGENT_CLIENT_SECRET_URL", "https://api.x.ai/v1/realtime/client_secrets")
    monkeypatch.setenv("XAI_VOICE_AGENT_WEBSOCKET_URL", "wss://api.x.ai/v1/realtime")
    monkeypatch.setenv("XAI_VOICE_AGENT_HISTORY_RECENT_WORKOUT_LIMIT", "18")

    importlib.reload(config)

    assert config.XAI_VOICE_AGENT_ENABLED is True
    assert config.XAI_VOICE_AGENT_MODEL == "grok-voice-latest"
    assert config.XAI_VOICE_AGENT_REGION == "us-east-1"
    assert config.XAI_VOICE_AGENT_VOICE == "Rex"
    assert config.XAI_VOICE_AGENT_MAX_SESSION_SECONDS == 420
    assert config.XAI_VOICE_AGENT_FREE_MAX_SESSION_SECONDS == 90
    assert config.XAI_VOICE_AGENT_PREMIUM_MAX_SESSION_SECONDS == 480
    assert config.XAI_VOICE_AGENT_FREE_SESSIONS_PER_DAY == 3
    assert config.XAI_VOICE_AGENT_PREMIUM_SESSIONS_PER_DAY == 12
    assert config.XAI_VOICE_AGENT_CLIENT_SECRET_URL == "https://api.x.ai/v1/realtime/client_secrets"
    assert config.XAI_VOICE_AGENT_WEBSOCKET_URL == "wss://api.x.ai/v1/realtime"
    assert config.XAI_VOICE_AGENT_HISTORY_RECENT_WORKOUT_LIMIT == 18


def test_premium_override_envs_are_resolved(monkeypatch):
    monkeypatch.setenv("PREMIUM_TIER_OVERRIDE_USER_IDS", "user_a,user_b")
    monkeypatch.setenv("PREMIUM_TIER_OVERRIDE_EMAILS", "premium@example.com, second@example.com ")

    importlib.reload(config)

    assert config.PREMIUM_TIER_OVERRIDE_USER_IDS == ["user_a", "user_b"]
    assert config.PREMIUM_TIER_OVERRIDE_EMAILS == ["premium@example.com", "second@example.com"]
    assert config.user_has_premium_override(user_id="user_b") is True
    assert config.user_has_premium_override(email="premium@example.com") is True
    assert config.user_has_premium_override(email="PREMIUM@EXAMPLE.COM") is True
    assert config.user_has_premium_override(user_id="missing", email="missing@example.com") is False


def test_app_store_webhook_env_overrides(monkeypatch):
    monkeypatch.setenv("APP_STORE_BUNDLE_IDS", "com.coachi.app,com.coachi.app.beta")
    monkeypatch.setenv("APP_STORE_TRUSTED_ROOT_SHA256S", "root_a,root_b")
    monkeypatch.setenv("APP_STORE_SERVER_NOTIFICATIONS_ENABLED", "true")
    monkeypatch.setenv("APP_STORE_SERVER_NOTIFICATIONS_VERIFY_SIGNATURE", "false")

    importlib.reload(config)

    assert config.APP_STORE_BUNDLE_IDS == ["com.coachi.app", "com.coachi.app.beta"]
    assert config.APP_STORE_TRUSTED_ROOT_SHA256S == ["root_a", "root_b"]
    assert config.APP_STORE_SERVER_NOTIFICATIONS_ENABLED is True
    assert config.APP_STORE_SERVER_NOTIFICATIONS_VERIFY_SIGNATURE is False


def test_security_env_overrides(monkeypatch):
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MAX_DAYS", "5")
    monkeypatch.setenv("JWT_REFRESH_TOKEN_MAX_DAYS", "20")
    monkeypatch.setenv("JWT_SECRET_MAX_AGE_DAYS", "30")
    monkeypatch.setenv("APPLE_AUTH_ENABLED", "true")
    monkeypatch.setenv("EMAIL_AUTH_ENABLED", "true")
    monkeypatch.setenv("EMAIL_AUTH_CODE_TTL_MINUTES", "15")
    monkeypatch.setenv("GOOGLE_AUTH_ENABLED", "true")
    monkeypatch.setenv("FACEBOOK_AUTH_ENABLED", "true")
    monkeypatch.setenv("VIPPS_AUTH_ENABLED", "true")
    monkeypatch.setenv("MOBILE_API_AUTH_REQUIRED", "true")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_STORAGE_BACKEND", "database")
    monkeypatch.setenv("RATE_LIMIT_RETENTION_SECONDS", "172800")
    monkeypatch.setenv("API_RATE_LIMIT_PER_HOUR", "150")
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_HOUR", "20")
    monkeypatch.setenv("CONTINUOUS_RATE_LIMIT_PER_HOUR", "900")
    monkeypatch.setenv("AUTH_LOGIN_RATE_LIMIT_PER_MINUTE", "7")
    monkeypatch.setenv("AUTH_REFRESH_RATE_LIMIT_PER_MINUTE", "22")
    monkeypatch.setenv("PROFILE_UPSERT_RATE_LIMIT_PER_MINUTE", "12")
    monkeypatch.setenv("COACH_TALK_FREE_RATE_LIMIT_PER_DAY", "8")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://coachi.app,https://www.coachi.app")
    monkeypatch.setenv("AUDIO_SIGNATURE_BYPASS_FOR_TESTS", "false")

    importlib.reload(config)

    assert config.JWT_ACCESS_TOKEN_MAX_DAYS == 5
    assert config.JWT_REFRESH_TOKEN_MAX_DAYS == 20
    assert config.JWT_SECRET_MAX_AGE_DAYS == 30
    assert config.APPLE_AUTH_ENABLED is True
    assert config.EMAIL_AUTH_ENABLED is True
    assert config.EMAIL_AUTH_CODE_TTL_MINUTES == 15
    assert config.GOOGLE_AUTH_ENABLED is True
    assert config.FACEBOOK_AUTH_ENABLED is True
    assert config.VIPPS_AUTH_ENABLED is True
    assert config.MOBILE_API_AUTH_REQUIRED is True
    assert config.RATE_LIMIT_ENABLED is True
    assert config.RATE_LIMIT_STORAGE_BACKEND == "database"
    assert config.RATE_LIMIT_RETENTION_SECONDS == 172800
    assert config.API_RATE_LIMIT_PER_HOUR == 150
    assert config.AUTH_RATE_LIMIT_PER_HOUR == 20
    assert config.CONTINUOUS_RATE_LIMIT_PER_HOUR == 900
    assert config.AUTH_LOGIN_RATE_LIMIT_PER_MINUTE == 7
    assert config.AUTH_REFRESH_RATE_LIMIT_PER_MINUTE == 22
    assert config.PROFILE_UPSERT_RATE_LIMIT_PER_MINUTE == 12
    assert config.COACH_TALK_FREE_RATE_LIMIT_PER_DAY == 8
    assert config.CORS_ALLOWED_ORIGINS == ["https://coachi.app", "https://www.coachi.app"]
    assert config.AUDIO_SIGNATURE_BYPASS_FOR_TESTS is False


def test_security_refresh_ttl_defaults_to_7_days(monkeypatch):
    monkeypatch.delenv("JWT_ACCESS_TOKEN_MAX_DAYS", raising=False)
    monkeypatch.delenv("JWT_REFRESH_TOKEN_MAX_DAYS", raising=False)

    importlib.reload(config)

    assert config.JWT_ACCESS_TOKEN_MAX_DAYS == 7
    assert config.JWT_REFRESH_TOKEN_MAX_DAYS == 7


def test_mobile_api_auth_defaults_to_guest_friendly(monkeypatch):
    monkeypatch.delenv("MOBILE_API_AUTH_REQUIRED", raising=False)

    importlib.reload(config)

    assert config.MOBILE_API_AUTH_REQUIRED is False


def test_non_apple_auth_providers_default_to_disabled(monkeypatch):
    monkeypatch.delenv("APPLE_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("EMAIL_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("GOOGLE_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_IDS", raising=False)
    monkeypatch.delenv("FACEBOOK_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("VIPPS_AUTH_ENABLED", raising=False)

    importlib.reload(config)

    assert config.APPLE_AUTH_ENABLED is True
    assert config.EMAIL_AUTH_ENABLED is True
    assert config.GOOGLE_AUTH_ENABLED is True
    assert config.GOOGLE_AUTH_CONFIGURED is False
    assert config.GOOGLE_CLIENT_IDS == []
    assert config.FACEBOOK_AUTH_ENABLED is False
    assert config.VIPPS_AUTH_ENABLED is False


def test_google_client_ids_env_override(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_IDS", "ios-client-id,web-client-id")

    importlib.reload(config)

    assert config.GOOGLE_CLIENT_IDS == ["ios-client-id", "web-client-id"]
    assert config.GOOGLE_AUTH_CONFIGURED is True


def test_storage_paths_default_to_absolute_runtime_dirs(monkeypatch):
    for key in (
        "INSTANCE_DIR",
        "UPLOAD_DIR",
        "OUTPUT_DIR",
        "TTS_AUDIO_CACHE_DIR",
        "WELCOME_ROTATION_STATE_PATH",
        "ZONE_PERSONALIZATION_STORAGE_PATH",
    ):
        monkeypatch.delenv(key, raising=False)

    importlib.reload(config)

    assert Path(config.INSTANCE_DIR).is_absolute()
    assert Path(config.UPLOAD_DIR).is_absolute()
    assert Path(config.OUTPUT_DIR).is_absolute()
    assert Path(config.TTS_AUDIO_CACHE_DIR).is_absolute()
    assert Path(config.WELCOME_ROTATION_STATE_PATH).is_absolute()
    assert Path(config.ZONE_PERSONALIZATION_STORAGE_PATH).is_absolute()
    assert config.INSTANCE_DIR.endswith("/instance")
    assert config.UPLOAD_DIR.endswith("/uploads")
    assert config.OUTPUT_DIR.endswith("/output")
    assert config.TTS_AUDIO_CACHE_DIR.endswith("/output/cache")
    assert config.WELCOME_ROTATION_STATE_PATH.endswith("/instance/cache/utterance_rotation_state.json")
    assert config.ZONE_PERSONALIZATION_STORAGE_PATH.endswith("/instance/zone_personalization.json")


def test_storage_paths_allow_env_overrides(monkeypatch):
    monkeypatch.setenv("INSTANCE_DIR", "tmp/runtime-instance")
    monkeypatch.setenv("UPLOAD_DIR", "tmp/runtime-uploads")
    monkeypatch.setenv("OUTPUT_DIR", "tmp/runtime-output")
    monkeypatch.setenv("TTS_AUDIO_CACHE_DIR", "tmp/runtime-output/cache")
    monkeypatch.setenv("WELCOME_ROTATION_STATE_PATH", "tmp/runtime-instance/rotation.json")
    monkeypatch.setenv("ZONE_PERSONALIZATION_STORAGE_PATH", "tmp/runtime-instance/personalization.json")

    importlib.reload(config)

    assert config.INSTANCE_DIR.endswith("/tmp/runtime-instance")
    assert config.UPLOAD_DIR.endswith("/tmp/runtime-uploads")
    assert config.OUTPUT_DIR.endswith("/tmp/runtime-output")
    assert config.TTS_AUDIO_CACHE_DIR.endswith("/tmp/runtime-output/cache")
    assert config.WELCOME_ROTATION_STATE_PATH.endswith("/tmp/runtime-instance/rotation.json")
    assert config.ZONE_PERSONALIZATION_STORAGE_PATH.endswith("/tmp/runtime-instance/personalization.json")


def test_database_default_url_uses_instance_dir(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("INSTANCE_DIR", "tmp/test-instance-db")

    importlib.reload(config)

    database_url = database.get_database_url()
    assert database_url.startswith("sqlite:////")
    assert database_url.endswith("/tmp/test-instance-db/treningscoach.db")
