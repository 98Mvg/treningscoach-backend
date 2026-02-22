from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


def test_web_blueprint_is_registered() -> None:
    assert "web_routes" in main.app.blueprints


def test_web_blueprint_owns_landing_and_runtime_routes() -> None:
    expected_paths = {"/", "/preview", "/preview/<variant>", "/health", "/app/runtime", "/waitlist", "/analytics/event"}
    found = {rule.rule for rule in main.app.url_map.iter_rules() if rule.rule in expected_paths}
    assert found == expected_paths
