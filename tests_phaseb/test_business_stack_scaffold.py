import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_web_scaffold_files_exist():
    expected_files = [
        "web/package.json",
        "web/README.md",
        "web/app/page.tsx",
        "web/app/api/health/route.ts",
        "web/app/api/webhooks/clerk/route.ts",
        "web/app/account/page.tsx",
        "web/app/account/history/page.tsx",
        "web/app/account/premium/page.tsx",
        "web/app/account/preferences/page.tsx",
        "web/app/sign-in/[[...sign-in]]/page.tsx",
        "web/app/sign-up/[[...sign-up]]/page.tsx",
        "web/app/support/page.tsx",
        "web/app/legal/privacy/page.tsx",
        "web/app/legal/terms/page.tsx",
        "web/middleware.ts",
        "web/lib/account-data.ts",
        "web/lib/clerk-sync.ts",
        "web/lib/email.ts",
        "web/lib/env.ts",
        "web/lib/posthog.ts",
        "web/lib/supabase.ts",
    ]
    for relative_path in expected_files:
        assert (REPO_ROOT / relative_path).exists(), relative_path


def test_web_package_has_required_business_stack_dependencies():
    package = json.loads((REPO_ROOT / "web/package.json").read_text(encoding="utf-8"))
    dependencies = package["dependencies"]

    for dependency in [
        "@clerk/nextjs",
        "@sentry/nextjs",
        "@supabase/supabase-js",
        "next",
        "posthog-js",
        "posthog-node",
        "resend",
        "svix",
        "zod",
    ]:
        assert dependency in dependencies


def test_supabase_migration_has_required_tables():
    migration = (REPO_ROOT / "supabase/migrations/20260309_000001_business_platform.sql").read_text(encoding="utf-8")

    for table_name in [
        "profiles",
        "workout_sessions",
        "workout_metrics",
        "entitlements",
        "identity_links",
        "email_events",
    ]:
        assert f"create table if not exists {table_name}" in migration


def test_business_platform_docs_exist():
    expected_docs = [
        "docs/business-platform/coachi-business-stack.md",
        "docs/business-platform/coachi-storekit-first.md",
        "docs/business-platform/coachi-migration-checklist.md",
    ]
    for relative_path in expected_docs:
        assert (REPO_ROOT / relative_path).exists(), relative_path


def test_legacy_export_script_covers_all_supabase_import_artifacts():
    script = (REPO_ROOT / "scripts/export_legacy_to_supabase_json.py").read_text(encoding="utf-8")

    for output_name in [
        "profiles.json",
        "workout_sessions.json",
        "workout_metrics.json",
        "email_events.json",
        "entitlements.json",
        "identity_links.json",
    ]:
        assert output_name in script


def test_clerk_webhook_shell_syncs_profiles_and_identity_links():
    route_content = (REPO_ROOT / "web/app/api/webhooks/clerk/route.ts").read_text(encoding="utf-8")
    helper_content = (REPO_ROOT / "web/lib/clerk-sync.ts").read_text(encoding="utf-8")

    assert "user.created" in route_content
    assert "user.updated" in route_content
    assert "user.deleted" in route_content
    assert "upsertClerkUserProfile" in route_content
    assert "clearClerkUserLink" in route_content
    assert "identity_links" in helper_content
    assert "profiles" in helper_content


def test_account_shell_reads_mirrored_supabase_data():
    account_page = (REPO_ROOT / "web/app/account/page.tsx").read_text(encoding="utf-8")
    history_page = (REPO_ROOT / "web/app/account/history/page.tsx").read_text(encoding="utf-8")
    premium_page = (REPO_ROOT / "web/app/account/premium/page.tsx").read_text(encoding="utf-8")
    helper = (REPO_ROOT / "web/lib/account-data.ts").read_text(encoding="utf-8")

    assert "getAccountDataSnapshot" in account_page
    assert "getAccountDataSnapshot" in history_page
    assert "getAccountDataSnapshot" in premium_page
    assert "workout_sessions" in helper
    assert "workout_metrics" in helper
    assert "entitlements" in helper


def test_resend_email_shell_tracks_email_events():
    email_helper = (REPO_ROOT / "web/lib/email.ts").read_text(encoding="utf-8")

    assert "Resend" in email_helper
    assert "email_events" in email_helper
    assert "welcomeEmailHtml" in email_helper
    assert "waitlistConfirmationHtml" in email_helper
