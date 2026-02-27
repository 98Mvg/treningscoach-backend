#!/usr/bin/env python3
"""
Phrase catalog review + cleanup helper.

Usage examples:
  python3 tools/phrase_catalog_editor.py export --format both
  python3 tools/phrase_catalog_editor.py remove-words --words "pathetic,embarrassing" --language en
  python3 tools/phrase_catalog_editor.py remove-words --words-file output/phrase_review/disliked_words.txt --apply
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tts_phrase_catalog import PHRASE_CATALOG  # noqa: E402


SOURCE_FILE = PROJECT_ROOT / "tts_phrase_catalog.py"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "phrase_review"


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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review and clean TTS phrase catalog.")
    sub = parser.add_subparsers(dest="command", required=True)

    export_cmd = sub.add_parser("export", help="Export phrase catalog in readable formats.")
    export_cmd.add_argument(
        "--format",
        choices=["csv", "md", "both"],
        default="both",
        help="Output format.",
    )
    export_cmd.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to write exports.",
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
        if args.format in {"csv", "both"}:
            csv_path = output_dir / "phrase_catalog.csv"
            export_csv(csv_path, rows)
            print(f"Wrote {csv_path}")
        if args.format in {"md", "both"}:
            md_path = output_dir / "phrase_catalog.md"
            export_markdown(md_path, rows)
            print(f"Wrote {md_path}")

        words_file = output_dir / "disliked_words.txt"
        if not words_file.exists():
            words_file.write_text(
                "# Put one disliked word or phrase per line.\n# Example:\n# pathetic\n# embarrassing\n",
                encoding="utf-8",
            )
            print(f"Created {words_file}")
        return 0

    if args.command == "remove-words":
        words = _collect_words(args.words, args.words_file)
        return remove_words(words=words, language=args.language, apply_changes=args.apply)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
