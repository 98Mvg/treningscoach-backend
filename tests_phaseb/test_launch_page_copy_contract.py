from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATHS = [
    REPO_ROOT / "templates" / "index_launch.html",
    REPO_ROOT / "backend" / "templates" / "index_launch.html",
]


def test_launch_page_copy_is_free_mode_now() -> None:
    banned_fragments = [
        "Premium with full history",
        "premium with full history",
        "25 NOK/month",
        "25 kr/måned",
        "coaching-cue",
    ]
    required_fragments = [
        "Betalte planer kan komme senere.",
        "Paid plans may come later.",
    ]

    for path in TEMPLATE_PATHS:
        text = path.read_text(encoding="utf-8")
        for fragment in banned_fragments:
            assert fragment not in text, f"Found outdated paid-mode copy '{fragment}' in {path}"
        for fragment in required_fragments:
            assert fragment in text, f"Missing free-mode launch copy '{fragment}' in {path}"
