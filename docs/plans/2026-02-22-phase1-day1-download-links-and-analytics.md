# 2026-02-22 - Phase 1 (Day 1) Download Funnel Links + Landing Analytics Cleanup

## Scope shipped

- Added env-driven app store URLs for launch pages (App Store + Google Play + Android early access).
- Wired launch template CTA buttons to those URLs (with safe fallback anchors in local/dev).
- Added click tracking for store/early-access CTA events from the launch page.
- Removed legacy demo analytics events from backend allowlist to match "no web demo" launch direction.
- Kept root/backend runtime files synced.

## Files changed

- `main.py`
- `backend/main.py`
- `templates/index_launch.html`
- `backend/templates/index_launch.html`
- `.env.example`
- `backend/.env.example`
- `tests_phaseb/test_api_contracts.py`

## Runtime behavior

- New env variables:
  - `APP_STORE_URL`
  - `GOOGLE_PLAY_URL`
  - `ANDROID_EARLY_ACCESS_URL`
- New landing analytics event allowlist:
  - `waitlist_signup`
  - `app_store_click`
  - `google_play_click`
  - `android_early_access_click`
- Legacy demo events are rejected by `/analytics/event`.

## Verification

- Compile:
  - `python3 -m py_compile main.py backend/main.py`
- Tests:
  - `pytest -q tests_phaseb/test_api_contracts.py tests_phaseb/test_waitlist_persistence.py`
  - Result: `10 passed`

## Notes

- Existing UTC-naive timestamp warnings (`datetime.utcnow()`) remain and are unchanged by this slice.
- Existing root/backend mirror still exists; this change keeps both paths in sync to avoid drift.
