from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN = REPO_ROOT / "main.py"
ROOT_TEMPLATE = REPO_ROOT / "templates" / "index_launch.html"
BACKEND_TEMPLATE = REPO_ROOT / "backend" / "templates" / "index_launch.html"


def test_launch_site_is_the_default_coachi_web_variant() -> None:
    text = MAIN.read_text(encoding="utf-8")
    assert 'DEFAULT_WEB_VARIANT = getattr(config, "WEB_UI_VARIANT", "launch")' in text
    assert 'candidate = (raw_variant or DEFAULT_WEB_VARIANT or "launch").strip().lower()' in text
    assert 'candidate = "launch"' in text


def test_launch_site_keeps_primary_cta_visible_and_collapses_secondary_navigation() -> None:
    text = ROOT_TEMPLATE.read_text(encoding="utf-8")

    assert 'id="siteNav"' in text
    assert 'id="navLinks"' in text
    assert 'class="pill pill-primary nav-primary-cta"' in text
    assert 'class="hamburger" id="hamburger"' in text
    assert '.nav.nav-collapsed .nav-links' in text
    assert '.nav.nav-collapsed .lang-switch' in text
    assert '.nav.nav-collapsed .hamburger' in text
    assert '@media (max-width: 900px)' in text
    assert '@media (max-width: 560px)' in text


def test_launch_site_uses_runtime_overflow_detection_for_navigation() -> None:
    text = ROOT_TEMPLATE.read_text(encoding="utf-8")

    assert "function updateNavigationLayout()" in text
    assert "window.innerWidth <= 900" in text
    assert "siteNav.scrollWidth > siteNav.clientWidth + 2" in text
    assert 'window.addEventListener("resize", updateNavigationLayout)' in text
    assert "requestAnimationFrame(updateNavigationLayout);" in text
    assert "setMobileMenuOpen(!mobileMenu.classList.contains(\"open\"))" in text


def test_root_and_backend_launch_templates_stay_in_sync() -> None:
    root = ROOT_TEMPLATE.read_text(encoding="utf-8")
    backend = BACKEND_TEMPLATE.read_text(encoding="utf-8")
    assert root == backend
