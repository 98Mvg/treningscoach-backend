"""Compatibility backend entrypoint.

Source of truth runtime lives in repository root `main.py`.
This shim exists only to keep legacy scripts working while avoiding
root/backend runtime drift.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ROOT_PATH = str(ROOT_DIR)
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

from main import app  # noqa: E402


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=False)
