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

// MARK: - SubscriptionManager

@MainActor
final class SubscriptionManager: ObservableObject {

    static let shared = SubscriptionManager()

    // MARK: - Published State

    @Published var status: SubscriptionStatus = .unknown
    @Published var isLoading = false
    @Published var errorMessage: String?

    var isPremium: Bool {
        status == .premium || status == .trial
    }

    var hasLoadedProducts: Bool {
        !products.isEmpty
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

    // MARK: - Private State

    private var products: [Product] = []
    private var transactionListener: Task<Void, Error>?

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
        await refreshStatus()
        await loadProducts()
        await syncLatestEntitlementWithBackend()
    }

    // MARK: - Product Loading

    func loadProducts() async {
        let ids = Set(AppConfig.Subscription.allProductIDs)
        guard !ids.isEmpty else { return }
        do {
            products = try await Product.products(for: ids)
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

    // MARK: - Purchase

    func purchase(_ product: Product) async {
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
                // Cross-check with server (best-effort, non-blocking)
                let txID = String(transaction.id)
                Task {
                    _ = await BackendAPIService.shared.validateSubscription(
                        transactionID: txID,
                        signedTransactionInfo: signedTransactionInfo
                    )
                }
            case .pending:
                break   // Transaction awaiting approval (e.g., Ask to Buy)
            case .userCancelled:
                break
            @unknown default:
                break
            }
        } catch {
            errorMessage = error.localizedDescription
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
