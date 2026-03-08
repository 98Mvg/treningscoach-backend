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
    text = AUTH_MANAGER.read_text(encoding="utf-8")

    google = _method_block(text, "func signInWithGoogle() async {", "    // MARK: - Apple Sign-In")
    facebook = _method_block(text, "func signInWithFacebook() async {", "    // MARK: - Vipps Sign-In")
    vipps = _method_block(text, "func signInWithVipps() async {", "    // MARK: - Sign Out")

    assert "markUnsupportedProvider(label: L10n.registerWithGoogle)" in google
    assert "markUnsupportedProvider(label: L10n.signInWithFacebook)" in facebook
    assert "markUnsupportedProvider(label: L10n.signInWithVipps)" in vipps

    assert "sendAuthRequest(" not in google
    assert "sendAuthRequest(" not in facebook
    assert "sendAuthRequest(" not in vipps
