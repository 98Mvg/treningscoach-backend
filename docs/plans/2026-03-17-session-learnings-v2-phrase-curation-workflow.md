# Session Learnings — 2026-03-17 V2 phrase curation workflow

## Goal

Improve the Coachi V2 phrase pack workflow without introducing a third parallel authoring path.

## Runtime/source-of-truth path

- Phrase curation source stays in `phrase_review_v2.py`
- Review/export/import tooling stays in `tools/phrase_catalog_editor.py`
- Pack generation stays in `tools/generate_audio_pack.py`
- `candidate_queue.py` and `tools/candidate_review.py` remain side tools only

## What changed

- Added explicit curation categories:
  - `instruction`
  - `context_progress`
- Export now supports category-first artifacts under `output/phrase_curation/`:
  - `<category>_current.md`
  - `<category>_working.json`
- Import now supports structured JSON operations:
  - `keep`
  - `edit`
  - `add_variant`

## Important implementation rule

For `add_variant`, next phrase id must be derived from the existing V2 review rows using `family + event`, not family alone.

Why:
- `zone.pause` contains both `pause_detected` and `pause_resumed`
- `zone.countdown` contains `countdown_30`, `countdown_15`, `countdown_5`, and `countdown_start`
- some ids use implicit base ids like `zone.countdown.start`, while others use numeric variant ids like `zone.phase.warmup.1`

If numbering is done only by family, new variants will land on the wrong id stem.

## Acceptance shape

The intended loop is now:

1. Export one category
2. Review only current active phrases
3. Paste edits/additions into JSON
4. Dry-run import
5. Apply import to `phrase_review_v2.py`
6. Regenerate normal V2 review/export as needed

## Guardrails for future work

- Do not bypass `approved_for_import` / `approved_for_recording`
- Do not let curation JSON directly affect pack generation
- Do not merge candidate queue into the runtime V2 review path
- Keep new user-added phrases as `future` by default until explicitly approved and recorded
