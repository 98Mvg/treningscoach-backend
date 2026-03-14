from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_app_store_submission_checklist_documents_paid_apps_and_reviewer_paths() -> None:
    content = _read_text("docs/checklists/app-store-submission-checklist.md")
    assert "Paid Apps Agreement" in content
    assert "app-store-connect-fill-in-template.md" in content
    assert "subscription-sandbox-test-matrix.md" in content
    assert "app.coachi.premium.monthly" in content
    assert "app.coachi.premium.yearly" in content
    assert "monthly subscription product" in content
    assert "yearly subscription product" in content
    assert "Restore Purchases" in content
    assert "Manage Subscription" in content
    assert "free core workout flow" in content
    assert "TestFlight" in content


def test_app_review_notes_template_matches_free_core_and_optional_premium_truth() -> None:
    content = _read_text("docs/checklists/app-review-notes-template.md")
    assert "[APP_VERSION]" in content
    assert "[BUILD_NUMBER]" in content
    assert "[PREMIUM_GROUP_NAME]" in content
    assert "free to download" in content
    assert "free core workout experience" in content
    assert "monthly or yearly Apple subscriptions" in content
    assert "No paywall interrupts an active workout" in content
    assert "Delete account" in content


def test_launch_ops_checklist_references_app_store_submission_assets() -> None:
    content = _read_text("docs/checklists/phase1-launch-ops-checklist.md")
    assert "app-store-submission-checklist.md" in content or "app-review-notes-template.md" in content
    assert "app-store-connect-fill-in-template.md" in content
    assert "subscription-sandbox-test-matrix.md" in content
    assert "Paid Apps Agreement" in content
    assert "Submit the first subscriptions together with the app version." in content


def test_app_store_connect_fill_in_template_matches_repo_truth() -> None:
    content = _read_text("docs/checklists/app-store-connect-fill-in-template.md")
    assert "com.coachi.app" in content
    assert "app.coachi.premium.monthly" in content
    assert "app.coachi.premium.yearly" in content
    assert "[FILL IN]" in content
    assert "free core workout flow" in content


def test_subscription_sandbox_matrix_covers_launch_critical_flows() -> None:
    content = _read_text("docs/checklists/subscription-sandbox-test-matrix.md")
    assert "Monthly Purchase" in content
    assert "Yearly Purchase" in content
    assert "Restore Purchases" in content
    assert "Manage Subscription" in content
    assert "Delete Account" in content
    assert "TestFlight" in content
