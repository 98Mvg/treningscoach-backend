import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

REVIEW_SPEC = importlib.util.spec_from_file_location("phrase_review_v2", REPO_ROOT / "phrase_review_v2.py")
review = importlib.util.module_from_spec(REVIEW_SPEC)
assert REVIEW_SPEC and REVIEW_SPEC.loader
sys.modules[REVIEW_SPEC.name] = review
REVIEW_SPEC.loader.exec_module(review)

EDITOR_SPEC = importlib.util.spec_from_file_location("phrase_catalog_editor", REPO_ROOT / "tools" / "phrase_catalog_editor.py")
editor = importlib.util.module_from_spec(EDITOR_SPEC)
assert EDITOR_SPEC and EDITOR_SPEC.loader
sys.modules[EDITOR_SPEC.name] = editor
EDITOR_SPEC.loader.exec_module(editor)


def test_build_review_rows_summary_shape():
    rows = review.build_review_rows()
    summary = review.summarize_review_rows(rows)

    assert summary["total_rows"] == 120
    assert summary["active_rows"] == 57
    assert summary["compatibility_rows"] == 28
    assert summary["future_rows"] == 32
    assert summary["record_now_rows"] >= 10



def test_build_review_rows_group_order():
    rows = review.build_review_rows()
    groups = []
    for row in rows:
        if not groups or groups[-1] != row.group:
            groups.append(row.group)

    assert groups == [
        "instruction",
        "context",
        "progress",
        "motivation",
        "diagnostic secondary",
        "compatibility only",
        "future additions",
    ]



def test_validate_review_rows_passes_for_default_rows():
    rows = review.build_review_rows()
    assert review.validate_review_rows(rows) == []


def test_build_curation_rows_instruction_filters_current_active_only():
    rows = review.build_curation_rows("instruction")

    assert len(rows) == 18
    assert {row.active_status for row in rows} == {"active"}
    assert {row.group for row in rows} == {"instruction"}
    assert "zone.above.default.1" in {row.phrase_id for row in rows}
    assert "zone.above.default.2" in {row.phrase_id for row in rows}
    assert "zone.in_zone.default.3" in {row.phrase_id for row in rows}
    assert "zone.above.default.3" not in {row.phrase_id for row in rows}
    assert "zone.above.minimal.1" not in {row.phrase_id for row in rows}


def test_build_curation_rows_context_progress_excludes_future_and_compatibility():
    rows = review.build_curation_rows("context_progress")

    assert len(rows) == 19
    assert {row.active_status for row in rows} == {"active"}
    assert {row.group for row in rows} <= {"context", "progress", "motivation"}
    assert "zone.phase.warmup.1" in {row.phrase_id for row in rows}
    assert "zone.main_started.2" in {row.phrase_id for row in rows}
    assert "zone.countdown.halfway.dynamic" in {row.phrase_id for row in rows}
    assert "zone.countdown.session_halfway.dynamic" in {row.phrase_id for row in rows}
    assert "zone.phase.warmup.2" not in {row.phrase_id for row in rows}
    assert "zone.watch_disconnected.1" not in {row.phrase_id for row in rows}


def test_build_runtime_pack_rows_include_active_and_secondary_only():
    rows = review.build_runtime_pack_rows()

    assert {row.active_status for row in rows} == {"active", "active_secondary"}
    assert "zone.countdown.halfway.dynamic" in {row.phrase_id for row in rows}
    assert "zone.main_started.2" in {row.phrase_id for row in rows}
    assert "zone.watch_disconnected.1" in {row.phrase_id for row in rows}


def test_build_runtime_event_phrase_map_groups_active_variants_by_event():
    event_map = review.build_runtime_event_phrase_map()

    assert event_map["main_started"] == [
        "zone.main_started.1",
        "zone.main_started.2",
    ]
    assert event_map["above_zone"] == [
        "zone.above.default.1",
        "zone.above.default.2",
    ]
    assert event_map["in_zone"] == [
        "zone.in_zone.default.1",
        "zone.in_zone.default.2",
        "zone.in_zone.default.3",
    ]
    assert event_map["interval_sustain_stage_1"] == [
        "interval.motivate.s1.1",
        "interval.motivate.s1.2",
    ]



def test_export_v2_review_writes_and_roundtrips(tmp_path: Path):
    rows = review.build_review_rows()

    csv_path = tmp_path / "phrase_catalog_sorted.csv"
    tsv_path = tmp_path / "phrase_catalog_sorted.tsv"
    json_path = tmp_path / "phrase_catalog_sorted.json"
    xlsx_path = tmp_path / "phrase_catalog_sorted.xlsx"

    editor.export_v2_review_csv(csv_path, rows)
    editor.export_v2_review_tsv(tsv_path, rows)
    editor.export_v2_review_json(json_path, rows)
    editor.export_v2_review_xlsx(xlsx_path, rows)

    assert csv_path.exists()
    assert tsv_path.exists()
    assert json_path.exists()
    assert xlsx_path.exists()

    csv_rows = editor.load_v2_review_rows(csv_path)
    tsv_rows = editor.load_v2_review_rows(tsv_path)
    json_rows = editor.load_v2_review_rows(json_path)
    xlsx_rows = editor.load_v2_review_rows(xlsx_path)

    assert len(csv_rows) == len(rows)
    assert len(tsv_rows) == len(rows)
    assert len(json_rows) == len(rows)
    assert len(xlsx_rows) == len(rows)
    assert csv_rows[0].phrase_id == rows[0].phrase_id
    assert xlsx_rows[-1].phrase_id == rows[-1].phrase_id



def test_export_v2_promoted_import_csv_filters_to_approved_active_rows(tmp_path: Path):
    rows = review.build_review_rows()
    approved_rows = []
    for row in rows:
        if row.phrase_id == "zone.above.default.1":
            approved_rows.append(replace(row, approved_for_import="yes"))
        elif row.phrase_id == "zone.watch_disconnected.1":
            approved_rows.append(replace(row, approved_for_import="yes"))
        else:
            approved_rows.append(row)

    out = tmp_path / "phrase_catalog_promoted.csv"
    count = editor.export_v2_promoted_import_csv(out, approved_rows)

    assert count == 2
    content = out.read_text(encoding="utf-8")
    assert "id,en,no" in content
    assert "zone.above.default.1" in content
    assert "zone.watch_disconnected.1" in content



def test_validate_review_rows_rejects_future_import_approval():
    rows = review.build_review_rows()
    mutated = []
    for row in rows:
        if row.phrase_id == "zone.above.default.3":
            mutated.append(replace(row, approved_for_import="yes"))
        else:
            mutated.append(row)

    errors = review.validate_review_rows(mutated)
    assert any("future row cannot be approved for import" in err for err in errors)
