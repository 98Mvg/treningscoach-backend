from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
SECURITY_CHECKLIST = REPO_ROOT / "docs" / "checklists" / "phase1-security-review.md"
OPS_CHECKLIST = REPO_ROOT / "docs" / "checklists" / "phase1-launch-ops-checklist.md"


def test_phase1_security_review_exists_and_has_30_rules() -> None:
    text = SECURITY_CHECKLIST.read_text(encoding="utf-8")
    numbered = re.findall(r"^\d+\.\s", text, flags=re.MULTILINE)
    assert len(numbered) == 30
    assert "Do not let AI decide workout events" in text
    assert "Never interrupt workouts with paywalls" in text
    assert "Fail fast on STT quota or rate-limit errors" in text


def test_launch_ops_checklist_references_security_review() -> None:
    text = OPS_CHECKLIST.read_text(encoding="utf-8")
    assert "phase1-security-review.md" in text
