import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_env_runbook_exists_and_references_coachi_no():
    content = (REPO_ROOT / "docs/business-platform/coachi-env-runbook.md").read_text(encoding="utf-8")
    assert "Coachi.no" in content
    assert "NEXT_PUBLIC_" in content
    assert "server-only" in content


def test_web_email_shell_is_limited_to_initial_three_flows():
    content = (REPO_ROOT / "web/lib/email.ts").read_text(encoding="utf-8")
    assert "'welcome'" in content
    assert "'waitlist_confirmation'" in content
    assert "'account_created_confirmation'" in content
    assert "workout_summary" not in content
    assert "weekly_summary" not in content
    assert "upgrade_confirmation" not in content


def test_posthog_event_list_matches_current_business_scope():
    content = (REPO_ROOT / "web/lib/posthog.ts").read_text(encoding="utf-8")
    expected_events = [
        "signup_completed",
        "app_opened",
        "workout_started",
        "workout_completed",
        "coach_score_viewed",
        "talk_to_coach_used",
        "upgrade_viewed",
        "subscription_started",
        "trial_started",
        "subscription_active",
    ]
    for event in expected_events:
        assert f"'{event}'" in content


def test_client_side_files_do_not_reference_server_only_secrets():
    client_files = [
        "web/app/page.tsx",
        "web/app/support/page.tsx",
        "web/app/legal/privacy/page.tsx",
        "web/app/legal/terms/page.tsx",
        "web/app/sign-in/[[...sign-in]]/page.tsx",
        "web/app/sign-up/[[...sign-up]]/page.tsx",
        "web/components/providers.tsx",
        "web/lib/posthog.ts",
        "web/instrumentation-client.ts",
        "web/sentry.client.config.ts",
    ]
    forbidden = [
        "CLERK_SECRET_KEY",
        "CLERK_WEBHOOK_SECRET",
        "SUPABASE_SERVICE_ROLE_KEY",
        "RESEND_API_KEY",
        "SENTRY_AUTH_TOKEN",
    ]
    for relative_path in client_files:
        content = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for secret_name in forbidden:
            assert secret_name not in content, f"{secret_name} leaked into {relative_path}"


def test_clerk_shell_is_coherent():
    sign_in = (REPO_ROOT / "web/app/sign-in/[[...sign-in]]/page.tsx").read_text(encoding="utf-8")
    sign_up = (REPO_ROOT / "web/app/sign-up/[[...sign-up]]/page.tsx").read_text(encoding="utf-8")
    middleware = (REPO_ROOT / "web/middleware.ts").read_text(encoding="utf-8")
    webhook = (REPO_ROOT / "web/app/api/webhooks/clerk/route.ts").read_text(encoding="utf-8")

    assert "SignIn" in sign_in
    assert "SignUp" in sign_up
    assert "/account(.*)" in middleware
    assert "user.created" in webhook
    assert "user.updated" in webhook
    assert "user.deleted" in webhook


def test_offline_verifier_references_required_business_artifacts():
    content = (REPO_ROOT / "scripts/verify_supabase_business_platform.py").read_text(encoding="utf-8")
    for token in [
        "profiles",
        "workout_sessions",
        "workout_metrics",
        "entitlements",
        "identity_links",
        "email_events",
        "profiles.json",
        "workout_sessions.json",
        "workout_metrics.json",
        "entitlements.json",
        "identity_links.json",
        "email_events.json",
    ]:
        assert token in content


def test_exported_supabase_artifacts_are_json_arrays_after_export():
    export_dir = REPO_ROOT / "output/supabase_export"
    expected_files = [
        "profiles.json",
        "workout_sessions.json",
        "workout_metrics.json",
        "entitlements.json",
        "identity_links.json",
        "email_events.json",
    ]
    for filename in expected_files:
        path = export_dir / filename
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, list), filename
