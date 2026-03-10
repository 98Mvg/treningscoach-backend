from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    REPO_ROOT / "docs" / "legal" / "coachi-personvernerklaering-utkast-no.md",
    REPO_ROOT / "docs" / "legal" / "coachi-vilkar-for-bruk-utkast-no.md",
    REPO_ROOT / "docs" / "settings" / "coachi-faq-og-kontohandlinger-no.md",
    REPO_ROOT / "docs" / "settings" / "coachi-settings-launch-spec-no.md",
]
PLACEHOLDERS = [
    "[COMPANY_NAME]",
    "[ORG_NUMBER]",
    "[COMPANY_ADDRESS]",
    "[SUPPORT_EMAIL]",
    "[PRIVACY_EMAIL]",
    "[WEBSITE_URL]",
    "[LAST_UPDATED_DATE]",
    "[SUBSCRIPTION_DETAILS]",
    "[PLACEHOLDER_FOR_VENUE]",
    "[VERIFY PROCESSOR]",
]


def test_launch_settings_and_legal_docs_do_not_ship_placeholder_tokens() -> None:
    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        for token in PLACEHOLDERS:
            assert token not in text, f"Found placeholder token {token} in {path.name}"


def test_launch_settings_and_legal_docs_use_active_support_and_site_details() -> None:
    for path in [
        REPO_ROOT / "docs" / "legal" / "coachi-personvernerklaering-utkast-no.md",
        REPO_ROOT / "docs" / "legal" / "coachi-vilkar-for-bruk-utkast-no.md",
        REPO_ROOT / "docs" / "settings" / "coachi-faq-og-kontohandlinger-no.md",
    ]:
        text = path.read_text(encoding="utf-8")
        assert "AI.Coachi@hotmail.com" in text, f"Missing support email in {path.name}"

    for path in [
        REPO_ROOT / "docs" / "legal" / "coachi-personvernerklaering-utkast-no.md",
        REPO_ROOT / "docs" / "legal" / "coachi-vilkar-for-bruk-utkast-no.md",
    ]:
        text = path.read_text(encoding="utf-8")
        assert "https://coachi.app" in text, f"Missing website in {path.name}"
        assert "10. mars 2026" in text, f"Missing launch-safe update date in {path.name}"


def test_privacy_and_terms_docs_match_launch_safe_processors_and_billing_copy() -> None:
    privacy = (REPO_ROOT / "docs" / "legal" / "coachi-personvernerklaering-utkast-no.md").read_text(encoding="utf-8")
    terms = (REPO_ROOT / "docs" / "legal" / "coachi-vilkar-for-bruk-utkast-no.md").read_text(encoding="utf-8")

    assert "hosting og drift: Render" in privacy
    assert "lydlagring og innholdssynk: Cloudflare R2" in privacy
    assert "tekst-til-tale: ElevenLabs" in privacy
    assert "e-post og support: Resend eller konfigurert SMTP-leverandør" in privacy
    assert "Coachi lanseres i gratis modus." in terms
    assert "App Store" in terms
