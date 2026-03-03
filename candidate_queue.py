"""Candidate queue library for offline phrase curation workflows.

Single source of truth for queue persistence, dedup keys, and helper mappings.
This module is intentionally runtime-independent (no workout/coaching path imports).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, Optional

# Queue storage
QUEUE_PATH = os.path.join("output", "candidate_queue.json")

# Safety caps for generation commands
MAX_TOTAL_PER_RUN = 30
MAX_PER_FAMILY_PER_RUN = 10

# Model defaults for offline generation tooling
CANDIDATE_MODEL_DEFAULT = "grok-3-mini"
CANDIDATE_TEMPERATURE = 0.9
CANDIDATE_MAX_TOKENS = 24
CANDIDATE_TIMEOUT = 10

PURPOSE_TAGS = {
    "interval.motivate": "motivation_in_zone",
    "easy_run.motivate": "motivation_in_zone",
    "zone.above": "hr_correction_above",
    "zone.below": "hr_correction_below",
    "zone.silence": "silence_filler",
    "zone.breath": "breath_guidance",
}

EVENT_TO_FAMILIES = {
    "interval_in_target_sustained": [
        "interval.motivate.s1",
        "interval.motivate.s2",
        "interval.motivate.s3",
        "interval.motivate.s4",
    ],
    "easy_run_in_target_sustained": [
        "easy_run.motivate.s1",
        "easy_run.motivate.s2",
        "easy_run.motivate.s3",
        "easy_run.motivate.s4",
    ],
}

ALL_MOTIVATION_FAMILIES = [
    "interval.motivate.s1",
    "interval.motivate.s2",
    "interval.motivate.s3",
    "interval.motivate.s4",
    "easy_run.motivate.s1",
    "easy_run.motivate.s2",
    "easy_run.motivate.s3",
    "easy_run.motivate.s4",
]


def load_queue(path: Optional[str] = None) -> list[dict]:
    """Load queue from disk. Returns [] when file is missing/invalid."""
    queue_path = path or QUEUE_PATH
    try:
        with open(queue_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return payload if isinstance(payload, list) else []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_queue(candidates: list[dict], path: Optional[str] = None) -> None:
    """Persist candidate list to disk with stable UTF-8 formatting."""
    queue_path = path or QUEUE_PATH
    Path(queue_path).parent.mkdir(parents=True, exist_ok=True)
    with open(queue_path, "w", encoding="utf-8") as fh:
        json.dump(candidates, fh, ensure_ascii=False, indent=2)


def compute_variant_key(
    event_type: str,
    phrase_family: str,
    text_en: str,
    text_no: str,
    persona: str,
) -> str:
    """Stable SHA256 dedup key across family/language/persona."""
    base = "|".join([
        (event_type or "").strip(),
        (phrase_family or "").strip(),
        (text_en or "").strip(),
        (text_no or "").strip(),
        (persona or "").strip(),
    ])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def is_duplicate(variant_key: str, queue: Iterable[dict]) -> bool:
    """Return True when key already exists in queue regardless of status."""
    key = (variant_key or "").strip()
    if not key:
        return False
    for candidate in queue:
        if str(candidate.get("variant_key") or "").strip() == key:
            return True
    return False
