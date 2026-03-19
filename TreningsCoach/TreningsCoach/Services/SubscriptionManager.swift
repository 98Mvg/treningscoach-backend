//
//  SubscriptionManager.swift
//  TreningsCoach
//
//  StoreKit 2 subscription foundation for Phase 4 monetization.
//  Tracks entitlement state and exposes isPremium for feature gating.
//
//  Product IDs are defined in AppConfig.Subscription.
//  All purchase logic is isolated here — other code reads isPremium only.
//

import Foundation
import StoreKit
import UIKit

// MARK: - Subscription Status

enum SubscriptionStatus: Equatable {
    case unknown          // Not yet verified (startup)
    case free             // No active subscription
    case trial            // Active free trial
    case premium          // Active paid subscription
    case expired          // Lapsed subscription
}

enum SubscriptionBillingOption {
    case monthly
    case yearly
}

enum SubscriptionPurchaseOutcome: Equatable {
    case success(SubscriptionStatus)
    case pending
    case userCancelled
    case failed
}

// MARK: - SubscriptionManager

@MainActor
final class SubscriptionManager: ObservableObject {

    static let shared = SubscriptionManager()

    // MARK: - Published State

    @Published var status: SubscriptionStatus = .unknown
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published private(set) var hasLoadedProducts = false

    var isPremium: Bool {
        status == .premium || status == .trial
    }

    var currentPlanLabel: String {
        switch status {
        case .unknown:
            return "Checking"
        case .free:
            return "Free"
        case .trial:
            return "Free Trial"
        case .premium:
            return "Premium"
        case .expired:
            return "Expired"
        }
    }

    var hasPremiumAccess: Bool {
        isPremium || AuthManager.shared.currentUser?.subscriptionTier.isPremium == true
    }

    var resolvedPlanLabel: String {
        if isPremium {
            return currentPlanLabel
        }
        if AuthManager.shared.currentUser?.subscriptionTier.isPremium == true {
            return "Premium"
        }
        return currentPlanLabel
    }

    var monthlyHasIntroOffer: Bool {
        monthlyProduct?.subscription?.introductoryOffer != nil
    }

    var yearlyHasIntroOffer: Bool {
        yearlyProduct?.subscription?.introductoryOffer != nil
    }

    // MARK: - Private State

    private var products: [Product] = []
    private var transactionListener: Task<Void, Error>?
    private var initializationTask: Task<Void, Never>?
    private var hasInitialized = false

    // MARK: - Init

    private init() {
        transactionListener = listenForTransactions()
    }

    deinit {
        transactionListener?.cancel()
    }

    // MARK: - Lifecycle

    /// Call once at app startup to verify entitlement and load products.
    func initialize() async {
        if hasInitialized {
            return
        }
        if let initializationTask {
            await initializationTask.value
            return
        }

        let task = Task { @MainActor [weak self] in
            guard let self else { return }
            defer { self.initializationTask = nil }
            await self.refreshStatus()
            await self.loadProducts()
            await self.syncLatestEntitlementWithBackend()
            self.hasInitialized = true
        }

        initializationTask = task
        await task.value
    }

    // MARK: - Product Loading

    func loadProducts() async {
        let ids = Set(AppConfig.Subscription.allProductIDs)
        guard !ids.isEmpty else { return }
        do {
            products = try await Product.products(for: ids)
            hasLoadedProducts = !products.isEmpty
        } catch {
            // Non-fatal — sandbox or no connectivity. Products reload on next purchase attempt.
        }
    }

    var monthlyProduct: Product? {
        products.first { $0.id == AppConfig.Subscription.monthlyProductID }
    }

    var yearlyProduct: Product? {
        products.first { $0.id == AppConfig.Subscription.yearlyProductID }
    }

    func formattedPrice(for option: SubscriptionBillingOption, isNorwegian: Bool) -> String {
        let amount = selectedPriceAmount(for: option) ?? fallbackPriceAmount(for: option, isNorwegian: isNorwegian)
        return Self.formatCurrency(amount: amount, isNorwegian: isNorwegian)
    }

    func formattedRecurringPrice(for option: SubscriptionBillingOption, isNorwegian: Bool) -> String {
        let unit: String
        switch option {
        case .monthly:
            unit = isNorwegian ? "mnd" : "mo"
        case .yearly:
            unit = isNorwegian ? "år" : "yr"
        }
        return "\(formattedPrice(for: option, isNorwegian: isNorwegian))/\(unit)"
    }

    func formattedFreePrice(isNorwegian: Bool) -> String {
        Self.formatCurrency(amount: 0, isNorwegian: isNorwegian)
    }

    func formattedYearlyPerMonthPrice(isNorwegian: Bool) -> String {
        let yearlyAmount = selectedPriceAmount(for: .yearly) ?? fallbackPriceAmount(for: .yearly, isNorwegian: isNorwegian)
        let unit = isNorwegian ? "mnd" : "mo"
        return "\(Self.formatCurrency(amount: yearlyAmount / 12, isNorwegian: isNorwegian))/\(unit)"
    }

    // MARK: - Purchase

    @discardableResult
    func purchase(_ product: Product) async -> SubscriptionPurchaseOutcome {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let purchaseOptions = appAccountTokenOption()
            let result: Product.PurchaseResult
            if purchaseOptions.isEmpty {
                result = try await product.purchase()
            } else {
                result = try await product.purchase(options: purchaseOptions)
            }
            switch result {
            case .success(let verification):
                let signedTransactionInfo = verification.jwsRepresentation
                let transaction = try checkVerified(verification)
                await transaction.finish()
                await refreshStatus()
                let refreshedStatus = status
                // Cross-check with server (best-effort, non-blocking)
                let txID = String(transaction.id)
                Task {
                    _ = await BackendAPIService.shared.validateSubscription(
                        transactionID: txID,
                        signedTransactionInfo: signedTransactionInfo
                    )
                }
                return .success(refreshedStatus)
            case .pending:
                return .pending   // Transaction awaiting approval (e.g., Ask to Buy)
            case .userCancelled:
                return .userCancelled
            @unknown default:
                return .failed
            }
        } catch {
            errorMessage = error.localizedDescription
            return .failed
        }
    }

    // MARK: - Restore

    func restorePurchases() async {
        isLoading = true
        defer { isLoading = false }
        do {
            try await AppStore.sync()
            await refreshStatus()
            await syncLatestEntitlementWithBackend()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func manageSubscription() {
        guard let url = URL(string: "https://apps.apple.com/account/subscriptions") else {
            return
        }
        UIApplication.shared.open(url)
    }

    // MARK: - Entitlement Verification

    func refreshStatus() async {
        // StoreKit's Transaction.currentEntitlements can trigger network requests
        // to Apple's servers on first call. Running the iteration off the MainActor
        // prevents micro-hangs on the UI thread (e.g. during onboarding text input).
        let newStatus: SubscriptionStatus = await Task.detached(priority: .userInitiated) {
            var computed: SubscriptionStatus = .free
            for await result in Transaction.currentEntitlements {
                guard case .verified(let transaction) = result else { continue }
                guard AppConfig.Subscription.allProductIDs.contains(transaction.productID) else { continue }

                if let expirationDate = transaction.expirationDate {
                    if expirationDate > Date() {
                        // Active subscription — check if it is still in the trial period
                        if let offerType = transaction.offerType, offerType == .introductory {
                            computed = .trial
                        } else {
                            computed = .premium
                        }
                    } else {
                        computed = .expired
                    }
                } else {
                    // Non-consumable (not applicable here, but safe default)
                    computed = .premium
                }
            }
            return computed
        }.value
        status = newStatus  // back on @MainActor — single @Published update
    }

    // MARK: - Transaction Listener

    private func listenForTransactions() -> Task<Void, Error> {
        Task.detached {
            for await result in Transaction.updates {
                do {
                    let signedTransactionInfo = result.jwsRepresentation
                    let transaction = try await self.checkVerified(result)
                    await transaction.finish()
                    await self.refreshStatus()
                    _ = await BackendAPIService.shared.validateSubscription(
                        transactionID: String(transaction.id),
                        signedTransactionInfo: signedTransactionInfo
                    )
                } catch {
                    // Ignore unverified transactions
                }
            }
        }
    }

    private func appAccountTokenOption() -> Set<Product.PurchaseOption> {
        guard let currentUserID = AuthManager.shared.currentUser?.id,
              let uuid = UUID(uuidString: currentUserID) else {
            return []
        }
        return [.appAccountToken(uuid)]
    }

    private func syncLatestEntitlementWithBackend() async {
        guard AuthManager.shared.hasUsableSession() || AuthManager.shared.currentRefreshToken() != nil else {
            return
        }

        var latestTransactionID: String?
        var latestSignedTransactionInfo: String?
        var latestSignedDate: Date?

        for await result in Transaction.currentEntitlements {
            guard case .verified(let transaction) = result else { continue }
            guard AppConfig.Subscription.allProductIDs.contains(transaction.productID) else { continue }

            let candidateDate = transaction.revocationDate ?? transaction.expirationDate ?? transaction.purchaseDate
            if let latestSignedDate, candidateDate <= latestSignedDate {
                continue
            }

            latestSignedDate = candidateDate
            latestTransactionID = String(transaction.id)
            latestSignedTransactionInfo = result.jwsRepresentation
        }

        _ = await BackendAPIService.shared.validateSubscription(
            transactionID: latestTransactionID,
            signedTransactionInfo: latestSignedTransactionInfo
        )
    }

    // MARK: - Verification Helper

    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified:
            throw SubscriptionError.verificationFailed
        case .verified(let payload):
            return payload
        }
    }

    private func selectedPriceAmount(for option: SubscriptionBillingOption) -> Decimal? {
        switch option {
        case .monthly:
            return monthlyProduct?.price
        case .yearly:
            return yearlyProduct?.price
        }
    }

    private func fallbackPriceAmount(for option: SubscriptionBillingOption, isNorwegian: Bool) -> Decimal {
        switch option {
        case .monthly:
            return isNorwegian ? AppConfig.Subscription.fallbackMonthlyPriceNOK : AppConfig.Subscription.fallbackMonthlyPriceUSD
        case .yearly:
            return isNorwegian ? AppConfig.Subscription.fallbackYearlyPriceNOK : AppConfig.Subscription.fallbackYearlyPriceUSD
        }
    }

    private static func formatCurrency(amount: Decimal, isNorwegian: Bool) -> String {
        let formatter = NumberFormatter()
        formatter.locale = Locale(identifier: isNorwegian ? "nb_NO" : "en_US")
        formatter.numberStyle = .decimal
        formatter.usesGroupingSeparator = true
        formatter.minimumFractionDigits = 0
        formatter.maximumFractionDigits = 2

        let number = NSDecimalNumber(decimal: amount)
        let formattedAmount = formatter.string(from: number) ?? number.stringValue

        if isNorwegian {
            return "\(formattedAmount) kr"
        }
        return "$\(formattedAmount)"
    }
}

// MARK: - Errors

enum SubscriptionError: LocalizedError {
    case verificationFailed

    var errorDescription: String? {
        switch self {
        case .verificationFailed:
            return "Purchase verification failed. Please try again."
        }
    }
}
