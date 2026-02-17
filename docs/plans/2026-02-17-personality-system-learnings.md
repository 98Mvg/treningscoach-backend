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
