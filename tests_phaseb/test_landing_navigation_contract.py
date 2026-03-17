from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "templates" / "index_codex.html"


def test_codex_landing_has_primary_cta_and_collapsible_navigation() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")

    assert 'class="pill pill-primary nav-primary-cta"' in text
    assert 'class="nav-toggle"' in text
    assert 'id="navOverflowMenu"' in text
    assert '.top-nav.nav-collapsed .nav-links' in text
    assert '.top-nav.nav-collapsed .nav-toggle' in text


def test_codex_landing_uses_runtime_overflow_detection_for_nav() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")

    assert "function updateNavigationLayout()" in text
    assert "dom.topNav.scrollWidth > dom.topNav.clientWidth + 2" in text
    assert "window.addEventListener(\"resize\", updateNavigationLayout)" in text
    assert "requestAnimationFrame(updateNavigationLayout)" in text
    assert "setNavMenuOpen(!state.navMenuOpen)" in text
