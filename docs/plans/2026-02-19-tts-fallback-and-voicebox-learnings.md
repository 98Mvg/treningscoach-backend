# 2026-02-19 - TTS Fallback and Voicebox Learnings

## Session objective
- Stop the app/backend from returning mock coach audio.
- Verify whether an open-source "Voicebox" path can replace ElevenLabs.

## Incident summary
- App logs showed successful backend health and welcome response, but audio duration stayed ~0.4s with mock `.wav` files.
- Render logs confirmed ElevenLabs initialized, but generation still fell back to mock.
- Root runtime error on Render:
  - `AttributeError: 'VoiceIntelligence' object has no attribute 'apply_text_rhythm'`

## Root cause
- `main.py` called `voice_intelligence.apply_text_rhythm(...)`.
- Deployed `voice_intelligence.py` did not include that method.
- Result: every TTS call failed before ElevenLabs synthesis and entered mock fallback path.

## Fixes shipped
- Added guard in runtime so text pacing is optional if method is missing (prevents hard failure).
- Added stronger fallback logging and diagnostics around ElevenLabs failures.
- Added retry behavior to attempt base voice before final mock fallback.
- Kept single runtime path (no parallel TTS architecture introduced).

## Commits pushed
- `2fe9925` - Fix ElevenLabs fallback and add CoachScore across web/iOS.
- `6912f23` - Retry ElevenLabs with base voice before mock fallback.
- `424fc18` - Add detailed ElevenLabs error diagnostics before mock fallback.
- `15eab0b` - Guard text pacing method to prevent TTS mock fallback.

## Validation checklist (when mock audio appears)
1. Confirm deployed commit SHA in Render includes the latest TTS fix.
2. Trigger `/welcome` and verify `audio_url` is not `coach_mock_*.wav`.
3. Check Render logs for `[TTS] FAILED` lines and exception type.
4. Confirm logs include ElevenLabs init and active voice source.
5. Re-test one continuous tick (`/coach/continuous`) and inspect `tts_status` fields.

## Voicebox (jamiepine/voicebox) findings
- It is a local/self-hosted voice studio and API based on Qwen3-TTS, not Meta Voicebox.
- Not a drop-in ElevenLabs replacement for this app.
- Language support is currently `zh|en|ja|ko|de|fr|ru|pt|es|it` (no Norwegian).
- Security hardening (auth/rate-limit) is incomplete by default for public exposure.
- Better fit as optional experimental provider for EN/testing, not primary production provider.

## Product decision captured
- Keep ElevenLabs as default production TTS provider.
- If added, gate Voicebox behind config flag (`TTS_PROVIDER=elevenlabs|voicebox`) and start with EN-only scope.

## Preventive guardrails
- Do not assume local uncommitted runtime helpers exist in deploy.
- For runtime-critical methods, either:
  - include explicit method existence checks, or
  - keep API contracts enforced with tests that fail on missing methods.
- Keep root and `backend/` mirrored runtime files synchronized before deploy.
