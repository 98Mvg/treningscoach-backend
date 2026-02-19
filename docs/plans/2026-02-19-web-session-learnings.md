# Web Session Learnings - 2026-02-19

## Scope covered
- Built and deployed the codex web variant as the primary public landing page.
- Added EN/NO page-level language switching with persistence.
- Added V2 image-driven UI polish and wired runtime API calls to Render.

## What worked
- Keeping one runtime path (`main.py` + `templates/index_codex.html`) avoided duplicate website logic.
- Mirroring template/static changes to both root and `backend/` paths prevented deployment drift.
- A single i18n dictionary for static and dynamic UI text made language behavior predictable.
- Render base URL helper for API calls made local preview + production behavior consistent.

## Key failure modes observed
- Render showed old UI until code was actually committed and pushed to `main`.
- Root route (`/`) can still serve older variant if default is not explicitly set to `codex`.
- Env/config mismatch (e.g., `WEB_UI_VARIANT`) can override template expectations.
- External URL checks from sandbox can fail due to DNS/network restrictions; local smoke tests are required fallback.

## Decisions to keep
- Default web variant should remain `codex` unless intentionally changed.
- Keep `WEB_VARIANT_TEMPLATES` with explicit safe fallback to `codex`.
- Keep EN/NO switch synchronized with `demoLanguage` so backend calls match visible language.
- Keep static website assets under `/static/site/images` (and mirrored in `backend/static/site/images`).

## Deployment checklist (Render)
1. Confirm latest GitHub commit is deployed (commit SHA in Render Deploys).
2. Confirm `WEB_UI_VARIANT=codex` (or unset if config default is `codex`).
3. If stale output persists: `Clear build cache & deploy`.
4. Verify:
   - `/` returns `X-Web-Variant: codex`
   - source contains `coachi_site_lang`
   - source contains `/static/site/images/v2-hero-ui.png`

## Quality checklist for next polish pass
- Replace placeholder store links with final App Store/Google Play URLs when available.
- Add true partner logos (licensed assets) instead of text pills.
- Add performance budget for hero image weight and responsive image variants.
- Add E2E smoke checks for: language toggle, waitlist submit, live demo endpoint health.

## Regression guardrails
- Do not create a parallel website architecture.
- Keep edits in the existing template/runtime path.
- Run at least:
  - `python3 -m py_compile main.py backend/main.py config.py backend/config.py`
  - Flask test-client check for `/preview/codex` and root `/` variant header.
