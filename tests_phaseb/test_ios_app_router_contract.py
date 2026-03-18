from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "TreningsCoachApp.swift"
APP_VIEW_MODEL = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "AppViewModel.swift"
CONTENT_VIEW = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "ContentView.swift"
API = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "BackendAPIService.swift"
SUBSCRIPTION_MANAGER = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "SubscriptionManager.swift"
PAYWALL = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "PaywallView.swift"
INFO_PLIST = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Info.plist"
WORKOUT_VM = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "ViewModels" / "WorkoutViewModel.swift"


def test_app_registers_root_open_url_handler() -> None:
    text = APP.read_text(encoding="utf-8")
    assert ".onOpenURL { url in" in text
    assert "appViewModel.handleIncomingURL(url)" in text


def test_app_view_model_exposes_deep_link_router_for_custom_and_universal_links() -> None:
    text = APP_VIEW_MODEL.read_text(encoding="utf-8")
    assert "enum AppDeepLinkDestination: Equatable" in text
    assert "@Published var pendingDeepLink: AppDeepLinkDestination?" in text
    assert 'scheme == "coachi"' in text
    assert '["coachi.app", "www.coachi.app"]' in text
    assert 'case "paywall":' in text
    assert 'case "subscription":' in text
    assert ".manageSubscription" in text
    assert ".restorePurchases" in text
    assert "consumePendingDeepLink()" in text


def test_main_tab_handles_deep_links_with_single_runtime_path() -> None:
    text = CONTENT_VIEW.read_text(encoding="utf-8")
    assert "@EnvironmentObject private var appViewModel: AppViewModel" in text
    assert "@State private var deepLinkPaywallContext: PaywallContext?" in text
    assert ".onChange(of: appViewModel.pendingDeepLink)" in text
    assert 'event: "deep_link_opened"' in text
    assert ".sheet(item: $deepLinkPaywallContext)" in text
    assert "PaywallView(context: context)" in text
    assert "subscriptionManager.manageSubscription()" in text
    assert "subscriptionManager.restorePurchases()" in text


def test_backend_api_service_uses_generic_mobile_analytics_and_signed_subscription_sync() -> None:
    text = API.read_text(encoding="utf-8")
    assert "static let shared = BackendAPIService()" in text
    assert 'private static let mobileAnalyticsAnonymousIDKey = "mobile_analytics_anonymous_id"' in text
    assert "func trackAnalyticsEvent(" in text
    assert '"\\(baseURL)/analytics/mobile"' in text
    assert '"anonymous_id": mobileAnalyticsAnonymousID()' in text
    assert "func validateSubscription(" in text
    assert '"signed_transaction_info"' in text


def test_subscription_manager_syncs_signed_transactions_and_app_account_token() -> None:
    text = SUBSCRIPTION_MANAGER.read_text(encoding="utf-8")
    assert "func initialize() async {" in text
    assert "if hasInitialized {" in text
    assert "if let initializationTask {" in text
    assert "await syncLatestEntitlementWithBackend()" in text
    assert "AuthManager.shared.hasUsableSession() || AuthManager.shared.currentRefreshToken() != nil" in text
    assert ".appAccountToken(uuid)" in text
    assert "verification.jwsRepresentation" in text
    assert "result.jwsRepresentation" in text
    assert "func validateSubscription(" in API.read_text(encoding="utf-8")


def test_paywall_and_workout_flow_use_generic_product_analytics() -> None:
    paywall_text = PAYWALL.read_text(encoding="utf-8")
    workout_text = WORKOUT_VM.read_text(encoding="utf-8")
    assert "trackAnalyticsEvent(event: event, metadata: meta)" in paywall_text
    assert '"paywall_restore_tapped"' in paywall_text
    assert 'trackAnalyticsEvent(\n            "workout_started"' in workout_text
    assert 'trackAnalyticsEvent(\n            "workout_completed"' in workout_text


def test_info_plist_registers_coachi_url_scheme() -> None:
    text = INFO_PLIST.read_text(encoding="utf-8")
    assert "<string>coachi</string>" in text
