# Coachi App Store Submission Checklist

Use this when submitting Coachi as a free app with optional Premium monthly/yearly subscriptions.

Companion docs:

- `docs/checklists/app-store-connect-fill-in-template.md`
- `docs/checklists/subscription-sandbox-test-matrix.md`
- `docs/checklists/app-review-notes-template.md`

## Product Truth

1. Confirm Coachi is free to download.
2. Confirm the free core workout flow is usable without payment.
3. Confirm Premium is optional and clearly marked as monthly or yearly Apple subscriptions.
4. Confirm no paywall interrupts an active workout.

## App Store Connect

1. Sign the Paid Apps Agreement.
2. Complete tax information.
3. Complete banking information.
4. Confirm privacy policy URL and App Privacy labels are up to date.
5. Create one subscription group for Coachi Premium.
6. Add the monthly subscription product:
   - product ID: `app.coachi.premium.monthly`
   - duration: `1 month`
7. Add the yearly subscription product:
   - product ID: `app.coachi.premium.yearly`
   - duration: `1 year`
8. Fill in all remaining unknown values from `docs/checklists/app-store-connect-fill-in-template.md`.
9. Submit the first subscriptions together with the app version.

## Reviewer-Visible Paths

1. Confirm reviewers can reach the paywall from a free-user path.
2. Confirm `Restore Purchases` is visible in the app.
3. Confirm `Manage Subscription` is visible in the app.
4. Confirm in-app account deletion is visible in settings.
5. Confirm the app can still be used in free core mode without purchase.

## Pre-Submission Testing

1. Run the full matrix in `docs/checklists/subscription-sandbox-test-matrix.md`.
2. Test monthly purchase in Sandbox.
3. Test yearly purchase in Sandbox.
4. Test restore purchases in Sandbox.
5. Test the same flows in TestFlight.
6. Confirm entitlement refresh after purchase and after restore.
7. Confirm the reviewer-facing instructions in `docs/checklists/app-review-notes-template.md` match the current build number, version, and final premium naming.

## Go / No-Go

Only submit when all of these are true:

1. Free users can complete a core workout without paying.
2. Premium users can buy monthly or yearly and unlock premium surfaces immediately.
3. `Restore Purchases` and `Manage Subscription` both work on device.
4. In-app `Delete account` works from settings.
5. Review notes, privacy policy URL, support URL, and screenshots are filled in.
6. The values in App Store Connect match the product IDs in `TreningsCoach/TreningsCoach/Config.swift`.
