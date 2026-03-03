# Welcome Rotation + XLSX/Latest Workflow

## Purpose
This workflow keeps welcome speech:
1. non-repetitive (utterance-id rotation),
2. text/audio-correct (text bound to selected utterance_id),
3. easy to review/edit in spreadsheet format.

## Runtime behavior (source of truth)
1. `/welcome` selects a `welcome.*` utterance ID from `tts_phrase_catalog.py`.
2. Selection uses persisted anti-repeat rotation state:
   - avoids recent K utterances (`WELCOME_ROTATION_RECENT_K`, default 2),
   - avoids reuse within 24h (`WELCOME_ROTATION_AVOID_HOURS`, default 24),
   - state file: `output/cache/utterance_rotation_state.json`.
3. `/welcome` returns:
   - `utterance_id`
   - `text` (exact phrase text for that ID/language)
   - `lang`
   - `category`
   - `audio_url` (optional, pack URL when configured)
4. iOS resolves welcome audio by `utterance_id` in this order:
   - bundled CoreAudioPack
   - downloaded local pack
   - R2 pack fetch
   - backend dynamic fallback (if available)

## Edit workflow (XLSX)
1. Export phrase catalog:
   - `python3 tools/phrase_catalog_editor.py export --format xlsx`
2. Edit welcome rows in:
   - `output/phrase_review/phrase_catalog.xlsx`
   - IDs to edit are `welcome.standard.*`, `welcome.beginner.*`, `welcome.breath.*`
3. Import and apply:
   - dry run: `python3 tools/phrase_catalog_editor.py import --xlsx output/phrase_review/phrase_catalog.xlsx`
   - apply: `python3 tools/phrase_catalog_editor.py import --xlsx output/phrase_review/phrase_catalog.xlsx --apply`

## Validation guardrails
`phrase_catalog_editor` now validates welcome IDs before export/import:
1. ID format must be `welcome.<group>.<n>`
2. numbering must be contiguous per group (`1..N`)
3. both `en` and `no` text must be non-empty

If validation fails, tooling exits with clear errors.

## Audio pack publish (latest.json flow)
1. Generate pack:
   - `python3 tools/generate_audio_pack.py --version v1`
2. Upload + update latest:
   - `python3 tools/generate_audio_pack.py --version v1 --upload`
3. Verify:
   - `output/audio_pack/latest.json` points to current manifest
   - active manifest includes edited `welcome.*` IDs
4. On app launch/workout start, iOS sync uses latest manifest and resolves welcome by returned `utterance_id`.

