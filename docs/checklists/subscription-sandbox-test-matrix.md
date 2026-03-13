# Coachi Subscription Sandbox And TestFlight Test Matrix

Use this on a real iPhone build before App Store submission.

## Setup

- Install the build you plan to submit.
- Use a Sandbox Apple account for purchase tests.
- Use the same product IDs as `TreningsCoach/TreningsCoach/Config.swift`:
  - `app.coachi.premium.monthly`
  - `app.coachi.premium.yearly`

## Free Core Flow

1. Launch app as a guest user.
2. Start a core workout without buying Premium.
3. Finish the workout.
4. Confirm the free core experience works and no paywall interrupts the active workout.

Expected result:
- workout start works
- workout completes
- premium upsell may appear after workout, but not during workout

## Paywall Visibility

1. Open the paywall from a free-user path.
2. Confirm both plans are visible.
3. Confirm `Restore Purchases` is visible.
4. Confirm `Manage Subscription` is visible.

Expected result:
- monthly and yearly plans both render
- restore and manage actions are one tap away

## Monthly Purchase

1. Purchase monthly Premium.
2. Return to the app.
3. Confirm premium state updates.
4. Confirm a premium-only surface unlocks.

Expected result:
- purchase succeeds
- entitlement updates without reinstall
- premium-only surface is now available

## Yearly Purchase

1. On a clean test account or reset state, purchase yearly Premium.
2. Return to the app.
3. Confirm premium state updates.

Expected result:
- yearly purchase succeeds
- yearly plan is treated as premium entitlement

## Restore Purchases

1. Reinstall app or sign in on a clean device state.
2. Open paywall or settings.
3. Tap `Restore Purchases`.

Expected result:
- previous premium entitlement returns
- no duplicate purchase required

## Manage Subscription

1. Tap `Manage Subscription`.

Expected result:
- system opens Apple subscription management

## Delete Account

1. While signed in, open settings.
2. Delete account in-app.
3. Restart app.

Expected result:
- account is removed from Coachi
- app returns to guest/free mode
- note: any Apple subscription still has to be cancelled in App Store

## TestFlight Repeat

Repeat these on the TestFlight build:

1. Free core flow
2. Monthly purchase
3. Yearly purchase
4. Restore Purchases
5. Manage Subscription

Mark pass/fail for the release build:

- Free core flow: `[PASS/FAIL]`
- Monthly purchase: `[PASS/FAIL]`
- Yearly purchase: `[PASS/FAIL]`
- Restore Purchases: `[PASS/FAIL]`
- Manage Subscription: `[PASS/FAIL]`
- Delete account: `[PASS/FAIL]`
