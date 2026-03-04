import plistlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTH_MANAGER = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Services"
    / "AuthManager.swift"
)
AUTH_VIEW = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Views"
    / "Onboarding"
    / "AuthView.swift"
)
ENTITLEMENTS = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "TreningsCoach.entitlements"
)
INFO_PLIST = (
    REPO_ROOT
    / "TreningsCoach"
    / "TreningsCoach"
    / "Info.plist"
)


def _apple_signin_enabled() -> bool:
    with INFO_PLIST.open("rb") as f:
        info = plistlib.load(f)
    return bool(info.get("APPLE_SIGN_IN_ENABLED", False))


def test_auth_manager_has_real_apple_signin_flow():
    text = AUTH_MANAGER.read_text(encoding="utf-8")
    assert "import AuthenticationServices" in text
    assert "func signInWithApple() async -> Bool" in text
    assert 'provider: "apple"' in text
    assert '"identity_token"' in text
    assert "ASAuthorizationAppleIDProvider" in text


def test_auth_view_uses_auth_manager_apple_signin():
    text = AUTH_VIEW.read_text(encoding="utf-8")
    assert "@EnvironmentObject var authManager: AuthManager" in text
    assert "await authManager.signInWithApple()" in text


def test_entitlements_match_apple_signin_flag():
    text = ENTITLEMENTS.read_text(encoding="utf-8")
    has_apple_signin_entitlement = "com.apple.developer.applesignin" in text

    if _apple_signin_enabled():
        assert has_apple_signin_entitlement
        assert "<string>Default</string>" in text
    else:
        assert not has_apple_signin_entitlement
