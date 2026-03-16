from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATHS = [
    REPO_ROOT / "templates" / "index_launch.html",
    REPO_ROOT / "backend" / "templates" / "index_launch.html",
]
DOWNLOAD_PAGE = REPO_ROOT / "templates" / "download.html"


def test_launch_page_copy_matches_free_download_optional_premium_model() -> None:
    banned_fragments = [
        "Premium with full history",
        "premium with full history",
        "25 NOK/month",
        "25 kr/måned",
        "coaching-cue",
        "Betalte planer kan komme senere.",
        "Paid plans may come later.",
        "treningscoach-backend.onrender.com",
    ]
    required_fragments = [
        "Coachi er gratis å laste ned. Premium er valgfritt",
        "Coachi is free to download. Premium is optional",
        'href="/privacy"',
        'href="/terms"',
    ]

    for path in TEMPLATE_PATHS:
        text = path.read_text(encoding="utf-8")
        for fragment in banned_fragments:
            assert fragment not in text, f"Found outdated paid-mode copy '{fragment}' in {path}"
        for fragment in required_fragments:
            assert fragment in text, f"Missing free-mode launch copy '{fragment}' in {path}"


def test_download_page_copy_and_legal_links_match_launch_model() -> None:
    text = DOWNLOAD_PAGE.read_text(encoding="utf-8")

    banned_fragments = [
        "Gratis mens vi er i beta.",
        "Gratis i beta. Ingen skjulte kostnader.",
        "Free while in beta.",
        "Free in beta. No hidden costs.",
    ]
    required_fragments = [
        "Gratis å laste ned med valgfri Premium i appen.",
        "Gratis å laste ned. Premium er valgfritt.",
        "Free to download with optional Premium in the app.",
        "Free to download. Premium is optional.",
        'href="/privacy"',
        'href="/terms"',
    ]

    for fragment in banned_fragments:
        assert fragment not in text, f"Found stale beta copy '{fragment}' in {DOWNLOAD_PAGE}"
    for fragment in required_fragments:
        assert fragment in text, f"Missing updated launch copy '{fragment}' in {DOWNLOAD_PAGE}"
