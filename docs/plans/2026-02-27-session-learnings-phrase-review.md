# 2026-02-27 Session Learnings — Phrase Review Workflow

## Goal completed
- Made the 380-phrase catalog easier to review and edit.
- Added a safe workflow to remove disliked words without manual editing of long source blocks.

## Single source of truth preserved
- `tts_phrase_catalog.py` remains the single source of truth.
- New tooling reads/writes this file directly, instead of adding parallel phrase stores.

## What was added
- `tools/phrase_catalog_editor.py`
  - `export` command generates readable review docs:
    - `output/phrase_review/phrase_catalog.md`
    - `output/phrase_review/phrase_catalog.csv`
    - `output/phrase_review/disliked_words.txt`
  - `remove-words` command:
    - supports `--words` and `--words-file`
    - supports language scope (`en`, `no`, `both`)
    - dry-run by default, `--apply` to write to source
    - prints preview of changed lines
- `tests_phaseb/test_phrase_catalog_editor.py`
  - validates cleanup behavior
  - validates word-file parsing/deduping
  - validates markdown export contract

## Additional user-friendly outputs generated
- 5-column editable sentence sheets for easier review:
  - `output/phrase_review/phrase_sentences_en_5wide.csv/.tsv`
  - `output/phrase_review/phrase_sentences_no_5wide.csv/.tsv`
  - `output/phrase_review/phrase_sentences_en_no_5wide.csv/.tsv`
- Browser/Word-readable variants:
  - `output/phrase_review/phrase_catalog_readable.html`
  - `output/phrase_review/phrase_catalog_readable.rtf`

## Validation
- `pytest -q tests_phaseb/test_phrase_catalog_editor.py` -> passed (`3 passed`)
- Dry-run of word removal verified expected preview behavior.

## Practical usage
1. Edit disliked words list:
   - `output/phrase_review/disliked_words.txt`
2. Preview:
   - `python3 tools/phrase_catalog_editor.py remove-words --words-file output/phrase_review/disliked_words.txt`
3. Apply:
   - `python3 tools/phrase_catalog_editor.py remove-words --words-file output/phrase_review/disliked_words.txt --apply`

## Key learning
- For large phrase sets, a two-step “export table + safe apply” flow is much faster and less error-prone than editing inline dictionaries manually.
