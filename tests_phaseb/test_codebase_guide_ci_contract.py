from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "codebase-guide-sync.yml"


def test_codebase_guide_ci_workflow_exists():
    assert WORKFLOW_PATH.exists()


def test_codebase_guide_ci_workflow_runs_sync_checks():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "scripts/generate_codebase_guide.py --check" in content
    assert "tests_phaseb/test_codebase_guide_sync.py" in content
    assert "tests_phaseb/test_root_runtime_source_of_truth.py" in content
