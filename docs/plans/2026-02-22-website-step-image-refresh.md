# 2026-02-22 - Website Step Image Refresh

## Change

- Updated launch website step 1 image ("Velg økt" / "Pick your run") to use provided asset.
- Kept step 2 and step 3 images unchanged.
- Synced root + backend template/static copies.

## Files

- `templates/index_launch.html`
- `backend/templates/index_launch.html`
- `static/site/images/step-choose-workout.png`
- `backend/static/site/images/step-choose-workout.png`

## Asset source

- `.claude/worktrees/elegant-bardeen/marketing/assets/website/hero-workout.png`

## Verification

- Rendered `/` via Flask test client and confirmed:
  - `X-Web-Variant: launch`
  - HTML contains `/static/site/images/step-choose-workout.png`
