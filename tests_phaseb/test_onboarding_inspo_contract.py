from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ONBOARDING_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "OnboardingContainerView.swift"
)
INTRO_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "FeaturesPageView.swift"
)
APP_VIEW_MODEL = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "ViewModels"
    / "AppViewModel.swift"
)


def _onboarding_text() -> str:
    return ONBOARDING_VIEW.read_text(encoding="utf-8")


def _intro_text() -> str:
    return INTRO_VIEW.read_text(encoding="utf-8")


def _app_viewmodel_text() -> str:
    return APP_VIEW_MODEL.read_text(encoding="utf-8")


def test_onboarding_includes_full_profile_and_hr_steps() -> None:
    text = _onboarding_text()
    guided_block = text.split("private var guidedOnboardingSteps: [OnboardingStep] {", 1)[1].split("private var showsGuidedProgress", 1)[0]
    assert "case birthAndGender" in text
    assert "case bodyMetrics" in text
    assert "case maxHeartRate" in text
    assert "case restingHeartRate" in text
    assert "case enduranceHabits" in text
    assert "case frequencyAndDuration" in text
    assert "case summary" in text
    assert "case result" in text
    assert "case noSensorFallback" in text
    assert "case premiumOffer" in text
    assert "case notificationPermission" in text
    assert "OnboardingFlowProgressView(" in text
    assert "Step \\(current) of \\(total)" in text
    assert ".identity," not in guided_block
    assert ".features," not in guided_block
    assert ".birthAndGender," in guided_block
    assert ".notificationPermission," in guided_block
    assert ".dataPurpose," not in guided_block
    assert "steps.insert(.frequencyAndDuration, at: 5)" in guided_block
    assert "steps.insert(.premiumOffer, at: steps.count - 1)" in guided_block
    assert "if formState.doesEnduranceTraining" in guided_block


def test_post_auth_explainer_starts_with_personalized_hello_page() -> None:
    text = _intro_text()
    post_auth_block = text.split("private func postAuthPages(displayName: String) -> [IntroStoryPage] {", 1)[1].split("private var showcasePrimaryTitle", 1)[0]
    assert "let greeting = displayName.isEmpty" in text
    assert 'titleNo: greeting' in post_auth_block
    assert 'bodyNo: "La meg først forklare hvordan vi kan hjelpe deg."' in post_auth_block
    assert post_auth_block.count('bodyNo: ""') == 4
    assert 'imageName: "IntroStory1"' in post_auth_block
    assert post_auth_block.count("IntroStoryPage(") == 5
    assert 'titleNo: "Jeg guider deg live med pulssoner"' in post_auth_block
    assert 'titleNo: "Jeg motiverer og tilpasser økten dynamisk"' in post_auth_block
    assert 'titleNo: "Du får en CoachScore etter hver økt"' in post_auth_block
    assert 'titleNo: "Etter økten kan vi snakke live"' in post_auth_block
    # Welcome uses .intro (bg-image carousel, 6s auto-advance)
    welcome_block = _onboarding_text().split("case .welcome:", 1)[1].split("case .language:", 1)[0]
    assert "mode: .intro" in welcome_block
    # Features uses .postAuthExplainer after identity
    assert 'case postAuthExplainer(displayName: String)' in text


def test_onboarding_routes_to_profile_completion_path() -> None:
    text = _onboarding_text()
    assert "@State private var authMode: AuthFlowMode = .register" in text
    assert "primaryTitle: L10n.register" in text
    assert 'secondaryTitle: L10n.current == .no ? "Jeg har allerede en bruker" : "I already have an account"' in text
    assert "authMode = .register" in text
    assert "authMode = .login" in text
    assert "move(to: .language)" in text
    assert "AuthView(mode: authMode)" in text
    assert "authManager.currentUser?.resolvedDisplayName ?? \"\"" in text
    assert "move(to: .identity)" in text
    assert "} onContinueWithoutAccount: {" in text
    assert "onBack: { move(to: .auth) }" in text
    assert "onContinue: { dismissKeyboardAndMove(to: .features) }" in text
    assert "onSecondary: { move(to: .identity) }" in text
    assert "onPrimary: { move(to: .birthAndGender) }" in text
    assert "onBack: { move(to: .features) }" in text
    assert "onContinue: { move(to: nextStepAfterEnduranceHabits) }" in text
    assert "private var nextStepAfterEnduranceHabits: OnboardingStep" in text
    assert "private var summaryBackStep: OnboardingStep" in text
    assert "onContinue: { move(to: .sensorConnect) }" in text
    assert "onBack: { move(to: summaryBackStep) }" in text
    assert "onContinue: { watchConnected in" in text
    assert "if !subscriptionManager.hasPremiumAccess {" in text
    assert "notificationBackStep = .premiumOffer" in text
    assert "move(to: .premiumOffer)" in text
    assert "notificationBackStep = .sensorConnect" in text
    assert "move(to: .notificationPermission)" in text
    assert "case .dataPurpose:" not in text
    assert "let profileDraft = formState.toDraft(" in text
    assert "appViewModel.completeOnboarding(profile: profileDraft)" in text


def test_watch_connected_onboarding_offer_reuses_existing_paywall_path() -> None:
    text = _onboarding_text()
    plan_card_block = text.split("private func planCard(for plan: PlanSelection, availableHeight: CGFloat, compactLayout: Bool, topInset: CGFloat, bottomInset: CGFloat) -> some View {", 1)[1].split("private func planFeatures", 1)[0]
    assert "struct WatchConnectedPremiumOfferStepView: View" in text
    assert "enum PresentationMode {" in text
    assert "case onboardingStep" in text
    assert "case manageSubscriptionInline" in text
    assert "watchManager: PhoneWCManager.shared" in text
    assert 'isNorwegian ? "Velg plan" : "Choose plan"' in text
    assert 'private enum PlanSelection: Int, CaseIterable' in text
    assert 'selectedPlan: PlanSelection = .free' in text
    assert 'selectedTrialPlan: PaywallPlanSelectionOption = .yearly' in text
    assert 'case trial' in text
    assert '@State private var autoAdvanceTask: Task<Void, Never>?' in text
    assert '@State private var isPagerInteracting = false' in text
    assert '@State private var isAdvancingAutomatically = false' in text
    assert '@State private var purchaseSuccessState: PremiumAccessSuccessState?' in text
    assert 'let presentationMode: PresentationMode' in text
    assert 'presentationMode: PresentationMode = .onboardingStep' in text
    assert 'private var showsOnboardingChrome: Bool { presentationMode == .onboardingStep }' in text
    assert 'private var showsCurrentPlanState: Bool { presentationMode == .manageSubscriptionInline }' in text
    assert 'private var selectsPremiumOnAppear: Bool { presentationMode == .onboardingStep }' in text
    assert 'private var autoAdvanceIntervalSeconds: UInt64?' in text
    assert "12" in text
    assert "Task { await subscriptionManager.loadProducts() }" in text
    assert "syncSelectedTrialPlanToEligibility()" in text
    assert 'if let resolvedLabelPlan = resolvedPlanSelection(from: subscriptionManager.resolvedPlanLabel)' in text
    assert 'private func resolvedPlanSelection(from label: String) -> PlanSelection? {' in text
    assert 'case "Free Trial":' in text
    assert 'case "Premium":' in text
    assert 'case "Free", "Expired", "Checking":' in text
    assert 'try? await Task.sleep(nanoseconds: intervalSeconds * 1_000_000_000)' in text
    assert 'let layoutWidth = min(min(renderWidth, deviceWidth), 500)' in text
    assert 'let contentWidth = max(0.0, layoutWidth - (contentSideInset * 2))' in text
    assert 'let compactLayout = layoutWidth < 390 || renderHeight < 780' in text
    assert 'let availablePagerHeight = max(380.0, renderHeight - safeTop - safeBottom - headerAndFooterHeight)' in text
    assert 'TabView(selection: $selectedPlan)' in text
    assert '.tabViewStyle(.page(indexDisplayMode: .never))' in text
    assert '.simultaneousGesture(pagerInteractionGesture)' in text
    assert '.frame(width: cardWidth, height: pageHeight, alignment: .leading)' in text
    assert 'planPager(' in text
    assert '.frame(width: contentWidth, height: availablePagerHeight)' in text
    assert '.frame(height: 630)' not in text
    assert 'DragGesture(minimumDistance: 24)' not in text
    assert 'DragGesture(minimumDistance: 10)' in text
    assert 'Text(isNorwegian ? "Sveip mellom Gratis, Premium og 14 dagers gratis prøveperiode" : "Swipe between Free, Premium, and a 14-day free trial")' in text
    assert 'planBackground(for: selectedPlan)' in text
    assert '.ignoresSafeArea()' in text
    assert 'return isNorwegian\n                        ? "Begrensede samtaler med coach"\n                        : "Limited conversations with coach"' in text
    assert 'return isNorwegian\n                    ? "Fullverdige samtaler med coach"\n                    : "Full conversations with coach"' in text
    assert 'title: isNorwegian ? "Coaching ved å analysere puls" : "Coaching by analysing puls"' in text
    assert 'freeValue: isNorwegian ? "5 dagers økthistorikk" : "5 days workout history"' in text
    assert 'premiumValue: isNorwegian ? "Full økthistorikk" : "Full workout history"' in text
    assert 'title: isNorwegian ? "Tilbakemelding etter hver økt" : "Single session feedback"' in text
    assert 'title: isNorwegian ? "Husker tidligere økter" : "Remembers past workouts"' in text
    assert 'title: isNorwegian ? "Velg coach-stemme (kommer snart)" : "Choose coach voice (coming soon)"' in text
    assert 'if row.id == "workout_history" {' in text
    assert 'return plan == .free ? row.freeValue : row.premiumValue' in text
    assert 'return isNorwegian ? "Fortsett med Gratis" : "Continue with Free"' in text
    assert 'return isNorwegian ? "Få Premium" : "Get Premium"' in text
    assert 'return isNorwegian ? "Start \\(trialDays) dagers gratis prøveperiode nå" : "Start \\(trialDays) days free trail now"' in text
    assert 'Color(hex: "2F7BFF")' in text
    assert 'if showsCurrentPlanState {' in text
    assert 'return isNorwegian ? "Gratis plan" : "Free plan"' in text
    assert 'case .premium:\n                return isNorwegian ? "Få Premium" : "Get Premium"' in text
    assert 'case .trial:\n                return isNorwegian ? "Start \\(trialDays) dagers gratis prøveperiode nå" : "Start \\(trialDays) days free trail now"' in text
    assert 'return isNorwegian ? "Administrer i App Store" : "Manage in App Store"' not in text
    assert 'private func planSummary(for plan: PlanSelection) -> String {' in text
    assert 'Start med Coachi-kjernene og oppgrader når du vil.' in text
    assert 'Lås opp hele Coachi-opplevelsen med mer innsikt, historikk og live coaching.' in text
    assert 'Prøv hele Coachi gratis i 14 dager med samme enkle oversikt som de andre planene.' in text
    assert 'ForEach(PlanSelection.allCases, id: \\.rawValue)' in text
    assert 'trialPricingOption(' in text
    assert 'private var trialEligibleOptions: [PaywallPlanSelectionOption]' in text
    assert 'if subscriptionManager.monthlyHasIntroOffer {' in text
    assert 'if subscriptionManager.yearlyHasIntroOffer {' in text
    assert 'if !subscriptionManager.hasLoadedProducts {' in text
    assert 'Gratis prøveperiode er ikke tilgjengelig akkurat nå.' in text
    assert 'Text(isNorwegian ? "Pris etter prøvetid" : "Pricing after trial")' not in text
    assert 'if !isInlineManageSubscription, trialEligibleOptions.contains(.yearly), let savingsText = yearlySavingsText {' in text
    assert "return ScrollView(.vertical, showsIndicators: false)" not in plan_card_block
    assert "Spacer(minLength: denseLayout ? 4 : 12)" in plan_card_block
    assert 'let isCurrentPlan = showsCurrentPlanState && plan == resolvedCurrentPlan' in plan_card_block
    assert 'let contentSpacing: CGFloat = denseLayout ? 12 : 18' in plan_card_block
    assert 'let featureSpacing: CGFloat = denseLayout ? 10 : 14' in plan_card_block
    assert 'let footerSpacing: CGFloat = denseLayout ? 6 : 10' in plan_card_block
    assert 'Alle Coachi-funksjoner er inkludert i prøveperioden. Kjøpet fullføres i App Store.' in text
    assert 'let headerHeight: CGFloat = {' in plan_card_block
    assert 'case .trial:' in plan_card_block
    assert 'planCardHeader(for: plan, accent: accent, isCurrentPlan: isCurrentPlan, height: headerHeight)' in plan_card_block
    assert '.overlay(alignment: .top)' not in plan_card_block
    assert '.disabled(isActionDisabled)' in plan_card_block
    assert 'headerBackground(for: plan, accent: accent)' in text
    assert 'if plan == .premium && !hasPremiumAccess && !isCurrentPlan {' in text
    assert '@State private var selectedTrialPlan: PaywallPlanSelectionOption = .yearly' in text
    assert '@State private var showPaywall' not in text
    assert 'paywallInitialPlan' not in text
    assert 'PaywallView(context: .general, initialPlan: paywallInitialPlan)' not in text
    assert 'Task { await purchaseSelection(.yearly) }' in text
    assert 'Task { await purchaseSelection(selectedTrialPlan) }' in text
    assert 'let purchaseOutcome = await subscriptionManager.purchase(product)' in text
    assert 'guard case let .success(status) = purchaseOutcome else { return }' in text
    assert 'purchaseSuccessState = successState' in text
    assert 'private enum PremiumAccessSuccessState: String, Identifiable' in text
    assert '.fullScreenCover(item: $purchaseSuccessState)' in text
    assert 'premiumSuccessScreen(for: state)' in text
    assert 'Continue to your Premium Dashboard' in text
    assert '"Your \\(trialDays)-day Coachi PREMIUM trial is now active!"' in text
    assert 'You are now a Coachi PREMIUM user!' in text
    assert 'Thank you for choosing the best. Prepare to unlock new heights!' in text
    assert 'Unparalleled Insights:' in text
    assert 'Personal Coaching:' in text
    assert 'Precision HR Zones:' in text
    assert "subscriptionManager.formattedFreePrice(isNorwegian: isNorwegian)" in text
    assert "subscriptionManager.formattedPrice(for: .monthly, isNorwegian: isNorwegian)" in text
    assert "subscriptionManager.formattedPrice(for: .yearly, isNorwegian: isNorwegian)" in text
    assert 'Text(isNorwegian ? "Apple Watch koblet til" : "Apple Watch connected")' in text
    assert 'title: isNorwegian ? "Klokken er klar" : "Your watch is ready"' not in text
    assert "private func dismissKeyboardAndMove(to step: OnboardingStep)" in text
    assert "syncSelectionForCurrentContext(animated: false)" in text


def test_app_viewmodel_persists_backend_relevant_profile_keys() -> None:
    text = _app_viewmodel_text()
    assert "func completeOnboarding(profile: OnboardingProfileDraft)" in text
    assert "func completeOnboardingForReturningUser(displayName: String, languageCode: String)" in text
    assert 'defaults.string(forKey: "user_first_name")' in text
    assert 'defaults.string(forKey: "user_last_name")' in text
    assert 'defaults.string(forKey: "user_display_name")' in text
    assert "let preferredDisplayName = [storedCombinedName, storedDisplayName, incomingDisplayName]" in text
    assert 'defaults.set(preferredDisplayName, forKey: "user_display_name")' in text
    assert 'defaults.set(profile.hrMax, forKey: "hr_max")' in text
    assert 'defaults.set(profile.restingHR, forKey: "resting_hr")' in text
    assert 'defaults.set(profile.age, forKey: "user_age")' in text
    assert 'defaults.set(profile.trainingLevel, forKey: "training_level")' in text
    assert 'defaults.set(profile.languageCode, forKey: "app_language")' in text


def test_app_viewmodel_retains_onboarding_optional_future_keys() -> None:
    text = _app_viewmodel_text()
    assert 'defaults.set(profile.heightCm, forKey: "user_height_cm")' in text
    assert 'defaults.set(profile.weightKg, forKey: "user_weight_kg")' in text
    assert 'defaults.set(profile.gender, forKey: "user_gender")' in text
    assert 'defaults.set(profile.notificationsOptIn, forKey: "notifications_opt_in")' in text


def test_reset_onboarding_clears_profile_and_hr_defaults() -> None:
    text = _app_viewmodel_text()
    assert 'keysToClear = [' in text
    assert '"hr_max"' in text
    assert '"resting_hr"' in text
    assert '"user_age"' in text
    assert 'keysToClear.forEach { defaults.removeObject(forKey: $0) }' in text


def test_onboarding_explains_hr_endurance_and_intensity_in_coachi_copy() -> None:
    text = _onboarding_text()
    assert "Makspuls er det høyeste antallet hjerteslag per minutt du kan nå under hard trening." in text
    assert "Max HR is the highest number of heart beats per minute your heart can reach during intense exercise." in text
    assert "Hvilepuls er hvor mange ganger hjertet ditt slår per minutt når du er avslappet og ikke trener." in text
    assert "Resting HR is how many times your heart beats per minute when you are relaxed and not exercising." in text
    assert "Hva er utholdenhetstrening?" in text
    assert "✅ 🏃 Løping" in text
    assert "✅ 🚶 Gåturer" in text
    assert "✅ 🚴 Sykling" in text
    assert "✅ 🏊 Svømming" in text
    assert "✅ 💃 Dansing" in text
    assert "✅ 🤸 Aerobic" in text
    assert "❌ 🧘 Yoga" in text
    assert "❌ 🏋️ Styrketrening" in text
    assert "❌ 🙆 Pilates" in text
    assert "Du blir bare lett andpusten og kan holde samme tempo lenge uten problemer." in text
    assert "Du puster raskere og kjenner at du jobber, men du har fortsatt kontroll og kan holde på en god stund." in text
    assert "Du blir tydelig andpusten, må jobbe hardt og klarer bare å holde intensiteten i korte drag." in text
    assert "Tap any value if you want to update it before continuing." in text
    assert "onEditField: { field in" in text
    assert "move(to: field.targetStep(doesEnduranceTraining: formState.doesEnduranceTraining))" in text
