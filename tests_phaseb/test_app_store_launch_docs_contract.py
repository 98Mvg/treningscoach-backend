from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_app_store_submission_checklist_documents_paid_apps_and_reviewer_paths() -> None:
    content = _read_text("docs/checklists/app-store-submission-checklist.md")
    assert "Paid Apps Agreement" in content
    assert "monthly subscription product" in content
    assert "yearly subscription product" in content
    assert "Restore Purchases" in content
    assert "Manage Subscription" in content
    assert "free core workout flow" in content
    assert "TestFlight" in content


def test_app_review_notes_template_matches_free_core_and_optional_premium_truth() -> None:
    content = _read_text("docs/checklists/app-review-notes-template.md")
    assert "free to download" in content
    assert "free core workout experience" in content
    assert "monthly or yearly Apple subscriptions" in content
    assert "No paywall interrupts an active workout" in content
    assert "Delete account" in content


def test_launch_ops_checklist_references_app_store_submission_assets() -> None:
    content = _read_text("docs/checklists/phase1-launch-ops-checklist.md")
    assert "app-store-submission-checklist.md" in content or "app-review-notes-template.md" in content
    assert "Paid Apps Agreement" in content
    assert "Submit the first subscriptions together with the app version." in content
