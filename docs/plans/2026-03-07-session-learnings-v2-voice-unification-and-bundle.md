# 2026-03-07 Session Learnings — V2 Voice Unification And Full Bundle

## What changed
- Added V2-only language voice overrides in the existing pack generator:
  - English: `9MPvdQh2pLsLhn7SuiIS`
  - Norwegian: `nhvaqgRyAq6BmFs3WcdX`
- Kept V1 pacing/energy by reusing the current `VOICE_SETTINGS["v1"]` fallback for `v2`.
- Gated V2 generation to approved `active` and `active_secondary` rows from `output/spreadsheet/phrase_catalog_sorted.csv`.
- Rebuilt the iOS bundle from the V2 manifest instead of the old curated category subset.
- Removed stale bundled MP3s so the app bundle no longer carries legacy V1 workout-cue audio.

## Repo truths confirmed
- Continuous workout ownership is still deterministic-first in [`zone_event_motor.py`](/Users/mariusgaarder/Documents/treningscoach/zone_event_motor.py).
- The pack pipeline remains:
  - review artifact
  - promoted `id,en,no` CSV
  - [`tts_phrase_catalog.py`](/Users/mariusgaarder/Documents/treningscoach/tts_phrase_catalog.py)
  - [`tools/generate_audio_pack.py`](/Users/mariusgaarder/Documents/treningscoach/tools/generate_audio_pack.py)
  - `output/audio_pack/<version>/manifest.json`
  - R2 `latest.json`
  - [`AudioPackSyncManager.swift`](/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/AudioPackSyncManager.swift)
- The app still expects bundled `wake_ack.*` and `welcome.standard.1-5` as local-first audio dependencies, so they must remain in the V2 bundle even though they are not part of the active workout cue review set.

## Important implementation details
- `tools/generate_audio_pack.py` now:
  - filters `v2` generation to approved active rows
  - adds required infrastructure IDs:
    - `wake_ack.en.default`
    - `wake_ack.no.default`
    - `welcome.standard.1-5`
  - forces `voice_id_override` by language for `v2`
  - prunes stale MP3s from `output/audio_pack/v2`
  - uploads only manifest-listed files
- `tools/select_core_bundle.py` now:
  - keeps curated behavior for non-`v2`
  - uses manifest-driven full copy for `v2`
  - clears stale `CoreAudioPack` MP3s before copying

## V2 output facts from this run
- Approved review rows promoted: `50`
- Text changes applied back into `tts_phrase_catalog.py`: `20`
- Generated V2 pack:
  - `57` phrase IDs
  - `114` MP3 files
- Bundle rebuild:
  - copied `114`
  - removed stale bundled files: `206`
- Public activation:
  - `latest.json` points to `v2`
  - public `v2/manifest.json` reports `114` files and `57` phrases

## Verification outcomes
- Tooling/runtime tests passed after the change: `116 passed`
- Generic iOS build succeeded after the new V2 bundle copy.
- Public R2 verification confirmed:
  - `zone.structure.work.1`
  - `zone.hr_poor_timing.1`
  - `wake_ack.en.default`
  - `welcome.standard.1`
  are all present in the active V2 manifest.

## Remaining caveat
- Final simulator-side sync-log verification was blocked by a `CoreSimulatorService` failure after the pack was already generated, uploaded, and bundled.
- That issue did not affect the actual V2 pack publication or the rebuilt app bundle.

## Next-step rule
- If bundle scope changes again, treat `wake_ack.*` and `welcome.standard.1-5` as required infrastructure unless the iOS lookup/prefetch path is changed deliberately.
