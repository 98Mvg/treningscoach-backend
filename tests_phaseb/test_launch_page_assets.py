from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LAUNCH_TEMPLATE = REPO_ROOT / "templates" / "index_launch.html"
BACKEND_LAUNCH_TEMPLATE = REPO_ROOT / "backend" / "templates" / "index_launch.html"
ROOT_STATIC_IMAGES = REPO_ROOT / "static" / "site" / "images"
BACKEND_STATIC_IMAGES = REPO_ROOT / "backend" / "static" / "site" / "images"


def _launch_image_references() -> list[str]:
    html = LAUNCH_TEMPLATE.read_text(encoding="utf-8")
    return sorted(set(re.findall(r"site/images/([A-Za-z0-9._-]+)", html)))


def test_launch_page_images_exist_in_root_static() -> None:
    missing = [name for name in _launch_image_references() if not (ROOT_STATIC_IMAGES / name).exists()]
    assert not missing, f"Missing launch images in root static: {missing}"


def test_launch_page_images_exist_in_backend_static() -> None:
    missing = [name for name in _launch_image_references() if not (BACKEND_STATIC_IMAGES / name).exists()]
    assert not missing, f"Missing launch images in backend static: {missing}"


def test_root_and_backend_launch_templates_are_in_sync() -> None:
    root_html = LAUNCH_TEMPLATE.read_text(encoding="utf-8")
    backend_html = BACKEND_LAUNCH_TEMPLATE.read_text(encoding="utf-8")
    assert root_html == backend_html, "templates/index_launch.html and backend/templates/index_launch.html drifted"


def test_launch_template_uses_static_url_for_images() -> None:
    html = LAUNCH_TEMPLATE.read_text(encoding="utf-8")
    expected = [
        "hero-runner.png",
        "step-choose-workout.png",
        "step-coaching.png",
        "watch-hr.png",
        "coach-push.png",
    ]
    for image_name in expected:
        token = f"url_for('static', filename='site/images/{image_name}'"
        assert token in html, f"Expected url_for() static reference for {image_name}"
