# Session Learnings — Subscription Wiring, Google Auth, Full Project Status

**Date:** 2026-03-13
**Commit:** `8cff2a5` (pushed to main)
**Context:** Merged subscription/monetization stack from `determined-sinoussi` worktree to main. Wired Google Sign-In, StoreKit 2, paywall, talk gating end-to-end.

---

## What Was Done This Session

### 1. StoreKit 2 Subscription System (NEW files on main)

| File | Purpose |
|------|---------|
| `TreningsCoach/Services/SubscriptionManager.swift` | StoreKit 2 manager — product loading, purchase flow, entitlement verification, restore, transaction listener |
| `TreningsCoach/Services/TalkUsageTracker.swift` | Free-tier talk limit enforcement — 1 question/workout, 3/day via UserDefaults with daily reset |
| `TreningsCoach/Views/Tabs/PaywallView.swift` | Paywall screen with 3 contexts: `.liveVoice`, `.talkLimit`, `.general` — includes Free vs Pro comparison, pricing, bilingual copy |

**Product IDs:** `app.coachi.premium.monthly`, `app.coachi.premium.yearly`
**Pricing:** $9.99/month, $79/year, 14-day trial
**Subscription states:** `unknown → free → trial → premium → expired`

### 2. Google Sign-In (real implementation, no SDK)

**`AuthManager.swift`** — replaced stub with real flow:
- Uses `ASWebAuthenticationSession` (built into iOS, no GoogleSignIn SDK dependency)
- Opens Google OAuth consent screen → extracts auth code → exchanges for tokens → sends `id_token` to backend
- Falls back to `markUnsupportedProvider()` if `googleSignInEnabled` flag is off
- `googleSignInEnabled` now reads from Info.plist build config flag (`GOOGLE_SIGN_IN_FEATURE_ENABLED`)
- `googleClientID` reads from Info.plist (`GOOGLE_CLIENT_ID`)

### 3. Feature Gating (wired end-to-end)

| Surface | Gate | Behavior |
|---------|------|----------|
| `WorkoutCompleteView` | `subscriptionManager.isPremium` | Free: shows paywall instead of live coach button |
| `LiveCoachConversationView` | `TalkUsageTracker.canAsk()` + billing flag | Free: shows `LockedCoachCard` when limit reached, remaining questions banner |
| `ProfileView` | `subscriptionManager.status` | Shows "Upgrade to Pro" button (free) or "Coachi Pro Active" badge (premium) |

### 4. Backend `/subscription/validate` Endpoint

**`main.py`** — added POST `/subscription/validate`:
- Protected by `@require_mobile_auth`
- Calls `resolve_user_subscription_tier(user_id)`
- Returns `{"tier": "premium" | "free"}`
- iOS calls this after StoreKit purchase for server-side cross-check

### 5. AuthView Updates

- Added `accountRequiredHint` text and `authBenefitRow` benefit cards (save history, sync profile, Apple/email signup)
- Google button is conditional on feature flag (real flow when enabled, "Coming soon" badge when disabled)
- Added `continueWithoutAccount` button + `signInLaterHint` (auth is optional, users can skip)
- Terms checkbox required before any auth action

### 6. Tests Updated

| Test File | Change |
|-----------|--------|
| `test_ios_auth_provider_contract.py` | Google now has real `sendAuthRequest(provider: "google")` + fallback `markUnsupportedProvider()` |
| `test_ios_auth_refresh_contract.py` | Google flag reads from `googleSignInFeatureEnabled` (not hardcoded false); benefit rows and accountRequiredHint verified present |

**Test results:** 708 passed, 13 failed (all 13 pre-existing, unrelated to this work)

---

## Full Project Status: What's DONE vs What's REMAINING

### Phase 1 — Launch Foundation: ALL DONE (15/15)

| # | Item | Status | Key Files |
|---|------|--------|-----------|
| 1 | Onboarding flow (features, auth, personalization) | DONE | `OnboardingContainerView.swift`, `FeaturesPageView.swift`, `AuthView.swift` |
| 2 | Auth: Apple + Google + passwordless email | DONE | `AuthManager.swift`, `auth_routes.py` |
| 3 | Profile view | DONE | `ProfileView.swift` |
| 4 | Workout complete view | DONE | `WorkoutCompleteView.swift` |
| 5 | Live coach conversation (post-workout) | DONE | `LiveCoachConversationView.swift`, `XAIRealtimeVoiceService.swift` |
| 6 | Watch integration | DONE | `TreningsCoachWatchApp/`, `PhoneWCManager.swift` |
| 7 | Audio pack sync (manifest-driven) | DONE | `AudioPackSyncManager.swift` |
| 8 | Backend API service with auth retry | DONE | `BackendAPIService.swift` |
| 9 | Keychain token storage | DONE | `KeychainHelper.swift` |
| 10 | AuthManager with token bundle | DONE | `AuthManager.swift` |
| 11 | Config with feature flags | DONE | `Config.swift` |
| 12 | L10n bilingual strings (en/no) | DONE | `L10n.swift` (150+ strings) |
| 13 | App Store subscription (StoreKit 2) | DONE | `SubscriptionManager.swift` |
| 14 | Paywall view | DONE | `PaywallView.swift` |
| 15 | Talk usage tracking | DONE | `TalkUsageTracker.swift` |

### Phase 2 — Quality & Polish: 4/9 DONE, 3/9 PARTIAL, 2/9 NOT DONE

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Delete dead code | PARTIAL | Active refactoring ongoing, no dedicated cleanup pass yet |
| 2 | Coach Score gamification (visual ring, XP, streaks) | PARTIAL | Backend `CoachScore` exists, `AppConfig.Progression` thresholds defined, but NO visual XP/streak rings in iOS UI |
| 3 | Workout history persistence | DONE | `WorkoutHistory` model in database.py, `/workouts` POST/GET endpoints, iOS can fetch via BackendAPIService |
| 4 | Analytics/event tracking | PARTIAL | PostHog + Sentry integrated (`launch_integrations.py`), voice telemetry endpoint exists, but not comprehensive workout analytics |
| 5 | Push notifications | NOT DONE | Only localization strings exist, no push notification manager or service |
| 6 | Crash reporting / error monitoring | DONE | Sentry integrated in backend via `launch_integrations.py` |
| 7 | Rate limiting polish | DONE | `RateLimitCounter` model, enforcement functions in main.py, tests passing |
| 8 | Deep linking | PARTIAL | Web routes exist (`/preview/<variant>`), subscription deep links in ProfileView, but no in-app deep link router |
| 9 | App Store listing / screenshots | NOT DONE | No screenshots, marketing assets, or App Store metadata in repo |

### Phase 4 — Monetization: 7/10 DONE, 2/10 PARTIAL, 1/10 NOT DONE

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | StoreKit 2 product config | DONE | Product IDs defined, `SubscriptionManager` loads/purchases/verifies |
| 2 | Receipt validation on backend | PARTIAL | `/subscription/validate` endpoint exists, calls `resolve_user_subscription_tier()`, but full App Store receipt verification not implemented |
| 3 | Subscription tier resolution | DONE | `resolve_user_subscription_tier()` in auth.py, `UserSubscription` model with tier column |
| 4 | Rate limiting by tier | PARTIAL | Backend flags gate features (`BILLING_ENABLED`, etc.), iOS enforces via `TalkUsageTracker`, but backend doesn't differentiate rate limits per tier yet |
| 5 | Feature flags for premium surfaces | DONE | `APP_FREE_MODE`, `BILLING_ENABLED`, `PREMIUM_SURFACES_ENABLED` in config.py, exported via `/app/runtime` |
| 6 | Paywall trigger points | DONE | 3 contexts: live voice (WorkoutCompleteView), talk limit (LiveCoachConversationView), general (ProfileView) |
| 7 | Trial period handling | DONE | `SubscriptionStatus.trial`, detects `offerType == .introductory`, `trialDurationDays=14` |
| 8 | Subscription restore flow | DONE | `restorePurchases()` via `AppStore.sync()`, wired in PaywallView |
| 9 | Cancellation/expiry handling | DONE | `SubscriptionStatus.expired`, expiry check via `expirationDate > Date()`, auto-detected on refresh |
| 10 | App Store Server Notifications webhook | NOT DONE | No webhook handler exists — production subscriptions can't be validated server-side on expiry/cancellation/refund |

---

## What's REMAINING (Prioritized)

### Critical for Launch

1. **App Store Server Notifications webhook** — Without this, the backend can't know when a subscription is cancelled/refunded/expires. Need a `/webhooks/app-store` endpoint that handles Apple's V2 notifications.
2. **App Store Connect configuration** — Product IDs (`app.coachi.premium.monthly`, `app.coachi.premium.yearly`) must be created in App Store Connect with pricing, trial, and review information.
3. **App Store listing** — Screenshots, app description, keywords, privacy policy URL, support URL.

### Important for Quality

4. **Coach Score visual gamification** — Backend score exists but iOS has no visual ring/XP/streak UI component.
5. **Workout history view** — Backend persists workouts but iOS lacks a dedicated history browsing view.
6. **Push notifications** — Workout reminders, streak maintenance, welcome notification.
7. **Dead code cleanup** — Remove stale files, unused imports, worktree remnants.

### Nice to Have

8. **Full receipt validation** — Server-side Apple receipt verification (currently trusts StoreKit 2 client-side verification).
9. **Per-tier rate limiting on backend** — Currently binary (free/premium flag), not tuned limits per tier.
10. **Deep link router** — Universal links for sharing workouts, opening specific screens.
11. **Comprehensive analytics** — Beyond voice telemetry, track workout completion, retention, feature usage.

---

## Architecture Decisions Made This Session

1. **No GoogleSignIn SDK dependency** — Used `ASWebAuthenticationSession` (built into iOS) for Google auth. Simpler build, no CocoaPods/SPM dependency, but requires backend to handle OAuth token exchange.

2. **Cherry-pick over git merge** — The worktree was 1 commit behind main (missing `b42318e` "Refresh onboarding and retire welcome audio"). Cherry-picked subscription-specific changes to avoid merge conflicts in heavily-modified UI files.

3. **Auth is optional** — Added `continueWithoutAccount` flow. Users can skip sign-in during onboarding and use the app with limited features. Sign-in becomes the upgrade path for history persistence and premium.

4. **SubscriptionManager as singleton** — `SubscriptionManager.shared` injected via `.environmentObject()` at app root. All views that need premium gating access it via `@EnvironmentObject`.

5. **TalkUsageTracker uses UserDefaults** — Simple enough for free-tier counting (1 question/workout, 3/day). Resets daily via calendar comparison. Premium users bypass entirely.

---

## Files Changed (Commit 8cff2a5)

**New files (3):**
- `TreningsCoach/Services/SubscriptionManager.swift`
- `TreningsCoach/Services/TalkUsageTracker.swift`
- `TreningsCoach/Views/Tabs/PaywallView.swift`

**Modified iOS (9):**
- `Config.swift` — Added `Subscription` struct, Google auth from build config
- `AuthManager.swift` — Real Google auth via ASWebAuthenticationSession
- `BackendAPIService.swift` — Added `validateSubscription()`
- `TreningsCoachApp.swift` — Injected SubscriptionManager
- `AuthView.swift` — Benefit rows, conditional Google button, continue without account
- `LiveCoachConversationView.swift` — Talk limit gating, LockedCoachCard, remaining banner
- `ProfileView.swift` — Premium section with upgrade/active states
- `WorkoutCompleteView.swift` — Live voice paywall gate
- `FeaturesPageView.swift`, `OnboardingContainerView.swift` — Onboarding updates

**Modified backend (1):**
- `main.py` — `/subscription/validate` endpoint

**Modified tests (4):**
- `test_ios_auth_provider_contract.py` — Google has real flow
- `test_ios_auth_refresh_contract.py` — Google flag from build config
- `test_monitor_management_contract.py`, `test_onboarding_inspo_contract.py`, `test_onboarding_theme_contract.py` — Onboarding updates

---

## Environment Flags Status

| Flag | Current Value | For Launch |
|------|--------------|------------|
| `APP_FREE_MODE` | `true` | Keep `true` — app is free to download |
| `BILLING_ENABLED` | `false` | Flip to `true` when App Store Connect products are live |
| `PREMIUM_SURFACES_ENABLED` | `false` | Flip to `true` when ready to show paywall |

**To activate monetization:** Set `BILLING_ENABLED=true` and `PREMIUM_SURFACES_ENABLED=true` in Render env vars. iOS will start showing paywalls at trigger points.

---

## Validation Commands

```bash
# Backend compile check
python3 -m py_compile main.py config.py brain_router.py brains/*.py

# Test suite
pytest -q tests_phaseb/

# Health check (after deploy)
curl https://treningscoach-backend.onrender.com/health
curl https://treningscoach-backend.onrender.com/brain/health
```
