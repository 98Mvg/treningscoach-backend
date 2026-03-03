"""Candidate queue library for offline phrase curation workflows.

Single source of truth for queue persistence, dedup keys, and helper mappings.
This module is intentionally runtime-independent (no workout/coaching path imports).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from norwegian_phrase_quality import rewrite_norwegian_phrase
from tts_phrase_catalog import PHRASE_CATALOG

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

_FORBIDDEN_EN = (
    "breathing exercise",
    "open app",
    "open the app",
    "ai coach",
)

_FORBIDDEN_NO = (
    "pusteøvelse",
    "åpne appen",
    "ai coach",
)

_NORWEGIAN_GOOD_EXAMPLES = [
    "Mer press nå!",
    "Trykk litt hardere.",
    "Bra jobba.",
    "Finn jevn rytme.",
    "Øk tempoet.",
    "Du klarer det!",
    "Hold deg fokusert!",
    "Nå øker vi trykket.",
]

_NORWEGIAN_BAD_EXAMPLES = [
    "Vakkert",
    "Gi meg mer kraft",
    "Holdt",
    "Jevn opp",
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


def _word_count(value: str) -> int:
    return len([token for token in str(value or "").strip().split() if token])


def validate_candidate(text_en: str, text_no: str, persona: str) -> dict:
    """Validate candidate cue quality with lightweight deterministic rules."""
    reasons: list[str] = []
    en = str(text_en or "").strip()
    no = str(text_no or "").strip()
    _ = persona  # reserved for future persona-specific rules

    if not en:
        reasons.append("en_empty")
    if not no:
        reasons.append("no_empty")

    if _word_count(en) > 12:
        reasons.append("en_length_too_long")
    if _word_count(no) > 12:
        reasons.append("no_length_too_long")

    en_lower = en.lower()
    no_lower = no.lower()
    if any(token in en_lower for token in _FORBIDDEN_EN):
        reasons.append("en_forbidden_phrase")
    if any(token in no_lower for token in _FORBIDDEN_NO):
        reasons.append("no_forbidden_phrase")

    return {"passed": len(reasons) == 0, "reasons": reasons}


def _existing_variant_numbers(phrase_family: str) -> list[int]:
    """Return sorted variant numbers for IDs that match <family>.<n>."""
    family = str(phrase_family or "").strip()
    if not family:
        return []
    pattern = re.compile(rf"^{re.escape(family)}\.(\d+)$")
    found: set[int] = set()
    for entry in PHRASE_CATALOG:
        phrase_id = str(entry.get("id") or "").strip()
        match = pattern.match(phrase_id)
        if match:
            found.add(int(match.group(1)))
    return sorted(found)


def next_variant_id(phrase_family: str) -> str:
    """Compute next catalog ID under family as max(existing)+1."""
    family = str(phrase_family or "").strip()
    if not family:
        return ".1"
    numbers = _existing_variant_numbers(family)
    next_number = (max(numbers) + 1) if numbers else 1
    return f"{family}.{next_number}"


def promote_to_catalog(candidates: list[dict], dry_run: bool = True) -> list[str]:
    """Assign IDs to approved candidates and mark them as promoted.

    Note: this function is assignment-only in current implementation.
    It does not mutate source files even when dry_run=False.
    """
    _ = dry_run  # kept for CLI compatibility
    assigned_ids: list[str] = []
    local_max: dict[str, int] = {}
    for candidate in candidates:
        if str(candidate.get("status") or "").strip().lower() != "approved":
            continue
        family = str(candidate.get("phrase_family") or "").strip()
        if not family:
            continue
        if family not in local_max:
            existing = _existing_variant_numbers(family)
            local_max[family] = max(existing) if existing else 0
        local_max[family] += 1
        phrase_id = f"{family}.{local_max[family]}"
        candidate["status"] = "promoted"
        candidate["promoted_phrase_id"] = phrase_id
        assigned_ids.append(phrase_id)
    return assigned_ids


def _candidate_id() -> str:
    ts = datetime.now(timezone.utc)
    return ts.strftime("cand_%Y%m%d_%H%M%S_%f")


def make_candidate(
    *,
    event_type: str,
    phrase_family: str,
    text_en: str,
    text_no: str,
    persona: str,
    model: str = CANDIDATE_MODEL_DEFAULT,
    source: str = "cli",
    existing_queue: Optional[Iterable[dict]] = None,
) -> dict:
    """Create a normalized candidate object."""
    en = str(text_en or "").strip()
    no = rewrite_norwegian_phrase(str(text_no or "").strip())
    queue = list(existing_queue or [])
    variant_key = compute_variant_key(event_type, phrase_family, en, no, persona)
    validation = validate_candidate(en, no, persona)
    status = "skipped" if is_duplicate(variant_key, queue) else "pending"
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "candidate_id": _candidate_id(),
        "status": status,
        "event_type": str(event_type or "").strip(),
        "phrase_family": str(phrase_family or "").strip(),
        "generated_text_en": en,
        "generated_text_no": no,
        "languages": ["en", "no"],
        "model": str(model or CANDIDATE_MODEL_DEFAULT),
        "model_params": {
            "temperature": CANDIDATE_TEMPERATURE,
            "max_tokens": CANDIDATE_MAX_TOKENS,
        },
        "persona": str(persona or "").strip(),
        "source": str(source or "cli"),
        "variant_key": variant_key,
        "validation": validation,
        "context": {
            "phase": None,
            "intensity": None,
            "session_id": None,
            "heart_rate": None,
            "elapsed_seconds": None,
        },
        "created_at": now_iso,
        "reviewed_at": None,
        "reviewer_note": None,
    }


def get_avoid_lists(phrase_family: str, queue: Iterable[dict]) -> tuple[list[str], list[str]]:
    """Return EN/NO avoid strings from catalog + queued candidates for family."""
    family = str(phrase_family or "").strip()
    en: list[str] = []
    no: list[str] = []
    for entry in PHRASE_CATALOG:
        phrase_id = str(entry.get("id") or "").strip()
        if phrase_id.startswith(f"{family}."):
            en_text = str(entry.get("en") or "").strip()
            no_text = str(entry.get("no") or "").strip()
            if en_text:
                en.append(en_text)
            if no_text:
                no.append(no_text)
    for candidate in queue:
        if str(candidate.get("phrase_family") or "").strip() != family:
            continue
        en_text = str(candidate.get("generated_text_en") or "").strip()
        no_text = str(candidate.get("generated_text_no") or "").strip()
        if en_text:
            en.append(en_text)
        if no_text:
            no.append(no_text)
    return en, no


def infer_purpose_tag(phrase_family: str) -> str:
    """Infer purpose tag by prefix, fallback to generic coaching."""
    family = str(phrase_family or "").strip()
    for prefix, purpose in PURPOSE_TAGS.items():
        if family.startswith(prefix):
            return purpose
    return "coaching"


def get_norwegian_tone_examples() -> tuple[list[str], list[str]]:
    """Return (good_examples, bad_examples) used for prompt grounding."""
    return list(_NORWEGIAN_GOOD_EXAMPLES), list(_NORWEGIAN_BAD_EXAMPLES)
