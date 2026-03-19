from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUBSCRIPTION_MANAGER = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "SubscriptionManager.swift"
PAYWALL = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "PaywallView.swift"
PROFILE = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "ProfileView.swift"
ONBOARDING = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Onboarding" / "OnboardingContainerView.swift"
CONFIG = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Config.swift"


def test_subscription_manager_exposes_manage_subscription_path():
    content = SUBSCRIPTION_MANAGER.read_text()
    config = CONFIG.read_text()
    assert "enum SubscriptionPurchaseOutcome: Equatable" in content
    assert "case success(SubscriptionStatus)" in content
    assert "case pending" in content
    assert "case userCancelled" in content
    assert "case failed" in content
    assert "func manageSubscription()" in content
    assert "https://apps.apple.com/account/subscriptions" in content
    assert "UIApplication.shared.open(url)" in content
    assert "enum SubscriptionBillingOption" in content
    assert "@discardableResult" in content
    assert "func purchase(_ product: Product) async -> SubscriptionPurchaseOutcome" in content
    assert "let refreshedStatus = status" in content
    assert "return .success(refreshedStatus)" in content
    assert "@Published private(set) var hasLoadedProducts = false" in content
    assert "var monthlyHasIntroOffer: Bool" in content
    assert "var yearlyHasIntroOffer: Bool" in content
    assert "func formattedPrice(for option: SubscriptionBillingOption, isNorwegian: Bool) -> String" in content
    assert "func formattedRecurringPrice(for option: SubscriptionBillingOption, isNorwegian: Bool) -> String" in content
    assert "func formattedFreePrice(isNorwegian: Bool) -> String" in content
    assert "func formattedYearlyPerMonthPrice(isNorwegian: Bool) -> String" in content
    assert 'formatter.locale = Locale(identifier: isNorwegian ? "nb_NO" : "en_US")' in content
    assert "formatter.minimumFractionDigits = 0" in content
    assert "formatter.maximumFractionDigits = 2" in content
    assert 'return "\\(formattedAmount) kr"' in content
    assert 'return "$\\(formattedAmount)"' in content
    assert "fallbackMonthlyPriceUSD" in config
    assert "fallbackMonthlyPriceNOK" in config
    assert "fallbackYearlyPriceUSD" in config
    assert "fallbackYearlyPriceNOK" in config


def test_paywall_exposes_restore_and_manage_subscription_buttons():
    content = PAYWALL.read_text()
    assert "enum PaywallPlanSelectionOption" in content
    assert "init(context: PaywallContext, initialPlan: PaywallPlanSelectionOption = .yearly)" in content
    assert '"Restore Purchases"' in content
    assert '"Choose subscription"' in content
    assert '"Keep Talking with Your Coach"' in content
    assert '"Your 30-second free coaching preview has ended.' in content
    assert '"Start \\(AppConfig.Subscription.trialDurationDays)-day free trial now"' in content
    assert 'AppConfig.LiveVoice.premiumMaxDurationSeconds / 60' in content
    assert 'AppConfig.LiveVoice.premiumSessionsPerDay' in content
    assert "unlimited daily sessions" not in content
    assert '"Yearly plan"' in content
    assert '"Monthly plan"' in content
    assert ".safeAreaInset(edge: .bottom)" in content
    assert "bottomActionSection" in content
    assert "subscriptionManager.restorePurchases()" in content
    assert '"https://coachi.no/terms"' in content
    assert '"https://coachi.no/privacy"' in content
    assert ".background(CoachiTheme.backgroundGradient.ignoresSafeArea())" in content
    assert ".fill(CoachiTheme.bg.opacity(0.94))" in content
    assert 'Color(hex: "F7F7FB")' not in content
    assert "subscriptionManager.monthlyHasIntroOffer" in content
    assert "subscriptionManager.yearlyHasIntroOffer" in content
    assert "subscriptionManager.formattedRecurringPrice(for: .monthly, isNorwegian: isNorwegian)" in content
    assert "subscriptionManager.formattedPrice(for: .yearly, isNorwegian: isNorwegian)" in content
    assert "subscriptionManager.formattedYearlyPerMonthPrice(isNorwegian: isNorwegian)" in content


def test_profile_premium_section_exposes_reviewer_visible_subscription_actions():
    content = PROFILE.read_text()
    onboarding = ONBOARDING.read_text()
    assert "ManageSubscriptionView(isManageSubscriptionPresented: $isManageSubscriptionPresented)" in content
    assert "showManageSubscription = true" in content
    assert "struct ManageSubscriptionFeatureRowData: Identifiable" not in content
    assert "enum SubscriptionComparisonCatalog {" not in content
    assert "struct ManageSubscriptionFeatureRowData: Identifiable" in onboarding
    assert "enum SubscriptionComparisonCatalog {" in onboarding
    assert "title: L10n.manageSubscription" in content
    assert 'Text(isNorwegian ? "Mine inkluderte elementer" : "My included items")' not in content
    assert 'Text(isNorwegian ? "Inkludert i abonnementet" : "Included in your plan")' not in content
    assert 'Text(isNorwegian ? "Min plan" : "My plan")' not in content
    assert "Text(localizedPlanStatus)" not in content
    assert "private var subscriptionStatusCard: some View" not in content
    assert "private var includedItemsCard: some View" not in content
    assert '(isNorwegian ? "Administrer i App Store" : "Manage in App Store")' in content
    assert '(isNorwegian ? "Gjenopprett kjøp" : "Restore purchases")' in content
    assert '(isNorwegian ? "Se alle tilbudene" : "See all offers")' not in content
    assert "@State private var showPlanOffers = false" not in content
    assert ".fullScreenCover(isPresented: $showPlanOffers)" not in content
    assert "WatchConnectedPremiumOfferStepView(" in content
    assert "presentationMode: .manageSubscriptionInline" in content
    assert ".frame(height: inlinePlanDeckHeight)" in content
    assert "min(max(UIScreen.main.bounds.height * 0.86, 760), 920)" in content
    assert "Continue to your Premium Dashboard" not in content
    assert '.frame(maxWidth: 320)' in content
    assert '.background(Color(hex: "22C55E"))' in content
    assert 'Button(isNorwegian ? "Brukervilkår" : "Terms")' in content
    assert 'Button(isNorwegian ? "personvernerklæring" : "privacy policy")' in content
    assert 'title: isNorwegian ? "Guidede økter" : "Guided workouts"' in onboarding
    assert 'title: isNorwegian ? "Coaching ved å analysere puls" : "Coaching by analysing puls"' in onboarding
    assert 'title: isNorwegian ? "Talk to Coach Live" : "Talk to Coach Live"' in onboarding
    assert 'title: isNorwegian ? "Tilbakemelding etter hver økt" : "Single session feedback"' in onboarding
    assert 'title: isNorwegian ? "Dype øktoppsummeringer" : "Deep workout insights"' in onboarding
    assert 'title: isNorwegian ? "Husker tidligere økter" : "Remembers past workouts"' in onboarding
    assert 'title: isNorwegian ? "Velg coach-stemme (kommer snart)" : "Choose coach voice (coming soon)"' in onboarding
    assert 'freeValue: isNorwegian ? "5 dagers økthistorikk" : "5 days workout history"' in onboarding
    assert 'premiumValue: isNorwegian ? "Full økthistorikk" : "Full workout history"' in onboarding
    assert 'Color(hex: "2F7BFF")' in onboarding
    assert '@State private var purchaseSuccessState: PremiumAccessSuccessState?' in onboarding
    assert 'private enum PremiumAccessSuccessState: String, Identifiable' in onboarding
    assert '.fullScreenCover(item: $purchaseSuccessState)' in onboarding
    assert 'Continue to your Premium Dashboard' in onboarding
    assert '"Your \\(trialDays)-day Coachi PREMIUM trial is now active!"' in onboarding
    assert 'You are now a Coachi PREMIUM user!' in onboarding
    assert "subscriptionManager.formattedFreePrice" in onboarding
    assert "subscriptionManager.formattedPrice(for: .monthly, isNorwegian: isNorwegian)" in onboarding
    assert "subscriptionManager.formattedPrice(for: .yearly, isNorwegian: isNorwegian)" in onboarding
