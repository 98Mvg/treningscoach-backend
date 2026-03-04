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


def test_entitlements_include_apple_signin_capability():
    text = ENTITLEMENTS.read_text(encoding="utf-8")
    assert "com.apple.developer.applesignin" in text
    assert "<string>Default</string>" in text
