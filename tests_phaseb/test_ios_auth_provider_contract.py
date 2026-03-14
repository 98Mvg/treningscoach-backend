from pathlib import Path


AUTH_MANAGER = Path(
    "/Users/mariusgaarder/Documents/treningscoach/TreningsCoach/TreningsCoach/Services/AuthManager.swift"
)


def _method_block(text: str, signature: str, next_marker: str) -> str:
    start = text.index(signature)
    end = text.index(next_marker, start)
    return text[start:end]


def test_placeholder_provider_tokens_are_removed() -> None:
    text = AUTH_MANAGER.read_text(encoding="utf-8")
    assert "google_id_token_placeholder" not in text
    assert "facebook_access_token_placeholder" not in text
    assert "vipps_access_token_placeholder" not in text


def test_non_apple_provider_methods_fail_locally_without_backend_requests() -> None:
    """Google has a real flow now (gated by feature flag). Facebook and Vipps are still stubs."""
    text = AUTH_MANAGER.read_text(encoding="utf-8")

    google = _method_block(text, "func signInWithGoogle() async -> Bool {", "    // MARK: - Email Sign-In")
    facebook = _method_block(text, "func signInWithFacebook() async {", "    // MARK: - Vipps Sign-In")
    vipps = _method_block(text, "func signInWithVipps() async {", "    // MARK: - Sign Out")

    # Google now has a real auth flow behind AppConfig.Auth.googleSignInEnabled
    assert "sendAuthRequest(provider: \"google\"" in google
    assert "markUnsupportedProvider(" in google  # fallback when flag is off
    assert "AppConfig.Auth.googleRedirectScheme" in google
    assert "code_challenge_method" in google
    assert "code_verifier" in google
    assert "pkceCodeChallenge(for: codeVerifier)" in google

    assert "markUnsupportedProvider(label: L10n.signInWithFacebook)" in facebook
    assert "markUnsupportedProvider(label: L10n.signInWithVipps)" in vipps

    assert "sendAuthRequest(" not in facebook
    assert "sendAuthRequest(" not in vipps
