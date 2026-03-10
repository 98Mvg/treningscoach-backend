from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WRANGLER_TOML = REPO_ROOT / "wrangler.toml"
WORKER_ENTRY = REPO_ROOT / "cloudflare" / "worker.js"
PACKAGE_JSON = REPO_ROOT / "package.json"


def test_cloudflare_worker_source_of_truth_files_exist() -> None:
    assert WRANGLER_TOML.exists()
    assert WORKER_ENTRY.exists()
    assert PACKAGE_JSON.exists()


def test_cloudflare_worker_wrangler_config_targets_proxy_worker() -> None:
    text = WRANGLER_TOML.read_text(encoding="utf-8")
    assert 'name = "treningscoach-backend"' in text
    assert 'main = "cloudflare/worker.js"' in text
    assert 'ORIGIN_URL = "https://treningscoach-backend.onrender.com"' in text


def test_cloudflare_worker_package_json_pins_wrangler_and_scripts() -> None:
    payload = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    assert payload["private"] is True
    assert payload["type"] == "module"
    assert payload["devDependencies"]["wrangler"]
    assert payload["scripts"]["cf:deploy"] == "wrangler deploy"
    assert payload["scripts"]["cf:dry-run"] == "wrangler deploy --dry-run"
    assert payload["scripts"]["cf:versions:upload"] == "wrangler versions upload"
