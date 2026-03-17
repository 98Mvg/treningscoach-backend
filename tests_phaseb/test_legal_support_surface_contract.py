from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUPPORT_TEMPLATE = REPO_ROOT / "templates" / "support.html"
PRIVACY_TEMPLATE = REPO_ROOT / "templates" / "privacy.html"
TERMS_TEMPLATE = REPO_ROOT / "templates" / "termsofuse.html"
PRIVACY_DRAFT = REPO_ROOT / "docs" / "legal" / "coachi-personvernerklaering-utkast-no.md"
TERMS_DRAFT = REPO_ROOT / "docs" / "legal" / "coachi-vilkar-for-bruk-utkast-no.md"


def test_support_template_covers_launch_help_topics() -> None:
    text = SUPPORT_TEMPLATE.read_text(encoding="utf-8")
    assert "Hvordan Coachi fungerer" in text
    assert "Klokke og synkronisering" in text
    assert "Brukerprofil" in text
    assert "Abonnement" in text
    assert "Puls og pulsm&aring;ler" in text
    assert "Historikk og juridisk informasjon" in text
    assert "AI.Coachi@hotmail.com" in text
    assert "https://coachi.no/privacy" in text
    assert "https://coachi.no/terms" in text
    assert "support.miahealth.no" not in text


def test_privacy_template_is_launch_grade_and_history_aware() -> None:
    text = PRIVACY_TEMPLATE.read_text(encoding="utf-8")
    assert "Historikk og data i Coachi" in text
    assert "Puls, lyd og AI-funksjoner" in text
    assert "Render" in text
    assert "Cloudflare R2" in text
    assert "AI.Coachi@hotmail.com" in text
    assert "https://coachi.no" in text
    assert "coachi.app" not in text


def test_terms_template_is_launch_grade_and_coachi_specific() -> None:
    text = TERMS_TEMPLATE.read_text(encoding="utf-8")
    assert "Trening, helse og sensorer" in text
    assert "AI, lyd og Talk to Coach" in text
    assert "Historikk, oppsummeringer og tilgjengelighet" in text
    assert "App Store" in text
    assert "https://coachi.no" in text
    assert "coachi.app" not in text


def test_legal_drafts_match_public_coachi_domain() -> None:
    privacy_text = PRIVACY_DRAFT.read_text(encoding="utf-8")
    terms_text = TERMS_DRAFT.read_text(encoding="utf-8")
    assert "https://coachi.no" in privacy_text
    assert "https://coachi.no" in terms_text
    assert "Historikk" in privacy_text
    assert "Talk to Coach" in terms_text
    assert "coachi.app" not in privacy_text
    assert "coachi.app" not in terms_text
