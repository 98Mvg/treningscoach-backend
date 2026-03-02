# 2026-02-17 — Personality System Learnings

## What we standardized
- Personality tone is now stable across experience levels (`beginner`, `intermediate`, `advanced`).
- Experience level no longer changes prompt tone or periodic coaching cadence.
- Beginner-only runtime safety guardrail is retained (`beginner_guardrail`) to avoid aggressive push language in risky moments.

## Prompt architecture (current)
- Continuous path uses:
  - `coach_personality.py` (base coach + realtime constraints)
  - `brains/base_brain.py` (shared persona directives across providers)
  - provider overlays (currently strongest in `grok_brain.py`)
- Conversational path uses:
  - `persona_manager.py` (`PersonaManager.get_system_prompt(...)`)

## Critical personality rules now enforced
- `personal_trainer` = strict but safe, process-first, no hype, no sarcasm.
- Humor is light/rare and disabled during distress/safety override.
- Safety always overrides intensity goals.
- Example lines are references, not fixed scripts.
- Model should occasionally generate fresh short phrasing in the same tone.
- Avoid back-to-back identical cue repetition.

## Norwegian quality guidance
- Keep Norwegian cues in proper Bokmål (`æ/ø/å`).
- Preserve high-quality reference lines for `personal_trainer` under “Hvordan coachen kan snakke (referanser)”.
- Do not force exact line reuse every tick; maintain style while varying wording.

## Fast-check list before future changes
1. Verify both root + `backend/` mirrors are updated for touched runtime files.
2. Run prompt tests:
   - `tests_phaseb/test_base_brain_normalization.py`
   - `tests_phaseb/test_persona_prompt_injection.py`
   - `tests_phaseb/test_grok_persona_prompting.py`
   - `tests_phaseb/test_persona_manager_prompt_consistency.py`
   - `tests_phaseb/test_training_level_runtime_consistency.py`
3. Confirm docs stay aligned:
   - `docs/PERSONALITY_PROMPT_BEHAVIOR.md`

## Collaboration preference to remember
- Keep guidance beginner-friendly and safe-by-default.
- Explain changes in plain language first, then code/commands.
- Favor simplest reliable solution and include clear next steps.

## 2026-02-17 Additional Troubleshooting Learnings

### Brain routing and availability
- Default routing is now Grok-first with immediate config fallback:
  - `BRAIN_PRIORITY=grok,config`
  - `USE_PRIORITY_ROUTING=true`
- This avoids Gemini/OpenAI/Claude usage by default when credits are unavailable.
- Verify active routing quickly via:
  - backend logs (`brain_provider`, `brain_source`, `brain_status`)
  - `/brain/health`

### Latency-aware behavior quality
- Continuous coaching now uses a two-step latency strategy:
  1. Fast fallback cue now (config) when model latency trend is high.
  2. Forced richer cue on next tick.
- Tuning knobs in `config.py`:
  - `LATENCY_FAST_FALLBACK_ENABLED`
  - `LATENCY_FAST_FALLBACK_THRESHOLD_SECONDS`
  - `LATENCY_FAST_FALLBACK_MIN_CALLS`
  - `LATENCY_FAST_FALLBACK_COOLDOWN_SECONDS`
- Debug fields returned from `/coach/continuous`:
  - `latency_fast_fallback_used`
  - `latency_rich_followup_forced`
  - `latency_pending_rich_followup`

### Norwegian quality system
- Native-quality rewrite layer is now centralized in:
  - `norwegian_phrase_quality.py` (and `backend/` mirror)
- Session-editable banlist is now supported:
  - `norwegian_phrase_banlist.json`
  - `backend/norwegian_phrase_banlist.json`
- Format:
  - `{"exact_rewrites": {"bad phrase": "better phrase"}}`
- After each workout session, append awkward lines to banlist first, then promote stable rewrites into `config.py` banks.

### Tone and voice learnings
- `personal_trainer` can be slightly more assertive without becoming mean.
- Norwegian phrasing tuned toward direct, natural Bokmål (avoid literal translations).
- Voice consistency/darkness improved by persona TTS tuning:
  - Higher `stability`
  - Higher `similarity_boost`
  - Moderate `style`
- ElevenLabs adapter now reads `similarity_boost` from persona config.

### High-signal checks before declaring a fix
1. Confirm root and `backend/` files are synced for all touched runtime modules.
2. Run:
   - `pytest -q tests_phaseb`
   - `python3 -m py_compile main.py brain_router.py config.py session_manager.py norwegian_phrase_quality.py elevenlabs_tts.py`
3. Re-test with real workout logs and verify:
   - Grok usage appears (`brain=grok/ai/success`) when expected.
   - No repeated awkward Norwegian lines.
   - No warmup wording in intense phase.
