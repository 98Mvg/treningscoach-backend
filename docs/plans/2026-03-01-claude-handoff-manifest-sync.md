# Claude Handoff (2026-03-01) — Manifest Sync Learnings Integrated

This note is for Claude Code so it can continue without losing context.

## What Codex just did

Codex integrated the manifest-sync audio-pack learnings into the project's persistent learnings surface.

Primary source-of-truth document:
- [`2026-03-01-manifest-sync-audio-pack-learnings.md`](/Users/mariusgaarder/Documents/treningscoach/docs/plans/2026-03-01-manifest-sync-audio-pack-learnings.md)

Cross-links and guardrails added:
- [`CLAUDE.md`](/Users/mariusgaarder/Documents/treningscoach/CLAUDE.md)  
  Added "0.2 Latest Session Learnings (2026-03-01) — Manifest Sync Audio Pack".
- [`tasks/lessons.md`](/Users/mariusgaarder/Documents/treningscoach/tasks/lessons.md)  
  Added explicit execution guardrails for manifest-sync behavior.
- [`2026-02-27-session-learnings-r2-audio-pack-execution.md`](/Users/mariusgaarder/Documents/treningscoach/docs/plans/2026-02-27-session-learnings-r2-audio-pack-execution.md)  
  Added follow-up pointer to the 2026-03-01 doc as latest authority.

## Non-negotiable rules Claude must preserve

1. `manifest.json` + `latest.json` are the source of truth for local audio pack state.
2. Always verify SHA256:
- manifest bytes hash for change detection
- per-file hash before persisting downloaded MP3s
3. Never delete stale audio files during active workout.
4. Keep version-isolated local audio-pack directories.
5. Keep dynamic pack version resolution in app runtime (sync manager first, config fallback second).
6. Keep persona safety boundaries (no toxic/performance audio bleed into personal trainer path).

## Operational intent

This was a learnings/documentation integration step, not a feature rewrite.  
If Claude changes audio-pack sync logic later, it must update the 2026-03-01 manifest-sync learnings doc in the same PR.
