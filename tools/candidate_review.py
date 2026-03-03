#!/usr/bin/env python3
"""Review and manage candidate queue.

Usage examples:
  python3 tools/candidate_review.py list
  python3 tools/candidate_review.py list --status pending
  python3 tools/candidate_review.py approve cand_001 cand_002
  python3 tools/candidate_review.py reject cand_001 --note "too generic"
  python3 tools/candidate_review.py approve-valid
  python3 tools/candidate_review.py export --format xlsx
  python3 tools/candidate_review.py import --xlsx output/candidate_review.xlsx
  python3 tools/candidate_review.py promote --dry-run
  python3 tools/candidate_review.py promote --apply
"""

from __future__ import annotations

import argparse
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import candidate_queue as cq


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_summary(queue: list[dict]) -> str:
    buckets: dict[str, int] = {}
    for candidate in queue:
        status = str(candidate.get("status") or "unknown")
        buckets[status] = buckets.get(status, 0) + 1
    if not buckets:
        return "Total: 0"
    parts = [f"{k}: {v}" for k, v in sorted(buckets.items())]
    return f"Total: {sum(buckets.values())} | " + " | ".join(parts)


def cmd_list(args: argparse.Namespace) -> int:
    queue = cq.load_queue()
    selected = queue
    if args.status:
        selected = [c for c in queue if str(c.get("status") or "") == args.status]

    if not selected:
        print("No candidates found.")
        print(_status_summary(queue))
        return 0

    print(f"{'ID':<32} {'Status':<10} {'Family':<26} {'Valid':<6} {'EN':<30} {'NO':<30}")
    print("-" * 136)
    for c in selected:
        cid = str(c.get("candidate_id") or "?")[:30]
        status = str(c.get("status") or "?")
        family = str(c.get("phrase_family") or "?")[:24]
        valid = "Y" if c.get("validation", {}).get("passed") else "N"
        en = str(c.get("generated_text_en") or "")[:28]
        no = str(c.get("generated_text_no") or "")[:28]
        print(f"{cid:<32} {status:<10} {family:<26} {valid:<6} {en:<30} {no:<30}")

    print("")
    print(_status_summary(queue))
    return 0


def _apply_status_update(queue: list[dict], candidate_ids: list[str], to_status: str, note: str | None = None) -> int:
    lookup = set(candidate_ids)
    now = _now_iso()
    count = 0
    for candidate in queue:
        cid = str(candidate.get("candidate_id") or "")
        if cid not in lookup:
            continue
        if str(candidate.get("status") or "") != "pending":
            print(f"  Skip {cid} - status is '{candidate.get('status')}', not 'pending'")
            continue
        candidate["status"] = to_status
        candidate["reviewed_at"] = now
        if note is not None:
            candidate["reviewer_note"] = note
        count += 1
    return count


def cmd_approve(args: argparse.Namespace) -> int:
    queue = cq.load_queue()
    count = _apply_status_update(queue, args.candidate_ids, "approved")
    cq.save_queue(queue)
    print(f"Approved {count} candidates.")
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    queue = cq.load_queue()
    count = _apply_status_update(queue, args.candidate_ids, "rejected", args.note or None)
    cq.save_queue(queue)
    print(f"Rejected {count} candidates.")
    return 0


def cmd_approve_valid(_: argparse.Namespace) -> int:
    queue = cq.load_queue()
    now = _now_iso()
    count = 0
    for candidate in queue:
        if str(candidate.get("status") or "") != "pending":
            continue
        if not bool(candidate.get("validation", {}).get("passed")):
            continue
        candidate["status"] = "approved"
        candidate["reviewed_at"] = now
        count += 1
    cq.save_queue(queue)
    print(f"Approved {count} valid pending candidates.")
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    queue = cq.load_queue()
    approved = [c for c in queue if str(c.get("status") or "") == "approved"]
    if not approved:
        print("No approved candidates to promote.")
        return 0

    print(f"Promoting {len(approved)} approved candidates:")
    for candidate in approved:
        family = candidate.get("phrase_family")
        en = candidate.get("generated_text_en")
        no = candidate.get("generated_text_no")
        print(f"  {family} - en=\"{en}\" no=\"{no}\"")

    assigned_ids = cq.promote_to_catalog(queue, dry_run=not args.apply)
    if assigned_ids:
        print("\nAssigned phrase IDs:")
        for phrase_id in assigned_ids:
            print(f"  {phrase_id}")

    if args.apply:
        cq.save_queue(queue)
        print("\nPromotion state saved to queue (status=promoted + promoted_phrase_id).")
        print("Catalog source update is not automatic in current candidate_queue implementation.")
    else:
        print("\nDry run only. Re-run with --apply to persist promoted status in queue.")
    return 0


REVIEW_COLUMNS = ["candidate_id", "status", "phrase_family", "en", "no", "validation", "model", "reviewer_note"]
REVIEW_COL_WIDTHS = [34.0, 14.0, 28.0, 44.0, 44.0, 34.0, 16.0, 30.0]
_XLSX_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _xml_text(value: str) -> str:
    return escape(value).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "&#10;")


def _col_label(idx: int) -> str:
    out = ""
    current = idx
    while current > 0:
        current, rem = divmod(current - 1, 26)
        out = chr(65 + rem) + out
    return out


def _cell_ref(col_idx: int, row_idx: int) -> str:
    return f"{_col_label(col_idx)}{row_idx}"


def _cell_inline(col_idx: int, row_idx: int, value: str, style: int) -> str:
    ref = _cell_ref(col_idx, row_idx)
    return (
        f'<c r="{ref}" s="{style}" t="inlineStr">'
        f'<is><t xml:space="preserve">{_xml_text(value)}</t></is></c>'
    )


def cmd_export(args: argparse.Namespace) -> int:
    if args.format != "xlsx":
        print(f"Unsupported format: {args.format}")
        return 2

    queue = cq.load_queue()
    pending = [c for c in queue if str(c.get("status") or "") == "pending"]
    if not pending:
        print("No pending candidates to export.")
        return 0

    output_dir = Path(PROJECT_ROOT) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = output_dir / "candidate_review.xlsx"

    sheet_rows: list[str] = []
    header_cells = "".join(_cell_inline(i, 1, col, 1) for i, col in enumerate(REVIEW_COLUMNS, start=1))
    sheet_rows.append(f'<row r="1" ht="24" customHeight="1">{header_cells}</row>')

    for excel_row, candidate in enumerate(pending, start=2):
        validation = candidate.get("validation", {})
        if validation.get("passed"):
            validation_str = "PASS"
        else:
            validation_str = "FAIL: " + "; ".join(validation.get("reasons", []))

        cells = [
            _cell_inline(1, excel_row, str(candidate.get("candidate_id") or ""), 0),
            _cell_inline(2, excel_row, str(candidate.get("status") or ""), 0),
            _cell_inline(3, excel_row, str(candidate.get("phrase_family") or ""), 0),
            _cell_inline(4, excel_row, str(candidate.get("generated_text_en") or ""), 0),
            _cell_inline(5, excel_row, str(candidate.get("generated_text_no") or ""), 0),
            _cell_inline(6, excel_row, validation_str, 0),
            _cell_inline(7, excel_row, str(candidate.get("model") or ""), 0),
            _cell_inline(8, excel_row, str(candidate.get("reviewer_note") or ""), 0),
        ]
        sheet_rows.append(f'<row r="{excel_row}">{"".join(cells)}</row>')

    last_row = max(2, len(pending) + 1)
    cols_xml = "".join(
        f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>'
        for i, w in enumerate(REVIEW_COL_WIDTHS, start=1)
    )
    max_ref = _cell_ref(len(REVIEW_COLUMNS), last_row)

    data_val = (
        f'<dataValidations count="1"><dataValidation type="list" allowBlank="1" '
        f'showErrorMessage="1" sqref="B2:B{last_row}">'
        f'<formula1>"pending,approved,rejected"</formula1>'
        f"</dataValidation></dataValidations>"
    )

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{max_ref}"/>'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        '</sheetView></sheetViews>'
        '<sheetFormatPr defaultRowHeight="20"/>'
        f"<cols>{cols_xml}</cols>"
        f"<sheetData>{''.join(sheet_rows)}</sheetData>"
        f'<autoFilter ref="A1:{max_ref}"/>'
        f"{data_val}"
        '</worksheet>'
    )

    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2">'
        '<font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>'
        '</fonts>'
        '<fills count="3">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/></patternFill></fill>'
        '</fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1">'
        '<alignment horizontal="center" wrapText="1"/></xf>'
        '</cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Candidates" sheetId="1" r:id="rId1"/></sheets>'
        '<calcPr calcId="0" fullCalcOnLoad="1"/>'
        '</workbook>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    pkg_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )

    with zipfile.ZipFile(xlsx_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", pkg_rels)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        archive.writestr("xl/styles.xml", styles_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)

    print(f"Exported {len(pending)} pending candidates to {xlsx_path}")
    print("Edit status (pending/approved/rejected) and reviewer_note, then import.")
    return 0


def _col_index(ref: str) -> int:
    col = 0
    for ch in ref:
        if ch.isalpha():
            col = col * 26 + (ord(ch.upper()) - 64)
        else:
            break
    return col


def _cell_text(cell: ET.Element) -> str:
    is_el = cell.find(f"{{{_XLSX_NS}}}is")
    if is_el is not None:
        t_el = is_el.find(f"{{{_XLSX_NS}}}t")
        if t_el is not None and t_el.text:
            return t_el.text
    v_el = cell.find(f"{{{_XLSX_NS}}}v")
    if v_el is not None and v_el.text:
        return v_el.text
    return ""


def cmd_import(args: argparse.Namespace) -> int:
    xlsx_path = Path(args.xlsx)
    if not xlsx_path.is_absolute():
        xlsx_path = Path(PROJECT_ROOT) / xlsx_path
    if not xlsx_path.exists():
        print(f"File not found: {xlsx_path}")
        return 2

    with zipfile.ZipFile(xlsx_path, "r") as archive:
        sheet_xml = archive.read("xl/worksheets/sheet1.xml")

    root = ET.fromstring(sheet_xml)
    rows: list[dict[str, str]] = []
    for row_el in root.iter(f"{{{_XLSX_NS}}}row"):
        if row_el.get("r") == "1":
            continue
        cells: dict[int, str] = {}
        for cell in row_el.iter(f"{{{_XLSX_NS}}}c"):
            ref = str(cell.get("r") or "")
            col = _col_index(ref)
            cells[col] = _cell_text(cell).strip()
        cid = cells.get(1, "")
        status = cells.get(2, "")
        note = cells.get(8, "")
        if cid:
            rows.append({"candidate_id": cid, "status": status, "reviewer_note": note})

    queue = cq.load_queue()
    now = _now_iso()
    changes = 0

    for row in rows:
        for candidate in queue:
            if str(candidate.get("candidate_id") or "") != row["candidate_id"]:
                continue
            new_status = row["status"]
            if new_status in ("approved", "rejected") and str(candidate.get("status") or "") == "pending":
                candidate["status"] = new_status
                candidate["reviewed_at"] = now
                if row["reviewer_note"]:
                    candidate["reviewer_note"] = row["reviewer_note"]
                changes += 1
            break

    cq.save_queue(queue)
    print(f"Imported {len(rows)} rows, applied {changes} status changes.")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review and manage candidate queue")
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List candidates")
    list_cmd.add_argument("--status", help="Filter status: pending/approved/rejected/promoted/skipped")

    approve_cmd = sub.add_parser("approve", help="Approve specific candidates")
    approve_cmd.add_argument("candidate_ids", nargs="+", help="Candidate IDs")

    reject_cmd = sub.add_parser("reject", help="Reject specific candidates")
    reject_cmd.add_argument("candidate_ids", nargs="+", help="Candidate IDs")
    reject_cmd.add_argument("--note", help="Rejection note")

    sub.add_parser("approve-valid", help="Approve all pending candidates that passed validation")

    export_cmd = sub.add_parser("export", help="Export pending queue to spreadsheet")
    export_cmd.add_argument("--format", default="xlsx", choices=["xlsx"], help="Export format")

    import_cmd = sub.add_parser("import", help="Import reviewed spreadsheet")
    import_cmd.add_argument("--xlsx", required=True, help="Path to xlsx")

    promote_cmd = sub.add_parser("promote", help="Promote approved entries to promoted state")
    mode = promote_cmd.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview promotion only")
    mode.add_argument("--apply", action="store_true", help="Persist promoted status in queue")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "list":
        return cmd_list(args)
    if args.command == "approve":
        return cmd_approve(args)
    if args.command == "reject":
        return cmd_reject(args)
    if args.command == "approve-valid":
        return cmd_approve_valid(args)
    if args.command == "export":
        return cmd_export(args)
    if args.command == "import":
        return cmd_import(args)
    if args.command == "promote":
        # default if no explicit mode is dry-run
        if not args.apply:
            args.dry_run = True
        return cmd_promote(args)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
