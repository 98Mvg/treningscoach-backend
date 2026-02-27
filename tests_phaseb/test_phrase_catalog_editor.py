import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tools" / "phrase_catalog_editor.py"
SPEC = importlib.util.spec_from_file_location("phrase_catalog_editor", MODULE_PATH)
editor = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = editor
SPEC.loader.exec_module(editor)


def test_remove_words_from_text_removes_and_cleans_spacing():
    patterns = editor._compile_patterns(["hardere", "embarrassing"])
    text_no = "Bra! Trykk hardere, ikke stopp!"
    text_en = "This is embarrassing, keep going!"

    cleaned_no = editor._remove_words_from_text(text_no, patterns)
    cleaned_en = editor._remove_words_from_text(text_en, patterns)

    assert cleaned_no == "Bra! Trykk, ikke stopp!"
    assert cleaned_en == "This is, keep going!"


def test_collect_words_from_csv_and_file_dedupes(tmp_path: Path):
    words_file = tmp_path / "words.txt"
    words_file.write_text("pathetic\n# comment\nembarrassing\nPathetic\n", encoding="utf-8")

    words = editor._collect_words("hardere,pathetic", str(words_file))

    assert words == ["hardere", "pathetic", "embarrassing"]


def test_export_markdown_writes_sections(tmp_path: Path):
    rows = editor._rows()[:3]
    out = tmp_path / "phrases.md"
    editor.export_markdown(out, rows)

    content = out.read_text(encoding="utf-8")
    assert "# Phrase Catalog Review" in content
    assert "Total phrases: **3**" in content
    assert "## " in content
