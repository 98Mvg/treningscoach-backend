from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUBSCRIPTION_MANAGER = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Services" / "SubscriptionManager.swift"
PAYWALL = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "PaywallView.swift"
PROFILE = REPO_ROOT / "TreningsCoach" / "TreningsCoach" / "Views" / "Tabs" / "ProfileView.swift"


def test_subscription_manager_exposes_manage_subscription_path():
    content = SUBSCRIPTION_MANAGER.read_text()
    assert "func manageSubscription()" in content
    assert "https://apps.apple.com/account/subscriptions" in content
    assert "UIApplication.shared.open(url)" in content


def test_paywall_exposes_restore_and_manage_subscription_buttons():
    content = PAYWALL.read_text()
    assert '"Restore Purchases"' in content
    assert '"Choose subscription"' in content
    assert '"Yearly plan"' in content
    assert '"Monthly plan"' in content
    assert "subscriptionManager.restorePurchases()" in content
    assert '"https://coachi.no/terms"' in content
    assert '"https://coachi.no/privacy"' in content


def test_profile_premium_section_exposes_reviewer_visible_subscription_actions():
    content = PROFILE.read_text()
    assert "ManageSubscriptionView()" in content
    assert "showManageSubscription = true" in content
    assert "title: L10n.manageSubscription" in content
    assert '"Se alle tilbudene"' in content
