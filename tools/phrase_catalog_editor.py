#!/usr/bin/env python3
"""
Phrase catalog review + cleanup helper.

Usage examples:
  python3 tools/phrase_catalog_editor.py export --format both
  python3 tools/phrase_catalog_editor.py export --format xlsx
  python3 tools/phrase_catalog_editor.py import --xlsx output/phrase_review/phrase_catalog.xlsx
  python3 tools/phrase_catalog_editor.py import --xlsx output/phrase_review/phrase_catalog.xlsx --apply
  python3 tools/phrase_catalog_editor.py remove-words --words "pathetic,embarrassing" --language en
  python3 tools/phrase_catalog_editor.py remove-words --words-file output/phrase_review/disliked_words.txt --apply
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tts_phrase_catalog import PHRASE_CATALOG  # noqa: E402


SOURCE_FILE = PROJECT_ROOT / "tts_phrase_catalog.py"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "phrase_review"

XLSX_COLUMNS = [
    "index",
    "id",
    "section",
    "bucket",
    "persona",
    "priority",
    "en",
    "no",
    "en_words",
    "no_words",
    "en_chars",
    "no_chars",
    "dup_en",
    "dup_no",
    "section_ok",
    "review_status",
    "notes",
    "action_needed",
]

XLSX_COLUMN_WIDTHS = [
    8.0,
    34.0,
    20.0,
    24.0,
    18.0,
    10.0,
    54.0,
    54.0,
    10.0,
    10.0,
    10.0,
    10.0,
    10.0,
    10.0,
    12.0,
    16.0,
    30.0,
    14.0,
]


@dataclass(frozen=True)
class PhraseRow:
    index: int
    phrase_id: str
    section: str
    bucket: str
    persona: str
    priority: str
    en: str
    no: str


def _rows() -> list[PhraseRow]:
    rows: list[PhraseRow] = []
    for idx, phrase in enumerate(PHRASE_CATALOG, start=1):
        phrase_id = str(phrase["id"])
        parts = phrase_id.split(".")
        section = ".".join(parts[:2]) if len(parts) >= 2 else phrase_id
        bucket = ".".join(parts[:3]) if len(parts) >= 3 else section
        rows.append(
            PhraseRow(
                index=idx,
                phrase_id=phrase_id,
                section=section,
                bucket=bucket,
                persona=str(phrase.get("persona", "")),
                priority=str(phrase.get("priority", "")),
                en=str(phrase.get("en", "")),
                no=str(phrase.get("no", "")),
            )
        )
    return rows


def _escape_md_cell(value: str) -> str:
    return value.replace("|", r"\|").replace("\n", " ").strip()


def export_csv(path: Path, rows: list[PhraseRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["index", "id", "section", "bucket", "persona", "priority", "en", "no"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "index": row.index,
                    "id": row.phrase_id,
                    "section": row.section,
                    "bucket": row.bucket,
                    "persona": row.persona,
                    "priority": row.priority,
                    "en": row.en,
                    "no": row.no,
                }
            )


def export_markdown(path: Path, rows: list[PhraseRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Phrase Catalog Review")
    lines.append("")
    lines.append(f"Total phrases: **{len(rows)}**")
    lines.append("")
    lines.append("Tips:")
    lines.append("- Use the CSV for fast filtering in Numbers/Excel.")
    lines.append("- Add disliked words to `output/phrase_review/disliked_words.txt` (one per line).")
    lines.append("- Run `python3 tools/phrase_catalog_editor.py remove-words --words-file output/phrase_review/disliked_words.txt --apply`.")
    lines.append("")

    current_section = None
    for row in rows:
        if row.section != current_section:
            current_section = row.section
            lines.append(f"## {current_section}")
            lines.append("")
            lines.append("| # | id | persona | priority | English | Norwegian |")
            lines.append("|---:|---|---|---|---|---|")
        lines.append(
            f"| {row.index} | `{_escape_md_cell(row.phrase_id)}` | {_escape_md_cell(row.persona)} | "
            f"{_escape_md_cell(row.priority)} | {_escape_md_cell(row.en)} | {_escape_md_cell(row.no)} |"
        )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def _col_label(idx: int) -> str:
    out = ""
    current = idx
    while current > 0:
        current, rem = divmod(current - 1, 26)
        out = chr(65 + rem) + out
    return out


def _cell_ref(col_idx: int, row_idx: int) -> str:
    return f"{_col_label(col_idx)}{row_idx}"


def _xml_text(value: str) -> str:
    return escape(value).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "&#10;")


def _cell_inline(col_idx: int, row_idx: int, value: str, style: int) -> str:
    ref = _cell_ref(col_idx, row_idx)
    return (
        f'<c r="{ref}" s="{style}" t="inlineStr">'
        f'<is><t xml:space="preserve">{_xml_text(value)}</t></is></c>'
    )


def _cell_number(col_idx: int, row_idx: int, value: int, style: int) -> str:
    ref = _cell_ref(col_idx, row_idx)
    return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'


def _cell_formula(col_idx: int, row_idx: int, formula: str, style: int) -> str:
    ref = _cell_ref(col_idx, row_idx)
    return f'<c r="{ref}" s="{style}"><f>{escape(formula)}</f></c>'


def _build_catalog_sheet(rows: list[PhraseRow]) -> str:
    ordered_rows = sorted(rows, key=lambda item: (item.section, item.bucket, item.phrase_id, item.index))
    sheet_rows: list[str] = []

    header_cells = "".join(_cell_inline(i, 1, title, 1) for i, title in enumerate(XLSX_COLUMNS, start=1))
    sheet_rows.append(f'<row r="1" ht="24" customHeight="1">{header_cells}</row>')

    for excel_row, row in enumerate(ordered_rows, start=2):
        cells: list[str] = []
        cells.append(_cell_number(1, excel_row, row.index, 2))
        cells.append(_cell_inline(2, excel_row, row.phrase_id, 2))
        cells.append(_cell_inline(3, excel_row, row.section, 2))
        cells.append(_cell_inline(4, excel_row, row.bucket, 2))
        cells.append(_cell_inline(5, excel_row, row.persona, 2))
        cells.append(_cell_inline(6, excel_row, row.priority, 2))
        cells.append(_cell_inline(7, excel_row, row.en, 2))
        cells.append(_cell_inline(8, excel_row, row.no, 2))

        cells.append(
            _cell_formula(
                9,
                excel_row,
                f'IF(LEN(TRIM(G{excel_row}))=0,0,LEN(TRIM(G{excel_row}))-LEN(SUBSTITUTE(TRIM(G{excel_row})," ",""))+1)',
                3,
            )
        )
        cells.append(
            _cell_formula(
                10,
                excel_row,
                f'IF(LEN(TRIM(H{excel_row}))=0,0,LEN(TRIM(H{excel_row}))-LEN(SUBSTITUTE(TRIM(H{excel_row})," ",""))+1)',
                3,
            )
        )
        cells.append(_cell_formula(11, excel_row, f"LEN(G{excel_row})", 3))
        cells.append(_cell_formula(12, excel_row, f"LEN(H{excel_row})", 3))
        cells.append(_cell_formula(13, excel_row, f'IF(COUNTIF($G:$G,G{excel_row})>1,"DUP","")', 3))
        cells.append(_cell_formula(14, excel_row, f'IF(COUNTIF($H:$H,H{excel_row})>1,"DUP","")', 3))
        cells.append(_cell_formula(15, excel_row, f'IF(LEFT(B{excel_row},LEN(C{excel_row}))=C{excel_row},"OK","CHECK")', 3))
        cells.append(_cell_inline(16, excel_row, "Review", 4))
        cells.append(_cell_inline(17, excel_row, "", 4))
        cells.append(
            _cell_formula(
                18,
                excel_row,
                f'IF(OR(M{excel_row}="DUP",N{excel_row}="DUP",O{excel_row}="CHECK"),"CHECK","")',
                5,
            )
        )

        sheet_rows.append(f'<row r="{excel_row}">{"".join(cells)}</row>')

    last_row = max(2, len(ordered_rows) + 1)
    data_validation_block = (
        f'<dataValidations count="1"><dataValidation type="list" allowBlank="1" '
        f'showErrorMessage="1" sqref="P2:P{last_row}">'
        f'<formula1>"Review,Keep,Edit,Remove,Needs Translation"</formula1>'
        f"</dataValidation></dataValidations>"
    )

    cols_xml = "".join(
        f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>'
        for idx, width in enumerate(XLSX_COLUMN_WIDTHS, start=1)
    )
    max_ref = _cell_ref(len(XLSX_COLUMNS), last_row)

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<dimension ref="A1:{max_ref}"/>'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        '<sheetFormatPr defaultRowHeight="20"/>'
        f"<cols>{cols_xml}</cols>"
        f"<sheetData>{''.join(sheet_rows)}</sheetData>"
        f'<autoFilter ref="A1:{max_ref}"/>'
        f"{data_validation_block}"
        "</worksheet>"
    )


def _build_summary_sheet() -> str:
    row_cells: list[str] = []
    row_cells.append(
        '<row r="1" ht="24" customHeight="1">'
        f'{_cell_inline(1, 1, "Phrase Catalog QA Summary", 1)}'
        f'{_cell_inline(2, 1, "", 1)}'
        "</row>"
    )

    rows = [
        (3, "Total phrases", "COUNTA(Catalog!B:B)-1"),
        (4, "Duplicate English phrases", 'COUNTIF(Catalog!M:M,"DUP")'),
        (5, "Duplicate Norwegian phrases", 'COUNTIF(Catalog!N:N,"DUP")'),
        (6, "Section/id mismatches", 'COUNTIF(Catalog!O:O,"CHECK")'),
        (7, "Rows marked action_needed", 'COUNTIF(Catalog!R:R,"CHECK")'),
        (9, "Priority core", 'COUNTIF(Catalog!F:F,"core")'),
        (10, "Priority extended", 'COUNTIF(Catalog!F:F,"extended")'),
        (12, "Review status = Review", 'COUNTIF(Catalog!P:P,"Review")'),
        (13, "Review status = Keep", 'COUNTIF(Catalog!P:P,"Keep")'),
        (14, "Review status = Edit", 'COUNTIF(Catalog!P:P,"Edit")'),
        (15, "Review status = Remove", 'COUNTIF(Catalog!P:P,"Remove")'),
        (16, "Review status = Needs Translation", 'COUNTIF(Catalog!P:P,"Needs Translation")'),
    ]
    for row_number, label, formula in rows:
        row_cells.append(
            f'<row r="{row_number}">'
            f"{_cell_inline(1, row_number, label, 2)}"
            f"{_cell_formula(2, row_number, formula, 3)}"
            "</row>"
        )

    row_cells.append(
        '<row r="18">'
        f'{_cell_inline(1, 18, "Tip: filter the Catalog sheet by action_needed and review_status.", 2)}'
        f'{_cell_inline(2, 18, "", 2)}'
        "</row>"
    )

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<dimension ref="A1:B18"/>'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        '<sheetFormatPr defaultRowHeight="20"/>'
        '<cols>'
        '<col min="1" max="1" width="40" customWidth="1"/>'
        '<col min="2" max="2" width="18" customWidth="1"/>'
        "</cols>"
        f"<sheetData>{''.join(row_cells)}</sheetData>"
        "</worksheet>"
    )


def export_xlsx(path: Path, rows: list[PhraseRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="4">
    <font><sz val="11"/><color rgb="FF000000"/><name val="Calibri"/><family val="2"/></font>
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/><family val="2"/></font>
    <font><sz val="11"/><color rgb="FF1E7145"/><name val="Calibri"/><family val="2"/></font>
    <font><sz val="11"/><color rgb="FF1F4E78"/><name val="Calibri"/><family val="2"/></font>
  </fonts>
  <fills count="6">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF2F2F2"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFDDEBF7"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFD9D9D9"/></left>
      <right style="thin"><color rgb="FFD9D9D9"/></right>
      <top style="thin"><color rgb="FFD9D9D9"/></top>
      <bottom style="thin"><color rgb="FFD9D9D9"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="6">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <xf numFmtId="0" fontId="2" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1">
      <alignment vertical="top" wrapText="1"/>
    </xf>
    <xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="top" wrapText="1"/>
    </xf>
    <xf numFmtId="0" fontId="3" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment vertical="top" wrapText="1"/>
    </xf>
    <xf numFmtId="0" fontId="0" fillId="5" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="top" wrapText="1"/>
    </xf>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
  <dxfs count="0"/>
  <tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/>
</styleSheet>
"""

    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <bookViews><workbookView xWindow="0" yWindow="0" windowWidth="24000" windowHeight="12000"/></bookViews>
  <sheets>
    <sheet name="Catalog" sheetId="1" r:id="rId1"/>
    <sheet name="Summary" sheetId="2" r:id="rId2"/>
  </sheets>
  <calcPr calcId="191029" fullCalcOnLoad="1"/>
</workbook>
"""

    workbook_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""

    package_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>
"""

    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    core_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:creator>phrase_catalog_editor</dc:creator>"
        "<cp:lastModifiedBy>phrase_catalog_editor</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
        "</cp:coreProperties>"
    )
    app_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>phrase_catalog_editor</Application>"
        "</Properties>"
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        handle.writestr("[Content_Types].xml", content_types_xml)
        handle.writestr("_rels/.rels", package_rels_xml)
        handle.writestr("docProps/core.xml", core_xml)
        handle.writestr("docProps/app.xml", app_xml)
        handle.writestr("xl/workbook.xml", workbook_xml)
        handle.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        handle.writestr("xl/styles.xml", styles_xml)
        handle.writestr("xl/worksheets/sheet1.xml", _build_catalog_sheet(rows))
        handle.writestr("xl/worksheets/sheet2.xml", _build_summary_sheet())


def _collect_words(words_csv: str | None, words_file: str | None) -> list[str]:
    out: list[str] = []
    if words_csv:
        out.extend([token.strip() for token in words_csv.split(",") if token.strip()])
    if words_file:
        file_path = Path(words_file)
        if not file_path.is_absolute():
            file_path = PROJECT_ROOT / file_path
        if not file_path.exists():
            raise FileNotFoundError(f"Words file not found: {file_path}")
        out.extend(
            [
                line.strip()
                for line in file_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        )
    # Stable dedupe
    seen: set[str] = set()
    cleaned: list[str] = []
    for token in out:
        lowered = token.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        cleaned.append(token)
    return cleaned


def _compile_patterns(words: Iterable[str]) -> list[re.Pattern[str]]:
    patterns: list[re.Pattern[str]] = []
    for word in words:
        if any(ch.isspace() for ch in word):
            patterns.append(re.compile(re.escape(word), flags=re.IGNORECASE))
        else:
            patterns.append(re.compile(rf"(?<!\w){re.escape(word)}(?!\w)", flags=re.IGNORECASE))
    return patterns


def _cleanup_text(text: str) -> str:
    cleaned = re.sub(r"\s{2,}", " ", text)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\(\s+", "(", cleaned)
    cleaned = re.sub(r"\s+\)", ")", cleaned)
    cleaned = re.sub(r"^[-,.;:!? ]+", "", cleaned)
    return cleaned.strip()


def _remove_words_from_text(text: str, patterns: list[re.Pattern[str]]) -> str:
    updated = text
    for pattern in patterns:
        updated = pattern.sub("", updated)
    return _cleanup_text(updated)


def remove_words(
    *,
    words: list[str],
    language: str,
    apply_changes: bool,
) -> int:
    if not words:
        print("No words supplied. Use --words or --words-file.")
        return 2

    languages = ["en", "no"] if language == "both" else [language]
    patterns = _compile_patterns(words)

    source = SOURCE_FILE.read_text(encoding="utf-8")
    replacements: dict[str, str] = {}
    changed_rows: list[tuple[str, str, str, str]] = []

    for phrase in PHRASE_CATALOG:
        phrase_id = str(phrase["id"])
        for lang in languages:
            old_text = str(phrase.get(lang, ""))
            new_text = _remove_words_from_text(old_text, patterns)
            if new_text != old_text:
                old_token = f"\"{lang}\": {json.dumps(old_text, ensure_ascii=False)}"
                new_token = f"\"{lang}\": {json.dumps(new_text, ensure_ascii=False)}"
                replacements[old_token] = new_token
                changed_rows.append((phrase_id, lang, old_text, new_text))

    if not changed_rows:
        print("No phrase text matched the provided words.")
        return 0

    updated = source
    changed_tokens = 0
    for old_token, new_token in replacements.items():
        count = updated.count(old_token)
        if count > 0:
            changed_tokens += count
            updated = updated.replace(old_token, new_token)

    print(f"Words: {', '.join(words)}")
    print(f"Languages: {', '.join(languages)}")
    print(f"Phrase fields changed: {len(changed_rows)}")
    print(f"Source token replacements: {changed_tokens}")
    print("")
    print("Preview (first 25):")
    for phrase_id, lang, old_text, new_text in changed_rows[:25]:
        print(f"- {phrase_id} [{lang}]")
        print(f"    old: {old_text}")
        print(f"    new: {new_text}")
    if len(changed_rows) > 25:
        print(f"... and {len(changed_rows) - 25} more.")

    if not apply_changes:
        print("")
        print("Dry run only. Re-run with --apply to write changes.")
        return 0

    SOURCE_FILE.write_text(updated, encoding="utf-8")
    print("")
    print(f"Applied changes to {SOURCE_FILE}")
    return 0


# =============================================================================
# XLSX IMPORT — read edited spreadsheet back into tts_phrase_catalog.py
# =============================================================================

_XLSX_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


@dataclass(frozen=True)
class _XlsxRow:
    phrase_id: str
    en: str
    no: str
    review_status: str


def _col_index(ref: str) -> int:
    """Convert cell ref like 'B2' to 1-based column index (B → 2)."""
    col = 0
    for ch in ref:
        if ch.isalpha():
            col = col * 26 + (ord(ch.upper()) - 64)
        else:
            break
    return col


def _cell_text(cell: ET.Element) -> str:
    """Extract text from an XLSX cell element (inline string or value)."""
    # Inline string: <is><t>text</t></is>
    is_el = cell.find(f"{{{_XLSX_NS}}}is")
    if is_el is not None:
        t_el = is_el.find(f"{{{_XLSX_NS}}}t")
        if t_el is not None and t_el.text:
            return t_el.text
    # Plain value: <v>text</v>
    v_el = cell.find(f"{{{_XLSX_NS}}}v")
    if v_el is not None and v_el.text:
        return v_el.text
    return ""


def read_xlsx(path: Path) -> list[_XlsxRow]:
    """Read phrase rows from an exported XLSX (Catalog sheet = sheet1)."""
    rows: list[_XlsxRow] = []
    with zipfile.ZipFile(path, "r") as zf:
        sheet_xml = zf.read("xl/worksheets/sheet1.xml")

    root = ET.fromstring(sheet_xml)
    for row_el in root.iter(f"{{{_XLSX_NS}}}row"):
        row_num = row_el.get("r", "")
        if row_num == "1":
            continue  # skip header

        cells: dict[int, str] = {}
        for cell_el in row_el.iter(f"{{{_XLSX_NS}}}c"):
            ref = cell_el.get("r", "")
            col = _col_index(ref)
            cells[col] = _cell_text(cell_el)

        phrase_id = cells.get(2, "").strip()   # column B
        en = cells.get(7, "").strip()          # column G
        no = cells.get(8, "").strip()          # column H
        review_status = cells.get(16, "").strip()  # column P

        if phrase_id:
            rows.append(_XlsxRow(phrase_id=phrase_id, en=en, no=no, review_status=review_status))

    return rows


def import_xlsx(
    *,
    xlsx_path: Path,
    apply_changes: bool,
) -> int:
    """Import edited XLSX back into tts_phrase_catalog.py.

    Detects text changes in en/no columns and applies them to the source file.
    Rows marked review_status='Remove' are listed but NOT auto-deleted (safety).
    """
    if not xlsx_path.exists():
        print(f"File not found: {xlsx_path}")
        return 2

    xlsx_rows = read_xlsx(xlsx_path)
    if not xlsx_rows:
        print("No data rows found in XLSX.")
        return 2

    # Build lookup from current catalog
    catalog_by_id: dict[str, dict] = {}
    for phrase in PHRASE_CATALOG:
        catalog_by_id[str(phrase["id"])] = phrase

    # Diff
    text_changes: list[tuple[str, str, str, str]] = []  # (phrase_id, lang, old, new)
    removals: list[str] = []
    unknown_ids: list[str] = []

    for xlsx_row in xlsx_rows:
        if xlsx_row.review_status.lower() == "remove":
            removals.append(xlsx_row.phrase_id)
            continue

        catalog_entry = catalog_by_id.get(xlsx_row.phrase_id)
        if not catalog_entry:
            if xlsx_row.phrase_id:
                unknown_ids.append(xlsx_row.phrase_id)
            continue

        old_en = str(catalog_entry.get("en", ""))
        old_no = str(catalog_entry.get("no", ""))

        if xlsx_row.en and xlsx_row.en != old_en:
            text_changes.append((xlsx_row.phrase_id, "en", old_en, xlsx_row.en))
        if xlsx_row.no and xlsx_row.no != old_no:
            text_changes.append((xlsx_row.phrase_id, "no", old_no, xlsx_row.no))

    # Report
    print(f"XLSX import: {xlsx_path.name}")
    print(f"  Rows read: {len(xlsx_rows)}")
    print(f"  Text changes: {len(text_changes)}")
    if removals:
        print(f"  Marked for removal: {len(removals)} (manual delete required)")
        for pid in removals[:10]:
            print(f"    - {pid}")
        if len(removals) > 10:
            print(f"    ... and {len(removals) - 10} more")
    if unknown_ids:
        print(f"  Unknown IDs (not in catalog): {len(unknown_ids)}")
        for pid in unknown_ids[:5]:
            print(f"    - {pid}")

    if not text_changes:
        print("\nNo text changes detected.")
        return 0

    print("\nChanges:")
    for phrase_id, lang, old_text, new_text in text_changes[:30]:
        print(f"  {phrase_id} [{lang}]")
        print(f"    old: {old_text}")
        print(f"    new: {new_text}")
    if len(text_changes) > 30:
        print(f"  ... and {len(text_changes) - 30} more")

    if not apply_changes:
        print("\nDry run only. Re-run with --apply to write changes.")
        return 0

    # Apply: replace in source file
    source = SOURCE_FILE.read_text(encoding="utf-8")
    applied = 0
    for phrase_id, lang, old_text, new_text in text_changes:
        old_token = f"\"{lang}\": {json.dumps(old_text, ensure_ascii=False)}"
        new_token = f"\"{lang}\": {json.dumps(new_text, ensure_ascii=False)}"
        if old_token in source:
            source = source.replace(old_token, new_token, 1)
            applied += 1
        else:
            print(f"  ⚠️  Could not locate source token for {phrase_id} [{lang}]")

    SOURCE_FILE.write_text(source, encoding="utf-8")
    print(f"\nApplied {applied}/{len(text_changes)} changes to {SOURCE_FILE}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review and clean TTS phrase catalog.")
    sub = parser.add_subparsers(dest="command", required=True)

    export_cmd = sub.add_parser("export", help="Export phrase catalog in readable formats.")
    export_cmd.add_argument(
        "--format",
        choices=["csv", "md", "xlsx", "both", "all"],
        default="both",
        help="Output format.",
    )
    export_cmd.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to write exports.",
    )

    import_cmd = sub.add_parser("import", help="Import edited XLSX back into phrase catalog.")
    import_cmd.add_argument(
        "--xlsx",
        required=True,
        help="Path to edited XLSX file.",
    )
    import_cmd.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to tts_phrase_catalog.py (default is dry run).",
    )

    remove_cmd = sub.add_parser("remove-words", help="Remove disliked words from phrase text.")
    remove_cmd.add_argument("--words", default="", help="Comma-separated words/phrases.")
    remove_cmd.add_argument(
        "--words-file",
        default="",
        help="Path to text file with one word per line.",
    )
    remove_cmd.add_argument(
        "--language",
        choices=["en", "no", "both"],
        default="both",
        help="Which language text fields to update.",
    )
    remove_cmd.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to tts_phrase_catalog.py (default is dry run).",
    )

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "export":
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = PROJECT_ROOT / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        rows = _rows()
        if args.format in {"csv", "both", "all"}:
            csv_path = output_dir / "phrase_catalog.csv"
            export_csv(csv_path, rows)
            print(f"Wrote {csv_path}")
        if args.format in {"md", "both", "all"}:
            md_path = output_dir / "phrase_catalog.md"
            export_markdown(md_path, rows)
            print(f"Wrote {md_path}")
        if args.format in {"xlsx", "all"}:
            xlsx_path = output_dir / "phrase_catalog.xlsx"
            export_xlsx(xlsx_path, rows)
            print(f"Wrote {xlsx_path}")

        words_file = output_dir / "disliked_words.txt"
        if not words_file.exists():
            words_file.write_text(
                "# Put one disliked word or phrase per line.\n# Example:\n# pathetic\n# embarrassing\n",
                encoding="utf-8",
            )
            print(f"Created {words_file}")
        return 0

    if args.command == "import":
        xlsx_path = Path(args.xlsx)
        if not xlsx_path.is_absolute():
            xlsx_path = PROJECT_ROOT / xlsx_path
        return import_xlsx(xlsx_path=xlsx_path, apply_changes=args.apply)

    if args.command == "remove-words":
        words = _collect_words(args.words, args.words_file)
        return remove_words(words=words, language=args.language, apply_changes=args.apply)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
