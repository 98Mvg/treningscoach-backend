# Coachi StoreKit-first premium policy

Coachi unlocks iOS premium features with **StoreKit first**.

This is the current product rule:

- iOS digital premium unlocks are not driven by Stripe checkout inside the app
- Stripe is reserved for future web billing and account surfaces
- entitlement state is normalized in the product data layer, not inferred directly from payment provider UI

Recommended first entitlement flags:

- `premium_talk_to_coach`
- `premium_extended_history`
- `premium_advanced_analysis`
- `premium_multiple_coaches` later

Source-of-truth rule:

- StoreKit (payment)
- product DB / Supabase (entitlement access)

The current Flask workout runtime remains unchanged by this policy.
