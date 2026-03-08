from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE_PATH = REPO_ROOT / "CODEBASE_GUIDE.md"
GENERATOR_PATH = REPO_ROOT / "scripts" / "generate_codebase_guide.py"


def _load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_codebase_guide", GENERATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_codebase_guide_is_generated_artifact():
    content = GUIDE_PATH.read_text(encoding="utf-8")
    assert "Generated file. Do not edit by hand." in content
    assert "scripts/generate_codebase_guide.py" in content
    assert "test_codebase_guide_sync.py" in content


def test_codebase_guide_matches_generator_output():
    module = _load_generator_module()
    expected = module.build_guide()
    actual = GUIDE_PATH.read_text(encoding="utf-8")
    assert actual == expected
