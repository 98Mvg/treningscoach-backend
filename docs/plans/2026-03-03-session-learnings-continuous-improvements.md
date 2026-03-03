# 2026-03-03 Session Learnings — Continuous Improvements

## Scope of this session
This session focused on stabilizing the Workout Talk v1 path (wake-word + button), preserving single source of truth behavior, and keeping audio-pack/runtime contracts in sync.
It also finalized countdown reliability and startup HR-loss behavior in the zone-event path.

## What worked (keep doing this)
1. Keep one runtime path:
   - `/coach/continuous` remains zone-event owned.
   - `/coach/talk` is a separate request path for user-initiated talk only.
2. Event-first on iOS:
   - If backend returns `events` field (even empty), treat it as event-capable and do not drift back into legacy speak selection for that tick path.
3. Talk arbitration is essential:
   - While `talk_listening` or `talk_speaking`, suppress event playback on iOS to avoid overlapping coach audio.
4. Phrase ID as source of truth:
   - Backend should send `phrase_id`.
   - iOS uses `phraseId` first; local utterance mapping is fallback only.
5. Manifest coverage tests prevent drift:
   - If phrase IDs are added to catalog/events, active manifest coverage tests catch missing audio-pack updates immediately.

## Locked decisions to remember
1. Wake words in v1 are only `coach` and `coachi`.
2. No `snakk` and no `pt` wake trigger in runtime logic.
3. Wake retrigger cooldown is fixed at 10 seconds.
4. `/coach/talk` `trigger_source` enum is only:
   - `wake_word`
   - `button`
5. Timeout budgets are trigger-specific in the same architecture:
   - wake-word: fast budget
   - button: slightly larger budget
6. No parallel architecture should be introduced for the same behavior.
7. Startup without HR should not speak `hr_signal_lost`; only real connected->disconnected transitions should emit HR-loss notice/cues.
8. Interval warmup end should follow explicit countdown flow (`30/15/5/start`) before main-set zone cues.
9. Interval tick budget must be phase-aware (`warmup/recovery` tighter polling) so countdown windows are not skipped.

## Common pitfalls and how to avoid them
1. Pitfall: adding new phrase IDs without updating active audio pack.
   - Avoid by running manifest coverage tests after every catalog change.
2. Pitfall: local sandbox DNS failures during TTS generation.
   - Use escalated run for outbound API calls when needed.
3. Pitfall: assuming public `r2.dev` URL availability from upload success.
   - Verify with S3 `head_object` plus public URL checks; these are separate concerns.
4. Pitfall: mixed event/legacy speech behavior in one workout.
   - Keep event ownership deterministic and log fallback usage explicitly.

## Continuous improvement runbook (repeatable)
1. Implement feature in existing runtime path only.
2. Add/adjust contract tests first:
   - wake rules
   - talk request/response contract
   - phrase/manifest coverage
3. Update phrase catalog IDs (if needed).
4. Generate/update audio pack artifacts.
5. Run targeted tests.
6. Upload to R2.
7. Verify:
   - R2 object existence via S3 API
   - public URL behavior (if expected to be public)
8. Commit in one coherent change or small reviewable chunks.

## Verification checklist for future sessions
- [ ] `events[]` behavior unchanged in `/coach/continuous`
- [ ] Startup with no HR does **not** emit `hr_signal_lost`
- [ ] Real HR disconnect still emits loss notice once per session
- [ ] Interval warmup emits `interval_countdown_30/15/5/start`
- [ ] `trigger_source` validation still strict
- [ ] wake words unchanged unless explicitly planned
- [ ] talk arbitration still suppresses overlapping event speech
- [ ] `tts_phrase_catalog.py` and active manifest in sync
- [ ] tests passing:
  - `tests_phaseb/test_api_contracts.py`
  - `tests_phaseb/test_talk_to_coach_contract.py`
  - `tests_phaseb/test_wakeword_capture_error_contract.py`
  - `tests_phaseb/test_audio_pack_manifest_coverage.py`

## Known environment note
R2 uploads can succeed while public `r2.dev` reads still return `403` if public access/policy is not enabled. Treat this as a deployment configuration item, not a code failure.

## Next likely improvements (safe sequence)
1. Keep wake ack defaults stable and test candidate acknowledgements via phrase ID promotion, not ad-hoc replacements.
2. Expand deterministic fallback bank quality by phase/zone context before adding any extra runtime complexity.
3. Continue removing legacy fallback dependencies only after explicit coverage proves no regressions in active workout flows.
