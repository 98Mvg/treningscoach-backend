"""Compatibility wrapper for root `user_memory.py`.

Source of truth runtime lives in repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ROOT_PATH = str(ROOT_DIR)
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

from user_memory import *  # noqa: F401,F403
