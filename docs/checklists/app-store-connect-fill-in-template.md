# Coachi App Store Connect Fill-In Template

Use this as the concrete worksheet before you start filling fields in App Store Connect.

## App Record

- App name: `Coachi AI`
- Bundle ID: `com.coachi.app`
- SKU: `coachi-ios-001`
- Primary language: `Norwegian (Bokmål)` (recommended default)
- Support URL: `https://coachi.no/support`
- Marketing URL: `https://coachi.no`
- Privacy policy URL: `https://coachi.no/privacy`
- Version to submit: `3.0`
- Build number to submit: `[FILL IN]`

## Product Truth

- App is free to download: `Yes`
- Free core workout flow usable without payment: `Yes`
- Premium optional: `Yes`
- Premium billing model: `Auto-renewable subscription`
- Subscription group count: `1`

## Subscription Group

- Group reference name: `Coachi Premium`
- Review screenshot ready: `[YES/NO]`
- Localized group display text ready: `[YES/NO]`

## Monthly Premium Product

- Product ID: `app.coachi.premium.monthly`
- Suggested reference name: `Coachi Premium Monthly`
- Duration: `1 month`
- Display name: `Coachi Premium Monthly`
- Description: `Unlock live coach conversations, higher usage limits, and other premium Coachi features.`
- Price tier: `[FILL IN]`
- Intro offer / free trial: `14-day free trial`

## Yearly Premium Product

- Product ID: `app.coachi.premium.yearly`
- Suggested reference name: `Coachi Premium Yearly`
- Duration: `1 year`
- Display name: `Coachi Premium Yearly`
- Description: `Unlock live coach conversations, higher usage limits, and other premium Coachi features.`
- Price tier: `[FILL IN]`
- Intro offer / free trial: `14-day free trial`

## Review Package

- Review notes pasted from `docs/checklists/app-review-notes-template.md`: `[YES/NO]`
- Screenshots uploaded: `[YES/NO]`
- App Privacy labels reviewed: `[YES/NO]`
- Paid Apps Agreement signed: `[YES/NO]`
- Tax complete: `[YES/NO]`
- Banking complete: `[YES/NO]`

## Sandbox / TestFlight

- Sandbox tester account email: `[FILL IN]`
- TestFlight build tested: `[FILL IN]`
- Monthly purchase verified: `[YES/NO]`
- Yearly purchase verified: `[YES/NO]`
- Restore verified: `[YES/NO]`
- Manage Subscription verified: `[YES/NO]`
- Free core workout verified without purchase: `[YES/NO]`
- Delete account verified: `[YES/NO]`

## Final Submission Gate

Do not submit until these match repo truth:

1. Product IDs match `TreningsCoach/TreningsCoach/Config.swift`
2. Premium is monthly/yearly only
3. free core workout flow remains available without payment
4. Review notes mention both free use and premium upsell
