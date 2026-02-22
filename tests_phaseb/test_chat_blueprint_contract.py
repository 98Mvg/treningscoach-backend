from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


def test_chat_blueprint_is_registered() -> None:
    assert "chat_routes" in main.app.blueprints


def test_chat_blueprint_owns_brain_and_chat_routes() -> None:
    expected_paths = {
        "/brain/health",
        "/brain/switch",
        "/chat/start",
        "/chat/stream",
        "/chat/message",
        "/chat/sessions",
        "/chat/sessions/<session_id>",
        "/chat/personas",
    }
    found = {rule.rule for rule in main.app.url_map.iter_rules() if rule.rule in expected_paths}
    assert found == expected_paths
