"""Compatibility wrapper for root `web_routes.py` source-of-truth module."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from web_routes import *  # noqa: F401,F403

