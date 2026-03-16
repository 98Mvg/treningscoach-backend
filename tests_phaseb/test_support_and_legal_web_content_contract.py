from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUPPORT_HTML = REPO_ROOT / "templates" / "support.html"
PRIVACY_HTML = REPO_ROOT / "templates" / "privacy.html"
TERMS_HTML = REPO_ROOT / "templates" / "termsofuse.html"


def test_support_page_covers_launch_help_topics() -> None:
    text = SUPPORT_HTML.read_text(encoding="utf-8")
    assert "Hvordan Coachi fungerer" in text
    assert "Klokke og synkronisering" in text
    assert "Brukerprofil" in text
    assert "Abonnement" in text
    assert "Puls og pulsm&aring;ler" in text
    assert "Historikk og juridisk informasjon" in text
    assert "hvordan treningsdata, puls og AI-funksjoner behandles" in text
    assert "GAARDER" in text
    assert "937 327 412" in text
    assert "Brenneribakken 10" in text
    assert "2815 Gj&oslash;vik" in text
    assert "mailto:AI.Coachi@hotmail.com" in text
    assert "/privacy" in text
    assert "/terms" in text


def test_privacy_page_is_upgrade_from_launch_stub() -> None:
    text = PRIVACY_HTML.read_text(encoding="utf-8")
    assert "Historikk og data" in text
    assert "Behandlingsgrunnlag og databehandlere" in text
    assert "Lagringstid, sletting og rettigheter" in text
    assert "Sikkerhet og endringer" in text
    assert "GAARDER" in text
    assert "937 327 412" in text
    assert "Brenneribakken 10" in text
    assert "2815 Gj&oslash;vik" in text
    assert "xAI, Google, OpenAI og Anthropic" in text
    assert "Cloudflare R2" in text
    assert "Render" in text
    assert "coachi.no" in text


def test_terms_page_covers_history_data_and_ai() -> None:
    text = TERMS_HTML.read_text(encoding="utf-8")
    assert "Historikk, oppsummeringer og tilgjengelighet" in text
    assert "AI, lyd og Talk to Coach" in text
    assert "GAARDER" in text
    assert "937 327 412" in text
    assert "Brenneribakken 10" in text
    assert "2815 Gj&oslash;vik" in text
    assert "App Store" in text
    assert "coachi.no" in text
