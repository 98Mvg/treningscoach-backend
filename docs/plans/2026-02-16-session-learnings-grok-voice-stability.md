# Session Learnings (Optimization + Faster Process)

Date: 2026-02-16  
Scope: Grok quality, iOS audio stability, wake-word reliability, faster debugging loop.

## What We Learned

1. Grok was active but output quality felt generic because realtime prompting did not strongly encode persona.
- Fix implemented: persona-aware prompt shaping in Grok realtime/chat paths (`personal_trainer` vs `toxic_mode`) plus training-level hints and anti-repeat instruction.
- Files: `brains/grok_brain.py`, `backend/brains/grok_brain.py`.

2. iOS crash root cause was tap lifecycle after engine start failure.
- Symptom: `AUIOClient_StartIO failed (1852797029)` then `CreateRecordingTap: (nullptr == Tap())`.
- Fix implemented: centralized teardown, tap state tracking, cleanup on start failure, and bounded start retry.
- File: `TreningsCoach/TreningsCoach/Services/ContinuousRecordingManager.swift`.

3. Wake-word + talk-button had a race that caused recognition thrash.
- Symptom: repeated `No speech detected`, exponential restarts, degraded mode loops.
- Fix implemented: block parallel capture flows, cancel pending restart tasks before button capture, treat idle no-speech as low-severity restart (not escalating error-retry path).
- Files: `TreningsCoach/TreningsCoach/Services/WakeWordManager.swift`, `TreningsCoach/TreningsCoach/ViewModels/WorkoutViewModel.swift`.

4. Silent coaching ticks should skip expensive AI generation.
- Kept: system silent-policy path with short debug text and no TTS.
- Benefit: lower latency + lower token cost when coach should stay quiet.

## Fast Triage Playbook (Reuse Every Session)

1. Confirm backend route health first.
- Check app log: `✅ Backend connected: healthy`.
- Check Render log: service bound to port and `/health` responsive.

2. Confirm which brain actually generated text.
- Use app diagnostic line: `brain=<provider>/<source>/<status>`.
- If not `grok/ai/success`, inspect fallback reason before changing prompts.

3. For speech issues, separate the two channels:
- Wake-word channel (always-on passive listen).
- Button capture channel (active short capture).
- Ensure they are not running capture simultaneously.

4. Treat `No speech detected` as expected idle noise unless user is actively speaking.
- Escalate only for persistent failures during confirmed speech input.

5. For startup audio failures:
- If `AUIOClient_StartIO failed`, verify teardown + retry behavior before touching routing/LLM code.

## Logging That Gives Maximum Signal

Keep these logs visible in one test run:
- iOS:
  - `Tap callback` + `MIC_ACTIVE`
  - `WAKEWORD_DETECTED`
  - `Capture session started`
  - `SPEECH_ERROR` + `RESTART/DEGRADED`
  - `Backend response ... brain=...`
- Render:
  - `Continuous coaching tick` context (lang/persona/phase)
  - `[BRAIN] <provider> | latency=... | success=...`
  - `Tick timing ... analyze_ms/decision_ms/brain_ms/tts_ms/total_ms`

## Process Optimizations To Keep

1. Always patch the single runtime path first.
- Avoid parallel architecture or duplicate code paths.

2. For backend edits, keep root + `backend/` mirror synchronized immediately.
- Prevent deploy drift and false negatives in production verification.

3. Add small focused tests for behavior changes.
- Persona prompting tests and router timeout tests were fast and high-signal.

4. Ship isolated commits by concern.
- Audio engine lifecycle fix.
- Grok quality/prompting fix.
- Wake-word capture stability fix.

## Suggested Next Optimization Targets

1. Add explicit speech-state telemetry counters exposed in diagnostics UI:
- `no_speech_events`, `capture_success_rate`, `restart_rate_per_min`.

2. Add backend error body propagation for `/coach/continuous` failures:
- Replace iOS-side `Unknown error` with backend reason + trace id.

3. Tune wake-word idle restart interval from observed sessions.
- Current low-severity restart delay is conservative; can be tuned from real usage.
