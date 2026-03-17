# Session Learnings — V2 R2 Runtime Truth

Date: 2026-03-17

## Problem

The app runtime already treated R2 as the active pack source through:

- `latest.json`
- `vX/manifest.json`
- `AudioPackSyncManager.swift`

But V2 pack generation was still split:

- text lived in `tts_phrase_catalog.py`
- V2 review rows only acted as an approval/ID filter

That created a subtle double-truth:

- app/runtime truth = R2 manifest + files
- generation truth = catalog text
- review truth = what the team thought V2 currently was

## Existing runtime path

Single existing path, no new architecture:

1. Local authoring/curation in `phrase_review_v2.py`
2. Pack generation in `tools/generate_audio_pack.py`
3. Upload to R2 as:
   - `v2/manifest.json`
   - `latest.json`
   - `v2/<lang>/<phrase_id>.mp3`
4. App sync in `AudioPackSyncManager.swift`
5. Playback resolution in `WorkoutViewModel.swift`

## Fix

### 1. V2 generator now uses runtime review rows as the local control surface

`tools/generate_audio_pack.py` now builds V2 phrases from active runtime rows in `phrase_review_v2.py` rather than only filtering `tts_phrase_catalog.py` by approved IDs.

That means:

- local V2 review/source decides which runtime phrases are in the pack
- R2 manifest/files remain the truth the app syncs from
- `tts_phrase_catalog.py` is no longer the hidden primary text source for V2 pack generation

### 2. Dynamic ids no longer hard-bypass the pack

`WorkoutViewModel.swift` previously treated any `*.dynamic` phrase id as:

- skip local pack
- skip R2 pack
- use backend TTS only

That made R2 impossible to be the real source for those ids, even if they were curated and uploaded.

Now the path is:

1. try local synced pack
2. try R2 download
3. only then fall back to backend TTS

This preserves fallback behavior without breaking R2 truth.

### 3. One-step sync stays on the same generator path

Added `--sync-r2` to `tools/generate_audio_pack.py`.

It keeps the existing pipeline together:

- generate/update audio pack
- write `manifest.json`
- write `latest.json`
- upload to R2
- prune stale R2 mp3 objects

No second upload script or alternate manifest flow was introduced.

## Why this is the right shape

- Keeps one runtime pack path
- Keeps app sync manifest-driven
- Removes hidden text drift between catalog and V2 review
- Keeps backend TTS as fallback, not primary, for curated pack ids

## Guardrails

- Do not reintroduce a second “review says one thing, generator says another” V2 source.
- If a phrase id is intended to exist in the synced pack, do not hard-bypass local/R2 playback based only on naming.
- If the user wants R2 to be truth, changes must flow through `tools/generate_audio_pack.py`, not a parallel uploader.

## Verification used in this pass

- `pytest -q tests_phaseb/test_generate_audio_pack_sample_and_latest.py tests_phaseb/test_phrase_catalog_v2_review.py tests_phaseb/test_r2_audio_pack_contract.py`
- `python3 -m py_compile phrase_review_v2.py tools/generate_audio_pack.py`
- `python3 tools/generate_audio_pack.py --version v2 --dry-run`
- `xcodebuild -project TreningsCoach/TreningsCoach.xcodeproj -scheme TreningsCoach ... build`

