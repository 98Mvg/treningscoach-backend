# 2026-02-27 Session Learnings — R2 Audio Pack Execution + Voice Safety

## What shipped today
- Completed and pushed R2 audio-pack rollout artifacts:
  - `tts_phrase_catalog.py` motivation cues (`motivation.1` to `motivation.10`)
  - `config.py` R2 env config (`R2_*`, `AUDIO_PACK_VERSION`)
  - `requirements.txt` (`boto3>=1.34.0`)
  - `.gitignore` audio-pack rules (ignore MP3 folders, keep manifests)
  - `tools/select_core_bundle.py`
  - `TreningsCoach/TreningsCoach/Resources/CoreAudioPack/` (108 bundled MP3 files)
  - `output/audio_pack/v1/manifest.json`
  - `output/audio_pack/latest.json`
- Added/confirmed speech transcript diagnostics hook in:
  - `TreningsCoach/TreningsCoach/Services/AudioPipelineDiagnostics.swift`

## Critical voice safety fix (single source of truth)
- Personal Trainer must never load toxic/performance pre-cached audio.
- Enforced with persona-scoped cache paths + toxic ID guard in:
  - `TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift`
- Audio pack generation also hardened:
  - `tools/generate_audio_pack.py`
  - Non-`toxic.*` IDs are forced to `personal_trainer`.

## Validation performed
- Python checks passed:
  - `python3 tts_phrase_catalog.py`
  - `python3 -m py_compile tts_phrase_catalog.py config.py tools/generate_audio_pack.py tools/select_core_bundle.py`
  - `python3 tools/generate_audio_pack.py --dry-run --version v1 --sample-one --sample-language en`
- Tests passed:
  - `pytest -q tests_phaseb/test_generate_audio_pack_sample_and_latest.py tests_phaseb/test_r2_audio_pack_contract.py tests_phaseb/test_phrase_catalog_editor.py`
- iOS build passed:
  - `xcodebuild ... -project TreningsCoach/TreningsCoach.xcodeproj ... build`

## Key architecture decision to keep
- Do **not** add parallel iOS speech layers (`AudioPackManager.swift` + `SpeechCoordinator.swift`) if equivalent behavior already exists in `WorkoutViewModel.swift`.
- Keep one runtime speech path and evolve it in-place.

## Operational note
- This terminal environment had outbound DNS blocked during checks (`curl: Could not resolve host`), so remote Render/R2 endpoint verification can fail here even if deployment is healthy.

## Do-not-regress checklist
- Keep event-capable speech ownership rule:
  - if `events` field exists (even empty), event router owns speech decisions.
- Keep `hr_bpm=0` contract when unavailable.
- Keep persona separation in local bundle/cache/R2 lookup paths.
- Keep `toxic.*` utterance suppression for Personal Trainer persona.
