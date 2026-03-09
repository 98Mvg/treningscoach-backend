from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_root_env_example_includes_business_stack_variables():
    content = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    for env_key in [
        "EMAIL_PROVIDER=",
        "RESEND_API_KEY=",
        "NEXT_PUBLIC_SITE_URL=",
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=",
        "CLERK_SECRET_KEY=",
        "CLERK_WEBHOOK_SECRET=",
        "SUPABASE_URL=",
        "SUPABASE_ANON_KEY=",
        "SUPABASE_SERVICE_ROLE_KEY=",
        "NEXT_PUBLIC_POSTHOG_KEY=",
        "NEXT_PUBLIC_POSTHOG_HOST=",
        "NEXT_PUBLIC_SENTRY_DSN=",
        "SENTRY_AUTH_TOKEN=",
        "EMAIL_FROM=",
        "EMAIL_REPLY_TO=",
    ]:
        assert env_key in content


def test_web_env_example_matches_business_stack_direction():
    content = (REPO_ROOT / "web/.env.example").read_text(encoding="utf-8")

    for env_key in [
        "NEXT_PUBLIC_SITE_URL=",
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=",
        "CLERK_SECRET_KEY=",
        "SUPABASE_URL=",
        "SUPABASE_ANON_KEY=",
        "SUPABASE_SERVICE_ROLE_KEY=",
        "NEXT_PUBLIC_POSTHOG_KEY=",
        "NEXT_PUBLIC_POSTHOG_HOST=",
        "NEXT_PUBLIC_SENTRY_DSN=",
        "RESEND_API_KEY=",
        "EMAIL_FROM=",
        "EMAIL_REPLY_TO=",
    ]:
        assert env_key in content


def test_web_env_example_does_not_embed_live_secrets():
    content = (REPO_ROOT / "web/.env.example").read_text(encoding="utf-8")

    banned_markers = [
        "vcp_",
        "sk_test_",
        "sbp_",
    ]
    for marker in banned_markers:
        assert marker not in content
