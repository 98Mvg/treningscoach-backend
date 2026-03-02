# Session Takeaways (Behavior Quality)

Date: 2026-02-15
Scope: language consistency, silence policy, latency, wake-word loop stability.

## Working Rules To Reuse

1. Keep a single runtime path.
- Production runs from `main.py` (Flask/Gunicorn). Avoid parallel logic paths.
- Keep root and `backend/` mirror files in sync after backend edits.

2. Language consistency is enforced at 3 layers.
- Normalize language at ingress (`welcome`, `/coach/continuous`, `/coach/talk`).
- Use locale-aware fallbacks in all brains/router.
- Apply a final output guard before TTS to prevent drift responses.

3. Normalize intensity keys everywhere.
- Canonical key is `intensity` with normalized values (`calm/moderate/intense/critical`).
- Legacy/localized aliases (`intensitet`, `moderat`, `kritisk`, etc.) must map to canonical values.

4. Silence policy must be session-scoped.
- Never use global silence counters for workout behavior decisions.
- Use per-session counters and clear on session end.

5. Wake-word restart loops must be bounded.
- Use exponential backoff, max attempts per window, and temporary degraded mode.
- Emit diagnostics for retries/degraded events for troubleshooting.

6. Latency tuning must be evidence-driven.
- Log stage timings per tick: analyze_ms, decision_ms, brain_ms, tts_ms, total_ms.
- Tune behavior only with observed timing data.

## Test Checklist To Reuse

- `pytest -q tests_phaseb`
- `python3 -m py_compile` on changed backend/root Python files
- If Swift touched: run `xcodebuild` when simulator/runtime is available

## Known Environment Caveat

- In this environment, iOS simulator availability can block `xcodebuild` destination tests.
- Treat this as environment limitation, not app logic failure.

