# Session Learnings (2026-02-22): UI Gesture Stability + Web Free-Mode

## What changed
- Workout screen gesture contract tightened:
  - Main circle long-press to end workout now requires 2.0s hold (lower accidental stop risk).
  - Mic long-press now uses a high-priority 1.5s gesture and reliably opens diagnostics.
  - Mic long-press opens directly on `Pulse` tab to expose HR/Watch sensor controls faster.
- Workout center icon readability improved with a darker circular backing.
- Launch page image references moved to Flask `url_for('static', ...)` for robust asset resolution.
- Launch page copy updated to match product policy:
  - Free now while quality is being perfected.
  - Paid plans can come later.
  - Removed explicit premium price language from FAQ.
- Backend modularization started without behavior changes:
  - Extracted web/landing/runtime endpoints from `main.py` into `web_routes.py` blueprint.
  - Kept root `main.py` as runtime source of truth and registered blueprint there.
  - Added `backend/web_routes.py` as compatibility wrapper to avoid root/backend drift.
- Backend modularization continued without behavior changes:
  - Extracted brain/chat endpoints from `main.py` into `chat_routes.py` blueprint.
  - Registered `chat_routes` blueprint from root `main.py`.
  - Added `backend/chat_routes.py` compatibility wrapper.
  - Added route-contract tests to ensure `/brain/*` and `/chat/*` paths remain stable.
- App inspo onboarding alignment (`nr 1` + `nr 2`) added in iOS flow:
  - New account step in onboarding sequence (Apple/Google quick actions + email registration form UI).
  - Setup profile step now captures first + last name (`Om deg`) and keeps beginner auto-leveling.
  - Onboarding sequence is now: Welcome -> Language -> Features -> Account -> Setup.
- App inspo onboarding alignment (`nr 3`) added in iOS flow:
  - New CoachScore intro step after setup for "one-number" explanation.
  - Uses simple score card with short factors (zone hold, consistency, recovery).
  - Onboarding sequence is now: Welcome -> Language -> Features -> Account -> Setup -> CoachScore Intro.
- App inspo onboarding alignment (`nr 4`) added in iOS flow:
  - New sensor connection step after CoachScore intro.
  - User gets explicit choice: connect watch now or continue without watch.
  - Onboarding sequence is now: Welcome -> Language -> Features -> Account -> Setup -> CoachScore Intro -> Sensor Connect.

## Validation
- `pytest` (targeted contracts) passed:
  - `tests_phaseb/test_workout_ui_gesture_contract.py`
  - `tests_phaseb/test_launch_page_assets.py`
  - `tests_phaseb/test_launch_page_copy_contract.py`
  - `tests_phaseb/test_config_env_overrides.py`
  - `tests_phaseb/test_api_contracts.py`
- iOS build passed with `xcodebuild` (Debug, generic iOS destination).

## Roadmap status snapshot
- Phase 1 (Voice + NO/EN experience): in progress, stable enough to continue UI/onboarding polish.
- Phase 2 (Event motor deterministic behavior): core in place, keep hardening guardrails and tests.
- Phase 3 (Sensor layer Watch HR/cadence + fallback): in progress, diagnostics/pulse panel path now clearer.
- Phase 4 (LLM as language layer only): pending hard boundary reinforcement in runtime contracts.
- Phase 5 (Personalization): baseline started, needs iterative tuning from real sessions.
- Phase 6 (Workout mode expansion): deferred until running/interval loop is consistently stable.
