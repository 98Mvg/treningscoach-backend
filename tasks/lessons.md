# Lessons / Execution Guardrails

Updated: 2026-02-23

## Workflow Orchestration

1. Plan-first for non-trivial work.
- Use checkable steps.
- Re-plan immediately if the path is failing.

2. Keep main context clean.
- Do targeted exploration before edits.
- Parallelize independent reads/checks.

3. Self-improvement loop.
- After corrections, write the lesson here.
- Turn repeated mistakes into explicit guardrails.

4. Verification before done.
- Do not mark complete without proof.
- Validate with build/tests/logs relevant to touched code.

5. Elegance, balanced.
- Ask if there is a simpler and more robust fix.
- Avoid over-engineering small fixes.

6. Autonomous bug-fixing behavior.
- When a bug is reported, investigate logs/errors/tests first.
- Fix root cause with minimal impact.

## Core Principles

- Simplicity first.
- No temporary patching when a clean fix is possible.
- Minimal impact: touch only what is necessary.

## Session-Specific Lessons

- 2026-02-23: Guard all runtime UI numeric inputs (`NaN`/`Inf`) before CoreGraphics/SwiftUI drawing.
- 2026-02-23: Keep coach persona contract strict: persona changes tone only, never event logic/cooldowns/scoring.
- 2026-02-23: For Phase 3 requests, derive `hrQuality` from current signal quality + watch/source state, not watch connection alone.
