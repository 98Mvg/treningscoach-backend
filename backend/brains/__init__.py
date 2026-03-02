"""Compatibility package for root `brains` modules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
ROOT_PATH = str(ROOT_DIR)
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

from brains import *  # noqa: F401,F403
