//
//  PaywallView.swift
//  TreningsCoach
//
//  Phase 4 conversion screen.
//  Shown when a free user reaches a usage limit or taps a premium feature.
//  Uses SubscriptionManager for StoreKit 2 purchases.
//
//  Trigger contexts:
//    .liveVoice  – user taps "Talk to Coach Live" without premium
//    .talkLimit  – user has used their free text questions
//    .general    – generic premium upsell
//

import StoreKit
import SwiftUI

// MARK: - Paywall Analytics (best-effort, fire-and-forget)
private func trackPaywallEvent(_ event: String, context: String, metadata: [String: Any] = [:]) {
    var meta = metadata
    meta["context"] = context
    Task {
        _ = await BackendAPIService.shared.trackAnalyticsEvent(event: event, metadata: meta)
    }
}

// MARK: - Context

enum PaywallContext: Identifiable {
    case liveVoice
    case talkLimit
    case general

    var headline: String {
        switch self {
        case .liveVoice: return "Keep Talking with Your Coach"
        case .talkLimit: return "Continue the Conversation"
        case .general:   return "Your Personal AI Coach"
        }
    }

    var headlineNo: String {
        switch self {
        case .liveVoice: return "Fortsett med coachen din live"
        case .talkLimit: return "Fortsett samtalen"
        case .general:   return "Din personlige AI-coach"
        }
    }

    var contextHint: String? {
        switch self {
        case .liveVoice: return "Your 30-second free coaching preview has ended. Upgrade for up to \(AppConfig.LiveVoice.premiumMaxDurationSeconds / 60)-minute live sessions, \(AppConfig.LiveVoice.premiumSessionsPerDay) sessions per day, and deeper workout insights."
        case .talkLimit: return "You've used your free coach question for this workout. Upgrade to keep the conversation going."
        case .general:   return nil
        }
    }

    var contextHintNo: String? {
        switch self {
        case .liveVoice: return "Den gratis 30-sekunders coach-previewen er ferdig. Oppgrader for opptil \(AppConfig.LiveVoice.premiumMaxDurationSeconds / 60) minutter per liveøkt, \(AppConfig.LiveVoice.premiumSessionsPerDay) samtaler per dag og dypere treningsinnsikt."
        case .talkLimit: return "Du har brukt det gratis coach-spørsmålet ditt for denne økten. Oppgrader for å fortsette samtalen."
        case .general:   return nil
        }
    }

    var id: String {
        switch self {
        case .liveVoice: return "live_voice"
        case .talkLimit: return "talk_limit"
        case .general: return "general"
        }
    }

    static func fromDeepLinkValue(_ value: String) -> PaywallContext {
        switch value {
        case "live_voice":
            return .liveVoice
        case "talk_limit":
            return .talkLimit
        default:
            return .general
        }
    }
}

enum PaywallPlanSelectionOption {
    case monthly
    case yearly
}

// MARK: - View

struct PaywallView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    @EnvironmentObject private var authManager: AuthManager
    @EnvironmentObject private var subscriptionManager: SubscriptionManager

    let context: PaywallContext
    @State private var selectedPlan: PaywallPlanSelectionOption
    @State private var showPurchaseAuthSheet = false
    @State private var pendingPurchaseOption: PaywallPlanSelectionOption?

    private var isNorwegian: Bool { L10n.current == .no }
    private var hasPremiumAccess: Bool {
        subscriptionManager.hasPremiumAccess
    }
    private var termsURL: URL? { URL(string: "https://coachi.no/terms") }
    private var privacyURL: URL? { URL(string: "https://coachi.no/privacy") }

    init(context: PaywallContext, initialPlan: PaywallPlanSelectionOption = .yearly) {
        self.context = context
        _selectedPlan = State(initialValue: initialPlan)
    }

    // MARK: - Body

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 20) {
                    topBar
                    if let hint = isNorwegian ? context.contextHintNo : context.contextHint {
                        Text(hint)
                            .font(.system(size: 15, weight: .regular))
                            .foregroundStyle(CoachiTheme.textSecondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 8)
                    }

                    planCard(option: .monthly)
                    planCard(option: .yearly)
                }
                .padding(.horizontal, 22)
                .padding(.top, 14)
                .padding(.bottom, 220)
            }
            .background(CoachiTheme.backgroundGradient.ignoresSafeArea())
            .navigationBarHidden(true)
            .safeAreaInset(edge: .bottom) {
                bottomActionSection
            }
        }
        .interactiveDismissDisabled(subscriptionManager.isLoading)
        .sheet(isPresented: $showPurchaseAuthSheet) {
            AuthView(
                mode: .login,
                onContinue: {
                    showPurchaseAuthSheet = false
                    resumePendingPurchaseIfNeeded()
                },
                onContinueWithoutAccount: {
                    showPurchaseAuthSheet = false
                    pendingPurchaseOption = nil
                }
            )
            .environmentObject(authManager)
        }
        .onAppear {
            trackPaywallEvent("paywall_shown", context: contextKey)
        }
    }

    private var contextKey: String {
        switch context {
        case .liveVoice: return "live_voice"
        case .talkLimit: return "talk_limit"
        case .general:   return "general"
        }
    }

    private var topBar: some View {
        HStack(spacing: 12) {
            Button {
                trackPaywallEvent("paywall_dismissed", context: contextKey)
                dismiss()
            } label: {
                Image(systemName: "chevron.left")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundColor(CoachiTheme.textPrimary)
                    .frame(width: 34, height: 34)
            }
            .buttonStyle(.plain)

            Text(isNorwegian ? "Velg abonnement" : "Choose subscription")
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(CoachiTheme.textPrimary)

            Spacer()
        }
        .padding(.top, 6)
    }

    private func planCard(option: PaywallPlanSelectionOption) -> some View {
        let isSelected = selectedPlan == option
        let isYearly = option == .yearly
        let priceLabel = isYearly ? yearlyPriceLabel : monthlyPriceLabel
        let name = isYearly
            ? (isNorwegian ? "Årsabonnement" : "Yearly plan")
            : (isNorwegian ? "Månedsabonnement" : "Monthly plan")
        let subtitle = isNorwegian ? "Kun deg" : "Just you"
        let trialText = planTrialText(for: option)
        let detailText = isYearly ? yearlySubtitle : (isNorwegian ? "Betal måned for måned" : "Pay month to month")

        return Button {
            selectedPlan = option
        } label: {
            VStack(alignment: .leading, spacing: 0) {
                if isYearly {
                    HStack {
                        Text(isNorwegian ? "Populær" : "Popular")
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(.white)
                        Spacer()
                        if isSelected {
                            Image(systemName: "checkmark")
                                .font(.system(size: 18, weight: .bold))
                                .foregroundColor(.white)
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
                    .background(Color(hex: "A78BFA"))
                }

                HStack(alignment: .top, spacing: 12) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(name)
                            .font(.system(size: 19, weight: .semibold))
                            .foregroundColor(CoachiTheme.textPrimary)
                        Text(subtitle)
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                        Text(trialText)
                            .font(.system(size: 15, weight: .regular))
                            .foregroundColor(CoachiTheme.textSecondary)
                        Text(detailText)
                            .font(.system(size: 15, weight: .medium))
                            .foregroundColor(CoachiTheme.primary)
                    }

                    Spacer()

                    VStack(alignment: .trailing, spacing: 6) {
                        Text(priceLabel)
                            .font(.system(size: 19, weight: .bold))
                            .foregroundColor(CoachiTheme.textPrimary)
                        if isSelected && !isYearly {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 20, weight: .semibold))
                                .foregroundColor(Color(hex: "5B4FD1"))
                        }
                    }
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 18)
            }
            .background(
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(CoachiTheme.surface)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .stroke(
                        isSelected ? Color(hex: "A78BFA") : CoachiTheme.borderSubtle.opacity(0.28),
                        lineWidth: isSelected ? 3 : 1
                    )
            )
            .shadow(color: CoachiTheme.textPrimary.opacity(0.08), radius: 18, x: 0, y: 10)
        }
        .buttonStyle(.plain)
    }

    private var callToActionButton: some View {
        Button {
            trackPaywallEvent(
                "paywall_cta_tapped",
                context: contextKey,
                metadata: ["plan": selectedPlan == .yearly ? "yearly" : "monthly"]
            )
            startPurchaseFlow(for: selectedPlan)
        } label: {
            Text(primaryCTAString)
                .font(.system(size: 19, weight: .bold))
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 18)
                .background(
                    Capsule(style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [Color(hex: "7C3AED"), Color(hex: "4F46E5")],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                )
        }
        .buttonStyle(.plain)
        .disabled(subscriptionManager.isLoading || selectedProduct == nil)
        .opacity(subscriptionManager.isLoading || selectedProduct == nil ? 0.65 : 1.0)
        .overlay(alignment: .center) {
            if subscriptionManager.isLoading {
                ProgressView()
                    .tint(.white)
            }
        }
    }

    private var restoreButton: some View {
        Button(isNorwegian ? "Gjenopprett kjøp" : "Restore Purchases") {
            trackPaywallEvent("paywall_restore_tapped", context: contextKey)
            Task { await subscriptionManager.restorePurchases() }
        }
        .font(.system(size: 16, weight: .bold))
        .foregroundColor(CoachiTheme.primary)
    }

    private var termsAndPrivacyFooter: some View {
        HStack(spacing: 8) {
            Button {
                guard let termsURL else { return }
                openURL(termsURL)
            } label: {
                Text(isNorwegian ? "Brukervilkår" : "Terms")
            }
            .buttonStyle(.plain)

            Text(isNorwegian ? "og" : "and")
                .foregroundColor(CoachiTheme.textSecondary)

            Button {
                guard let privacyURL else { return }
                openURL(privacyURL)
            } label: {
                Text(isNorwegian ? "personvernerklæring" : "privacy policy")
            }
            .buttonStyle(.plain)
        }
        .font(.system(size: 14, weight: .semibold))
        .foregroundColor(CoachiTheme.textPrimary)
    }

    private var bottomActionSection: some View {
        VStack(spacing: 14) {
            callToActionButton
            restoreButton
            termsAndPrivacyFooter
        }
        .padding(.horizontal, 22)
        .padding(.top, 18)
        .padding(.bottom, 16)
        .background(
            ZStack {
                Rectangle()
                    .fill(CoachiTheme.bg.opacity(0.94))
                    .ignoresSafeArea(edges: .bottom)

                Rectangle()
                    .fill(CoachiTheme.borderSubtle.opacity(0.32))
                    .frame(height: 1)
                    .frame(maxHeight: .infinity, alignment: .top)
            }
            .shadow(color: CoachiTheme.textPrimary.opacity(0.06), radius: 10, x: 0, y: -4)
        )
    }

    private var selectedProduct: Product? {
        switch selectedPlan {
        case .monthly:
            return subscriptionManager.monthlyProduct
        case .yearly:
            return subscriptionManager.yearlyProduct
        }
    }

    private var primaryCTAString: String {
        if planHasTrial(selectedPlan) {
            return isNorwegian
                ? "Start \(AppConfig.Subscription.trialDurationDays) dagers gratis prøveperiode nå"
                : "Start \(AppConfig.Subscription.trialDurationDays)-day free trial now"
        }
        return isNorwegian ? "Fortsett" : "Continue"
    }

    private func planHasTrial(_ option: PaywallPlanSelectionOption) -> Bool {
        switch option {
        case .monthly:
            return subscriptionManager.monthlyHasIntroOffer
        case .yearly:
            return subscriptionManager.yearlyHasIntroOffer
        }
    }

    private func planTrialText(for option: PaywallPlanSelectionOption) -> String {
        if planHasTrial(option) {
            return isNorwegian
                ? "Gratis prøveperiode \(AppConfig.Subscription.trialDurationDays) dager"
                : "Free trial \(AppConfig.Subscription.trialDurationDays) days"
        }
        return isNorwegian ? "Ingen gratis prøveperiode" : "No free trial"
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(spacing: 16) {
            // Icon
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [Color(hex: "A5F3EC").opacity(0.22), Color(hex: "67E8F9").opacity(0.12)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 88, height: 88)
                Image(systemName: "mic.fill")
                    .font(.system(size: 36, weight: .semibold))
                    .foregroundStyle(Color(hex: "A5F3EC"))
            }
            .padding(.top, 32)

            Text(isNorwegian ? context.headlineNo : context.headline)
                .font(.system(size: 30, weight: .bold))
                .foregroundStyle(Color.white.opacity(0.97))
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)

            if let hint = isNorwegian ? context.contextHintNo : context.contextHint {
                Text(hint)
                    .font(.system(size: 15, weight: .regular))
                    .foregroundStyle(Color.white.opacity(0.70))
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(.bottom, 32)
    }

    // MARK: - Bullets

    private struct BulletItem {
        let icon: String
        let en: String
        let no: String
    }

    private let bullets: [BulletItem] = [
        BulletItem(icon: "mic.badge.plus",    en: "Unlimited coach questions",          no: "Ubegrenset med coach-spørsmål"),
        BulletItem(icon: "waveform",          en: "Live voice coaching after workouts", no: "Live stemme-coaching etter øktene"),
        BulletItem(icon: "chart.line.uptrend.xyaxis", en: "Deep workout insights",     no: "Dyp analyse av øktene dine"),
        BulletItem(icon: "person.wave.2.fill", en: "Multiple coach personalities",     no: "Flere coach-personligheter"),
        BulletItem(icon: "clock.arrow.circlepath", en: "Full training history",        no: "Full treningshistorikk"),
    ]

    private var bulletSection: some View {
        VStack(spacing: 12) {
            ForEach(bullets, id: \.en) { item in
                HStack(spacing: 14) {
                    ZStack {
                        RoundedRectangle(cornerRadius: 10, style: .continuous)
                            .fill(Color(hex: "A5F3EC").opacity(0.14))
                            .frame(width: 40, height: 40)
                        Image(systemName: item.icon)
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundStyle(Color(hex: "A5F3EC"))
                    }
                    Text(isNorwegian ? item.no : item.en)
                        .font(.system(size: 16, weight: .medium))
                        .foregroundStyle(Color.white.opacity(0.92))
                    Spacer()
                    Image(systemName: "checkmark")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundStyle(Color(hex: "A5F3EC"))
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .fill(Color.white.opacity(0.05))
                )
            }
        }
        .padding(.bottom, 28)
    }

    // MARK: - Comparison Table

    private var comparisonSection: some View {
        VStack(spacing: 0) {
            // Header row
            HStack(spacing: 0) {
                Text(isNorwegian ? "Funksjon" : "Feature")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(Color.white.opacity(0.50))
                    .frame(maxWidth: .infinity, alignment: .leading)
                Text(isNorwegian ? "Gratis" : "Free")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(Color.white.opacity(0.50))
                    .frame(width: 66, alignment: .center)
                Text("Pro")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(Color(hex: "A5F3EC"))
                    .frame(width: 66, alignment: .center)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(Color.white.opacity(0.04))
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous).inset(by: 0).path(in: CGRect(x: 0, y: 0, width: 1000, height: 44)))

            // Rows
            let rows: [(String, String, String, String)] = [
                (isNorwegian ? "Løpecoaching" : "Core coaching",        "✓", "✓", ""),
                (isNorwegian ? "Pulssone-analyse" : "HR zone coaching", "✓", "✓", ""),
                (isNorwegian ? "Coach Score" : "Coaching Score",        "✓", "✓", ""),
                (isNorwegian ? "Økt-historikk" : "Workout history",     isNorwegian ? "10 øk." : "10 wkt.", isNorwegian ? "Alle" : "All", ""),
                (isNorwegian ? "Coach-spørsmål" : "Coach questions",    isNorwegian ? "1/økt" : "1/wkt.", isNorwegian ? "Ubegr." : "Unlim.", ""),
                (isNorwegian ? "Live voice" : "Live voice",             "—", "✓", "premium"),
                (isNorwegian ? "Avansert analyse" : "Deep analytics",   "—", "✓", "premium"),
            ]

            ForEach(Array(rows.enumerated()), id: \.offset) { index, row in
                HStack(spacing: 0) {
                    Text(row.0)
                        .font(.system(size: 14, weight: .regular))
                        .foregroundStyle(Color.white.opacity(0.84))
                        .frame(maxWidth: .infinity, alignment: .leading)
                    Text(row.1)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundStyle(Color.white.opacity(0.55))
                        .frame(width: 66, alignment: .center)
                    Text(row.2)
                        .font(.system(size: 13, weight: row.3 == "premium" ? .bold : .medium))
                        .foregroundStyle(row.3 == "premium" ? Color(hex: "A5F3EC") : Color.white.opacity(0.84))
                        .frame(width: 66, alignment: .center)
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 11)
                .background(index % 2 == 0 ? Color.clear : Color.white.opacity(0.025))
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(Color.white.opacity(0.10), lineWidth: 1)
        )
        .padding(.bottom, 28)
    }

    // MARK: - Pricing

    private var pricingSection: some View {
        VStack(spacing: 12) {
            if hasPremiumAccess {
                currentPlanCard
            }

            // Yearly (recommended)
            yearlyButton
            // Monthly
            monthlyButton

            if let errorMessage = subscriptionManager.errorMessage {
                Text(errorMessage)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundStyle(Color.red.opacity(0.85))
                    .multilineTextAlignment(.center)
            }
        }
        .padding(.bottom, 16)
    }

    private var currentPlanCard: some View {
        HStack(spacing: 12) {
            Image(systemName: "checkmark.seal.fill")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(Color(hex: "A5F3EC"))

            VStack(alignment: .leading, spacing: 3) {
                Text(isNorwegian ? "Planen din er aktiv" : "Your plan is active")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(Color.white.opacity(0.92))
                Text(subscriptionManager.resolvedPlanLabel)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(Color.white.opacity(0.72))
            }

            Spacer()
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 14)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(Color.white.opacity(0.06))
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(Color(hex: "A5F3EC").opacity(0.20), lineWidth: 1)
                )
        )
    }

    private var hasIntroOffer: Bool {
        subscriptionManager.yearlyProduct?.subscription?.introductoryOffer != nil
    }

    private var yearlyButton: some View {
        Button {
            trackPaywallEvent("paywall_cta_tapped", context: contextKey, metadata: ["plan": "yearly", "has_trial": hasIntroOffer])
            startPurchaseFlow(for: .yearly)
        } label: {
            ZStack(alignment: .topTrailing) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(yearlyPrimaryLabel)
                            .font(.system(size: 16, weight: .bold))
                            .foregroundStyle(Color.black.opacity(0.84))
                        Text(yearlySubtitle)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundStyle(Color.black.opacity(0.60))
                    }
                    Spacer()
                    VStack(alignment: .trailing, spacing: 2) {
                        Text(yearlyPriceLabel)
                            .font(.system(size: 20, weight: .bold))
                            .foregroundStyle(Color.black.opacity(0.84))
                        if hasIntroOffer {
                            Text(isNorwegian ? "etter prøvetid" : "after trial")
                                .font(.system(size: 11, weight: .medium))
                                .foregroundStyle(Color.black.opacity(0.52))
                        }
                    }
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 18)
                .background(
                    RoundedRectangle(cornerRadius: 20, style: .continuous)
                        .fill(Color(hex: "A5F3EC"))
                )

                // Badge
                Text(hasIntroOffer
                     ? (isNorwegian ? "\(AppConfig.Subscription.trialDurationDays) dager gratis" : "\(AppConfig.Subscription.trialDurationDays) days free")
                     : (isNorwegian ? "Spar 34%" : "Save 34%"))
                    .font(.system(size: 11, weight: .bold))
                    .foregroundStyle(Color.white)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(
                        Capsule(style: .continuous)
                            .fill(Color(hex: "0A7A64"))
                    )
                    .offset(x: -14, y: -12)
            }
        }
        .buttonStyle(.plain)
        .disabled(subscriptionManager.isLoading || subscriptionManager.yearlyProduct == nil)
        .overlay {
            if subscriptionManager.isLoading {
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(Color.black.opacity(0.20))
                    .overlay { ProgressView().tint(.white) }
            }
        }
    }

    private var yearlyPrimaryLabel: String {
        if hasIntroOffer {
            return isNorwegian
                ? "Start \(AppConfig.Subscription.trialDurationDays) dager gratis"
                : "Start \(AppConfig.Subscription.trialDurationDays)-Day Free Trial"
        }
        return isNorwegian ? "Årlig — Anbefalt" : "Yearly — Best Value"
    }

    private var monthlyButton: some View {
        Button {
            trackPaywallEvent("paywall_cta_tapped", context: contextKey, metadata: ["plan": "monthly"])
            startPurchaseFlow(for: .monthly)
        } label: {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(isNorwegian ? "Månedlig" : "Monthly")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundStyle(Color.white.opacity(0.90))
                    Text(isNorwegian ? "Avslutt når som helst" : "Cancel anytime")
                        .font(.system(size: 13, weight: .regular))
                        .foregroundStyle(Color.white.opacity(0.55))
                }
                Spacer()
                Text(monthlyPriceLabel)
                    .font(.system(size: 20, weight: .bold))
                    .foregroundStyle(Color.white.opacity(0.90))
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 18)
            .background(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(Color.white.opacity(0.07))
                    .overlay(
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .stroke(Color.white.opacity(0.18), lineWidth: 1.5)
                    )
            )
        }
        .buttonStyle(.plain)
        .disabled(subscriptionManager.isLoading || subscriptionManager.monthlyProduct == nil)
    }

    // MARK: - Footer

    private var footerSection: some View {
        VStack(spacing: 10) {
            Button(isNorwegian ? "Gjenopprett kjøp" : "Restore Purchases") {
                trackPaywallEvent("paywall_restore_tapped", context: contextKey)
                Task { await subscriptionManager.restorePurchases() }
            }
            .font(.system(size: 14, weight: .medium))
            .foregroundStyle(Color.white.opacity(0.55))

            Button(isNorwegian ? "Administrer abonnement" : "Manage Subscription") {
                trackPaywallEvent("paywall_manage_subscription_tapped", context: contextKey)
                subscriptionManager.manageSubscription()
            }
            .font(.system(size: 14, weight: .medium))
            .foregroundStyle(Color.white.opacity(0.55))

            Text(
                isNorwegian
                    ? "Abonnementet fornyes automatisk. Administrer eller avslutt når som helst i App Store."
                    : "Subscription renews automatically. Manage or cancel anytime in the App Store."
            )
            .font(.system(size: 12, weight: .regular))
            .foregroundStyle(Color.white.opacity(0.38))
            .multilineTextAlignment(.center)

            if !subscriptionManager.hasLoadedProducts {
                Text(
                    isNorwegian
                        ? "Hvis prisene ikke vises ennå, prøv igjen eller bruk Gjenopprett kjøp når App Store er klar."
                        : "If prices are not visible yet, try again or use Restore Purchases once the App Store is ready."
                )
                .font(.system(size: 12, weight: .medium))
                .foregroundStyle(Color.white.opacity(0.48))
                .multilineTextAlignment(.center)
            }
        }
        .padding(.top, 8)
    }

    // MARK: - Price Labels

    private var monthlyPriceLabel: String {
        subscriptionManager.formattedRecurringPrice(for: .monthly, isNorwegian: isNorwegian)
    }

    private var yearlyPriceLabel: String {
        subscriptionManager.formattedPrice(for: .yearly, isNorwegian: isNorwegian)
    }

    private var yearlySubtitle: String {
        subscriptionManager.formattedYearlyPerMonthPrice(isNorwegian: isNorwegian)
    }

    private func startPurchaseFlow(for option: PaywallPlanSelectionOption) {
        if !authManager.isAuthenticated {
            pendingPurchaseOption = option
            showPurchaseAuthSheet = true
            return
        }

        Task {
            await performPurchase(for: option)
        }
    }

    private func resumePendingPurchaseIfNeeded() {
        guard authManager.isAuthenticated, let option = pendingPurchaseOption else { return }
        pendingPurchaseOption = nil
        Task {
            await performPurchase(for: option)
        }
    }

    private func performPurchase(for option: PaywallPlanSelectionOption) async {
        guard authManager.isAuthenticated else { return }
        switch option {
        case .monthly:
            guard let product = subscriptionManager.monthlyProduct else { return }
            await subscriptionManager.purchase(product)
        case .yearly:
            guard let product = subscriptionManager.yearlyProduct else { return }
            await subscriptionManager.purchase(product)
        }
    }
}

// MARK: - Locked Coach Card (inline paywall hint)

/// Drop this into any view to show an inline "locked" state when a free user hits their limit.
struct LockedCoachCard: View {
    let languageCode: String
    let onUpgrade: () -> Void

    private var isNorwegian: Bool { languageCode == "no" }

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "lock.fill")
                .font(.system(size: 22, weight: .semibold))
                .foregroundStyle(Color(hex: "A5F3EC"))

            Text(isNorwegian
                 ? "Du har brukt det gratis coach-spørsmålet ditt for denne økten."
                 : "You've used your free coach question for this workout.")
                .font(.system(size: 15, weight: .medium))
                .foregroundStyle(Color.white.opacity(0.88))
                .multilineTextAlignment(.center)

            Text(isNorwegian
                 ? "Oppgrader til Pro for å fortsette samtalen."
                 : "Upgrade to Pro to keep the conversation going.")
                .font(.system(size: 13, weight: .regular))
                .foregroundStyle(Color.white.opacity(0.62))
                .multilineTextAlignment(.center)

            Button {
                onUpgrade()
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "star.fill")
                    Text(isNorwegian ? "Fortsett med Pro" : "Continue with Pro")
                }
                .font(.system(size: 15, weight: .semibold))
                .foregroundStyle(Color.black.opacity(0.84))
                .padding(.horizontal, 24)
                .padding(.vertical, 13)
                .background(
                    Capsule(style: .continuous)
                        .fill(Color(hex: "A5F3EC"))
                )
            }
            .buttonStyle(.plain)
        }
        .padding(20)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(Color.white.opacity(0.06))
                .overlay(
                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                        .stroke(Color(hex: "A5F3EC").opacity(0.28), lineWidth: 1.5)
                )
        )
    }
}
