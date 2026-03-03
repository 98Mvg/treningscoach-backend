import importlib.util
import sys
import zipfile
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


def test_export_xlsx_writes_workbook_with_formulas_and_filters(tmp_path: Path):
    rows = editor._rows()[:5]
    out = tmp_path / "phrase_catalog.xlsx"

    editor.export_xlsx(out, rows)

    assert out.exists()
    with zipfile.ZipFile(out) as workbook:
        names = set(workbook.namelist())
        assert "[Content_Types].xml" in names
        assert "xl/workbook.xml" in names
        assert "xl/worksheets/sheet1.xml" in names
        assert "xl/worksheets/sheet2.xml" in names
        assert "xl/styles.xml" in names

        sheet1 = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
        assert "en_words" in sheet1
        assert "review_status" in sheet1
        assert "action_needed" in sheet1
        assert '<f>LEN(G2)</f>' in sheet1
        assert 'autoFilter ref="A1:R6"' in sheet1
        assert 'sqref="P2:P6"' in sheet1

        sheet2 = workbook.read("xl/worksheets/sheet2.xml").decode("utf-8")
        assert "Phrase Catalog QA Summary" in sheet2
        assert "COUNTIF(Catalog!M:M" in sheet2


# ── XLSX Import (roundtrip) ──────────────────────────────────────────

def test_read_xlsx_roundtrip_all_rows(tmp_path: Path):
    """Export → read back: every row has an ID and both en/no text."""
    rows = editor._rows()
    xlsx_path = tmp_path / "catalog.xlsx"
    editor.export_xlsx(xlsx_path, rows)

    imported = editor.read_xlsx(xlsx_path)
    assert len(imported) == len(rows)
    for imp in imported:
        assert imp.phrase_id, "Row missing phrase_id"


def test_read_xlsx_text_matches_source(tmp_path: Path):
    """Exported en/no text matches the original catalog rows."""
    rows = editor._rows()[:10]
    xlsx_path = tmp_path / "catalog.xlsx"
    editor.export_xlsx(xlsx_path, rows)

    imported = editor.read_xlsx(xlsx_path)
    by_id = {imp.phrase_id: imp for imp in imported}
    for row in rows:
        imp = by_id.get(row.phrase_id)
        assert imp is not None, f"{row.phrase_id} missing from XLSX"
        assert imp.en == row.en, f"{row.phrase_id} en mismatch"
        assert imp.no == row.no, f"{row.phrase_id} no mismatch"


def test_import_xlsx_no_changes_detected(tmp_path: Path):
    """Import of unmodified XLSX reports zero changes."""
    rows = editor._rows()[:10]
    xlsx_path = tmp_path / "catalog.xlsx"
    editor.export_xlsx(xlsx_path, rows)

    result = editor.import_xlsx(xlsx_path=xlsx_path, apply_changes=False)
    assert result == 0


def test_import_xlsx_detects_text_edit(tmp_path: Path):
    """Modified text in XLSX is detected as a change."""
    import zipfile as zf
    from xml.etree import ElementTree as ET

    rows = editor._rows()[:10]
    xlsx_path = tmp_path / "original.xlsx"
    editor.export_xlsx(xlsx_path, rows)

    # Modify one cell in the XML
    NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    with zf.ZipFile(xlsx_path, "r") as z:
        sheet_xml = z.read("xl/worksheets/sheet1.xml")
        all_files = {n: z.read(n) for n in z.namelist()}

    root = ET.fromstring(sheet_xml)
    target_id = rows[0].phrase_id
    modified = False
    for row_el in root.iter(f"{{{NS}}}row"):
        cells: dict[int, ET.Element] = {}
        for cell_el in row_el.iter(f"{{{NS}}}c"):
            ref = cell_el.get("r", "")
            col = 0
            for ch in ref:
                if ch.isalpha():
                    col = col * 26 + (ord(ch.upper()) - 64)
                else:
                    break
            cells[col] = cell_el
        # col 2 = B = id
        if 2 in cells:
            is_el = cells[2].find(f"{{{NS}}}is")
            if is_el is not None:
                t_el = is_el.find(f"{{{NS}}}t")
                if t_el is not None and t_el.text == target_id:
                    # Edit col 7 = G = en text
                    if 7 in cells:
                        en_is = cells[7].find(f"{{{NS}}}is")
                        if en_is is not None:
                            en_t = en_is.find(f"{{{NS}}}t")
                            if en_t is not None:
                                en_t.text = "EDITED TEXT HERE"
                                modified = True
                                break

    assert modified, f"Could not find {target_id} in XLSX"

    edited_path = tmp_path / "edited.xlsx"
    modified_xml = ET.tostring(root, encoding="unicode")
    with zf.ZipFile(edited_path, "w", zf.ZIP_DEFLATED) as z:
        for name, data in all_files.items():
            if name == "xl/worksheets/sheet1.xml":
                z.writestr(name, modified_xml)
            else:
                z.writestr(name, data)

    # Read back — should find exactly one change
    imported = editor.read_xlsx(edited_path)
    changed = [r for r in imported if r.en == "EDITED TEXT HERE"]
    assert len(changed) == 1
    assert changed[0].phrase_id == target_id


def test_welcome_validation_helper_passes_for_current_catalog():
    assert editor._validate_welcome_or_fail() == 0


def test_welcome_validation_helper_fails_on_errors(monkeypatch):
    monkeypatch.setattr(editor, "validate_welcome_catalog", lambda: ["bad welcome gap"])
    assert editor._validate_welcome_or_fail() == 2
