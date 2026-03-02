# Candidate Queue System — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build CLI tools to generate, review, and promote AI-generated coaching phrase variants into the existing audio pack pipeline.

**Architecture:** A pure-Python queue library (`candidate_queue.py`) handles all queue I/O, dedup, validation, variant numbering, and catalog promotion. Two CLI tools (`generate_candidates.py`, `candidate_review.py`) use the library. Zero runtime changes — nothing touches `main.py`, `zone_event_motor.py`, or the workout flow.

**Tech Stack:** Python 3, hashlib (SHA256), json, argparse. Grok API via `brain_router.py`. XLSX export via same XML-zip pattern as `tools/phrase_catalog_editor.py`. No new dependencies.

**Design doc:** `docs/plans/2026-03-02-candidate-queue-design.md`

---

### Task 1: candidate_queue.py — Constants and Queue I/O

**Files:**
- Create: `candidate_queue.py`
- Create: `tests_phaseb/test_candidate_queue.py`

**Step 1: Write the failing tests**

Create `tests_phaseb/test_candidate_queue.py`:

```python
"""Tests for candidate_queue.py — pure queue library."""

import json
import os
import sys
import tempfile

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import candidate_queue as cq


class TestConstants:
    def test_queue_path_defined(self):
        assert hasattr(cq, "QUEUE_PATH")
        assert "candidate_queue.json" in cq.QUEUE_PATH

    def test_caps_defined(self):
        assert cq.MAX_TOTAL_PER_RUN == 30
        assert cq.MAX_PER_FAMILY_PER_RUN == 10

    def test_purpose_tags_defined(self):
        assert "interval.motivate" in cq.PURPOSE_TAGS
        assert "easy_run.motivate" in cq.PURPOSE_TAGS
        assert cq.PURPOSE_TAGS["interval.motivate"] == "motivation_in_zone"


class TestLoadSave:
    def test_load_empty_file(self, tmp_path):
        path = tmp_path / "queue.json"
        result = cq.load_queue(str(path))
        assert result == []

    def test_save_and_load_roundtrip(self, tmp_path):
        path = tmp_path / "queue.json"
        candidates = [
            {"candidate_id": "cand_001", "status": "pending", "phrase_family": "interval.motivate.s2"},
            {"candidate_id": "cand_002", "status": "approved", "phrase_family": "easy_run.motivate.s1"},
        ]
        cq.save_queue(candidates, str(path))
        loaded = cq.load_queue(str(path))
        assert len(loaded) == 2
        assert loaded[0]["candidate_id"] == "cand_001"
        assert loaded[1]["status"] == "approved"

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "sub" / "deep" / "queue.json"
        cq.save_queue([{"candidate_id": "test"}], str(path))
        assert path.exists()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests_phaseb/test_candidate_queue.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'candidate_queue'`

**Step 3: Write minimal implementation**

Create `candidate_queue.py`:

```python
"""
Candidate Queue Library — pure queue I/O, dedup, validation, variant numbering.

No Grok/API dependencies. Used by tools/generate_candidates.py and
tools/candidate_review.py. See docs/plans/2026-03-02-candidate-queue-design.md.
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants (tool-only, not runtime config.py)
# ---------------------------------------------------------------------------

QUEUE_PATH = os.path.join("output", "candidate_queue.json")

MAX_TOTAL_PER_RUN = 30
MAX_PER_FAMILY_PER_RUN = 10

CANDIDATE_MODEL_DEFAULT = "grok-3-mini"
CANDIDATE_TEMPERATURE = 0.9
CANDIDATE_MAX_TOKENS = 24
CANDIDATE_TIMEOUT = 10  # seconds — generous for offline

PURPOSE_TAGS = {
    "interval.motivate": "motivation_in_zone",
    "easy_run.motivate": "motivation_in_zone",
    "zone.above":        "hr_correction_above",
    "zone.below":        "hr_correction_below",
    "zone.silence":      "silence_filler",
    "zone.breath":       "breath_guidance",
}

# Map event_type → list of phrase families it can target
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

# All motivation families (for --all-motivation flag)
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


# ---------------------------------------------------------------------------
# Queue I/O
# ---------------------------------------------------------------------------

def load_queue(path: Optional[str] = None) -> List[dict]:
    """Load candidate queue from JSON file. Returns [] if file missing."""
    p = path or QUEUE_PATH
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_queue(candidates: List[dict], path: Optional[str] = None) -> None:
    """Save candidate queue to JSON file. Creates parent dirs if needed."""
    p = path or QUEUE_PATH
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests_phaseb/test_candidate_queue.py -v`
Expected: 6 PASS

**Step 5: Commit**

```bash
git add candidate_queue.py tests_phaseb/test_candidate_queue.py
git commit -m "feat: candidate_queue.py — constants + queue I/O with tests"
```

---

### Task 2: candidate_queue.py — variant_key + dedup

**Files:**
- Modify: `candidate_queue.py`
- Modify: `tests_phaseb/test_candidate_queue.py`

**Step 1: Write the failing tests**

Append to `tests_phaseb/test_candidate_queue.py`:

```python
class TestVariantKey:
    def test_deterministic(self):
        key1 = cq.compute_variant_key("interval_in_target_sustained", "interval.motivate.s2", "Come on!", "Kom igjen!", "personal_trainer")
        key2 = cq.compute_variant_key("interval_in_target_sustained", "interval.motivate.s2", "Come on!", "Kom igjen!", "personal_trainer")
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex

    def test_different_text_different_key(self):
        key1 = cq.compute_variant_key("interval_in_target_sustained", "interval.motivate.s2", "Come on!", "Kom igjen!", "personal_trainer")
        key2 = cq.compute_variant_key("interval_in_target_sustained", "interval.motivate.s2", "Push it!", "Trykk til!", "personal_trainer")
        assert key1 != key2

    def test_different_persona_different_key(self):
        key1 = cq.compute_variant_key("interval_in_target_sustained", "interval.motivate.s2", "Come on!", "Kom igjen!", "personal_trainer")
        key2 = cq.compute_variant_key("interval_in_target_sustained", "interval.motivate.s2", "Come on!", "Kom igjen!", "toxic_mode")
        assert key1 != key2


class TestIsDuplicate:
    def test_duplicate_in_queue(self):
        queue = [{"variant_key": "abc123", "status": "pending"}]
        assert cq.is_duplicate("abc123", queue) is True

    def test_not_duplicate(self):
        queue = [{"variant_key": "abc123", "status": "pending"}]
        assert cq.is_duplicate("xyz789", queue) is False

    def test_skipped_still_counts(self):
        queue = [{"variant_key": "abc123", "status": "skipped"}]
        assert cq.is_duplicate("abc123", queue) is True

    def test_empty_queue(self):
        assert cq.is_duplicate("abc123", []) is False
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests_phaseb/test_candidate_queue.py::TestVariantKey -v`
Expected: FAIL — `AttributeError: module 'candidate_queue' has no attribute 'compute_variant_key'`

**Step 3: Write minimal implementation**

Add to `candidate_queue.py` after the queue I/O section:

```python
# ---------------------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------------------

def compute_variant_key(
    event_type: str,
    phrase_family: str,
    text_en: str,
    text_no: str,
    persona: str,
) -> str:
    """SHA256 hex of (event_type + family + en + no + persona). Stable dedup key."""
    payload = f"{event_type}|{phrase_family}|{text_en}|{text_no}|{persona}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_duplicate(variant_key: str, queue: List[dict]) -> bool:
    """Check if variant_key already exists in the queue (any status)."""
    return any(c.get("variant_key") == variant_key for c in queue)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests_phaseb/test_candidate_queue.py -v`
Expected: All PASS (previous 6 + new 7 = 13)

**Step 5: Commit**

```bash
git add candidate_queue.py tests_phaseb/test_candidate_queue.py
git commit -m "feat: candidate_queue — variant_key computation + dedup"
```

---

### Task 3: candidate_queue.py — validate_candidate

**Files:**
- Modify: `candidate_queue.py`
- Modify: `tests_phaseb/test_candidate_queue.py`

**Step 1: Write the failing tests**

Append to `tests_phaseb/test_candidate_queue.py`:

```python
class TestValidateCandidate:
    def test_valid_short_cue(self):
        result = cq.validate_candidate("Come on!", "Kom igjen!", "personal_trainer")
        assert result["passed"] is True
        assert result["reasons"] == []

    def test_too_long_en(self):
        long_text = " ".join(["word"] * 20)
        result = cq.validate_candidate(long_text, "Kort.", "personal_trainer")
        assert result["passed"] is False
        assert any("en" in r and "length" in r.lower() for r in result["reasons"])

    def test_too_long_no(self):
        result = cq.validate_candidate("Short.", " ".join(["ord"] * 20), "personal_trainer")
        assert result["passed"] is False
        assert any("no" in r and "length" in r.lower() for r in result["reasons"])

    def test_forbidden_phrase_en(self):
        result = cq.validate_candidate("Try this breathing exercise!", "Prøv dette!", "personal_trainer")
        assert result["passed"] is False
        assert any("forbidden" in r.lower() for r in result["reasons"])

    def test_empty_text(self):
        result = cq.validate_candidate("", "Noe.", "personal_trainer")
        assert result["passed"] is False

    def test_both_empty(self):
        result = cq.validate_candidate("", "", "personal_trainer")
        assert result["passed"] is False
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests_phaseb/test_candidate_queue.py::TestValidateCandidate -v`
Expected: FAIL — `AttributeError: module 'candidate_queue' has no attribute 'validate_candidate'`

**Step 3: Write minimal implementation**

Add to `candidate_queue.py`:

```python
# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_candidate(
    text_en: str,
    text_no: str,
    persona: str,
) -> Dict[str, object]:
    """
    Run validate_coaching_text() on both languages.
    Returns {"passed": bool, "reasons": [str]}.
    """
    from coaching_engine import validate_coaching_text

    reasons: List[str] = []

    if not text_en or not text_en.strip():
        reasons.append("en: empty text")
    elif not validate_coaching_text(text=text_en, persona=persona, language="en", mode="realtime"):
        reasons.append(f"en: failed validation (length/forbidden/tone)")

    if not text_no or not text_no.strip():
        reasons.append("no: empty text")
    elif not validate_coaching_text(text=text_no, persona=persona, language="no", mode="realtime"):
        reasons.append(f"no: failed validation (length/forbidden/tone)")

    return {"passed": len(reasons) == 0, "reasons": reasons}
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests_phaseb/test_candidate_queue.py -v`
Expected: All PASS (13 + 6 = 19)

**Step 5: Commit**

```bash
git add candidate_queue.py tests_phaseb/test_candidate_queue.py
git commit -m "feat: candidate_queue — validate_candidate using coaching_engine"
```

---

### Task 4: candidate_queue.py — next_variant_id + promote_to_catalog

**Files:**
- Modify: `candidate_queue.py`
- Modify: `tests_phaseb/test_candidate_queue.py`

**Step 1: Write the failing tests**

Append to `tests_phaseb/test_candidate_queue.py`:

```python
class TestNextVariantId:
    def test_empty_family(self):
        """No existing variants → .1"""
        result = cq.next_variant_id("nonexistent.family.s9")
        assert result == "nonexistent.family.s9.1"

    def test_increments(self):
        """interval.motivate.s2 has .1 and .2 in catalog → .3"""
        result = cq.next_variant_id("interval.motivate.s2")
        assert result == "interval.motivate.s2.3"

    def test_with_gaps(self):
        """If .1 and .3 exist, next is .4 (max+1, no gap fill)."""
        # We test this by mocking — create a catalog-like list
        # Use the _existing_variant_numbers helper
        nums = cq._existing_variant_numbers("interval.motivate.s2")
        assert 1 in nums
        assert 2 in nums
        # next_variant_id should return max+1
        result = cq.next_variant_id("interval.motivate.s2")
        expected_next = max(nums) + 1
        assert result == f"interval.motivate.s2.{expected_next}"

    def test_easy_run_family(self):
        result = cq.next_variant_id("easy_run.motivate.s1")
        assert result == "easy_run.motivate.s1.3"  # .1 and .2 exist


class TestPromoteToCatalog:
    def test_promote_assigns_correct_ids(self, tmp_path):
        """Approved candidates get next variant numbers."""
        candidates = [
            {
                "candidate_id": "cand_001",
                "status": "approved",
                "event_type": "interval_in_target_sustained",
                "phrase_family": "interval.motivate.s2",
                "generated_text_en": "Lock it in!",
                "generated_text_no": "Lås det inn!",
                "persona": "personal_trainer",
            },
        ]
        new_ids = cq.promote_to_catalog(candidates, dry_run=True)
        assert len(new_ids) == 1
        assert new_ids[0] == "interval.motivate.s2.3"

    def test_promote_updates_status(self, tmp_path):
        candidates = [
            {
                "candidate_id": "cand_001",
                "status": "approved",
                "event_type": "interval_in_target_sustained",
                "phrase_family": "interval.motivate.s2",
                "generated_text_en": "Lock it in!",
                "generated_text_no": "Lås det inn!",
                "persona": "personal_trainer",
            },
        ]
        cq.promote_to_catalog(candidates, dry_run=True)
        assert candidates[0]["status"] == "promoted"

    def test_promote_skips_non_approved(self):
        candidates = [
            {"candidate_id": "cand_001", "status": "pending", "phrase_family": "interval.motivate.s2"},
            {"candidate_id": "cand_002", "status": "rejected", "phrase_family": "interval.motivate.s2"},
        ]
        new_ids = cq.promote_to_catalog(candidates, dry_run=True)
        assert new_ids == []
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests_phaseb/test_candidate_queue.py::TestNextVariantId -v`
Expected: FAIL — `AttributeError: module 'candidate_queue' has no attribute 'next_variant_id'`

**Step 3: Write minimal implementation**

Add to `candidate_queue.py`:

```python
# ---------------------------------------------------------------------------
# Variant numbering
# ---------------------------------------------------------------------------

def _existing_variant_numbers(phrase_family: str) -> List[int]:
    """
    Find existing variant numbers for a phrase family in tts_phrase_catalog.py.
    E.g. family="interval.motivate.s2" → checks for "interval.motivate.s2.N" → returns [1, 2].
    """
    from tts_phrase_catalog import PHRASE_CATALOG

    prefix = phrase_family + "."
    numbers = []
    for entry in PHRASE_CATALOG:
        pid = entry["id"]
        if pid.startswith(prefix):
            suffix = pid[len(prefix):]
            try:
                numbers.append(int(suffix))
            except ValueError:
                pass
    return sorted(numbers)


def next_variant_id(phrase_family: str) -> str:
    """
    Compute the next variant ID for a phrase family.
    E.g. "interval.motivate.s2" with .1 and .2 existing → "interval.motivate.s2.3"
    """
    existing = _existing_variant_numbers(phrase_family)
    next_num = (max(existing) + 1) if existing else 1
    return f"{phrase_family}.{next_num}"


# ---------------------------------------------------------------------------
# Promote to catalog
# ---------------------------------------------------------------------------

def promote_to_catalog(
    candidates: List[dict],
    dry_run: bool = False,
) -> List[str]:
    """
    Promote approved candidates to tts_phrase_catalog.py.

    - Assigns next variant IDs
    - If dry_run=False, appends entries to PHRASE_CATALOG source file
    - Updates candidate status to "promoted"
    - Returns list of new phrase IDs assigned

    Args:
        candidates: The full queue (or subset). Only status=="approved" are promoted.
        dry_run: If True, compute IDs and update status but don't write to catalog file.

    Returns:
        List of newly assigned phrase IDs (e.g. ["interval.motivate.s2.3"]).
    """
    from tts_phrase_catalog import PHRASE_CATALOG

    approved = [c for c in candidates if c.get("status") == "approved"]
    if not approved:
        return []

    # Group by family to assign sequential IDs
    by_family: Dict[str, List[dict]] = {}
    for c in approved:
        family = c["phrase_family"]
        by_family.setdefault(family, []).append(c)

    new_ids: List[str] = []
    new_entries: List[dict] = []

    for family, family_candidates in by_family.items():
        existing_nums = _existing_variant_numbers(family)
        next_num = (max(existing_nums) + 1) if existing_nums else 1

        for c in family_candidates:
            new_id = f"{family}.{next_num}"
            new_ids.append(new_id)
            new_entries.append({
                "id": new_id,
                "en": c["generated_text_en"],
                "no": c["generated_text_no"],
                "persona": c.get("persona", "personal_trainer"),
                "priority": "core",
            })
            c["status"] = "promoted"
            c["promoted_as"] = new_id
            next_num += 1

    if not dry_run and new_entries:
        _append_to_catalog_source(new_entries)

    return new_ids


def _append_to_catalog_source(entries: List[dict]) -> None:
    """
    Append new phrase entries to tts_phrase_catalog.py source file.

    Inserts before the closing ']' of PHRASE_CATALOG.
    Uses the same source-editing approach as phrase_catalog_editor.py.
    """
    import json as _json

    source_path = Path(__file__).resolve().parent / "tts_phrase_catalog.py"
    source = source_path.read_text(encoding="utf-8")

    # Find the last entry line before the closing ']' of PHRASE_CATALOG
    # Strategy: find the last '},' or '}' line before the standalone ']'
    lines = source.split("\n")
    insert_idx = None
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped == "]":
            insert_idx = i
            break

    if insert_idx is None:
        raise RuntimeError("Could not find PHRASE_CATALOG closing bracket in tts_phrase_catalog.py")

    # Build new lines
    new_lines = []
    new_lines.append("")
    new_lines.append("    # --- Promoted from candidate queue ---")
    for entry in entries:
        en_json = _json.dumps(entry["en"], ensure_ascii=False)
        no_json = _json.dumps(entry["no"], ensure_ascii=False)
        line = (
            f'    {{"id": "{entry["id"]}", '
            f'"en": {en_json}, '
            f'"no": {no_json}, '
            f'"persona": "{entry["persona"]}", '
            f'"priority": "{entry["priority"]}"}}, '
        )
        new_lines.append(line)

    # Insert before the closing ']'
    for idx, new_line in enumerate(new_lines):
        lines.insert(insert_idx + idx, new_line)

    source_path.write_text("\n".join(lines), encoding="utf-8")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests_phaseb/test_candidate_queue.py -v`
Expected: All PASS (19 + 6 = 25)

**Step 5: Commit**

```bash
git add candidate_queue.py tests_phaseb/test_candidate_queue.py
git commit -m "feat: candidate_queue — next_variant_id + promote_to_catalog"
```

---

### Task 5: candidate_queue.py — make_candidate helper

**Files:**
- Modify: `candidate_queue.py`
- Modify: `tests_phaseb/test_candidate_queue.py`

**Step 1: Write the failing test**

Append to `tests_phaseb/test_candidate_queue.py`:

```python
class TestMakeCandidate:
    def test_creates_valid_structure(self):
        c = cq.make_candidate(
            event_type="interval_in_target_sustained",
            phrase_family="interval.motivate.s2",
            text_en="Push it!",
            text_no="Trykk til!",
            persona="personal_trainer",
            model="grok-3-mini",
            source="cli",
        )
        assert c["status"] == "pending"
        assert c["candidate_id"].startswith("cand_")
        assert c["event_type"] == "interval_in_target_sustained"
        assert c["phrase_family"] == "interval.motivate.s2"
        assert c["generated_text_en"] == "Push it!"
        assert c["generated_text_no"] == "Trykk til!"
        assert c["languages"] == ["en", "no"]
        assert c["model"] == "grok-3-mini"
        assert c["source"] == "cli"
        assert c["variant_key"]  # non-empty
        assert "passed" in c["validation"]
        assert c["context"]["session_id"] is None
        assert c["reviewed_at"] is None

    def test_duplicate_gets_skipped_status(self):
        c1 = cq.make_candidate(
            event_type="interval_in_target_sustained",
            phrase_family="interval.motivate.s2",
            text_en="Push it!",
            text_no="Trykk til!",
            persona="personal_trainer",
        )
        queue = [c1]
        c2 = cq.make_candidate(
            event_type="interval_in_target_sustained",
            phrase_family="interval.motivate.s2",
            text_en="Push it!",
            text_no="Trykk til!",
            persona="personal_trainer",
            existing_queue=queue,
        )
        assert c2["status"] == "skipped"

    def test_validation_failure_stored(self):
        long_text = " ".join(["word"] * 20)
        c = cq.make_candidate(
            event_type="interval_in_target_sustained",
            phrase_family="interval.motivate.s2",
            text_en=long_text,
            text_no="Kort.",
            persona="personal_trainer",
        )
        assert c["status"] == "pending"
        assert c["validation"]["passed"] is False
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests_phaseb/test_candidate_queue.py::TestMakeCandidate -v`
Expected: FAIL — `AttributeError: module 'candidate_queue' has no attribute 'make_candidate'`

**Step 3: Write minimal implementation**

Add to `candidate_queue.py`:

```python
# ---------------------------------------------------------------------------
# Candidate builder
# ---------------------------------------------------------------------------

def _generate_candidate_id() -> str:
    """Generate a unique candidate ID: cand_YYYYMMDD_HHMMSS_NNN."""
    now = datetime.now(timezone.utc)
    # Use microseconds for uniqueness within same second
    return f"cand_{now.strftime('%Y%m%d_%H%M%S')}_{now.microsecond // 1000:03d}"


def make_candidate(
    *,
    event_type: str,
    phrase_family: str,
    text_en: str,
    text_no: str,
    persona: str = "personal_trainer",
    model: str = CANDIDATE_MODEL_DEFAULT,
    model_params: Optional[dict] = None,
    source: str = "cli",
    context: Optional[dict] = None,
    existing_queue: Optional[List[dict]] = None,
) -> dict:
    """
    Build a candidate dict with validation and dedup.

    Returns a complete candidate dict ready to append to the queue.
    Status will be:
      - "skipped" if duplicate found in existing_queue
      - "pending" otherwise (validation result stored but doesn't change status)
    """
    variant_key = compute_variant_key(event_type, phrase_family, text_en, text_no, persona)

    # Dedup check
    if existing_queue and is_duplicate(variant_key, existing_queue):
        return {
            "candidate_id": _generate_candidate_id(),
            "status": "skipped",
            "event_type": event_type,
            "phrase_family": phrase_family,
            "generated_text_en": text_en,
            "generated_text_no": text_no,
            "languages": ["en", "no"],
            "model": model,
            "model_params": model_params or {"temperature": CANDIDATE_TEMPERATURE, "max_tokens": CANDIDATE_MAX_TOKENS},
            "persona": persona,
            "source": source,
            "variant_key": variant_key,
            "validation": {"passed": False, "reasons": ["duplicate"]},
            "context": context or {"phase": None, "intensity": None, "session_id": None, "heart_rate": None, "elapsed_seconds": None},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_at": None,
            "reviewer_note": None,
        }

    validation = validate_candidate(text_en, text_no, persona)

    return {
        "candidate_id": _generate_candidate_id(),
        "status": "pending",
        "event_type": event_type,
        "phrase_family": phrase_family,
        "generated_text_en": text_en,
        "generated_text_no": text_no,
        "languages": ["en", "no"],
        "model": model,
        "model_params": model_params or {"temperature": CANDIDATE_TEMPERATURE, "max_tokens": CANDIDATE_MAX_TOKENS},
        "persona": persona,
        "source": source,
        "variant_key": variant_key,
        "validation": validation,
        "context": context or {"phase": None, "intensity": None, "session_id": None, "heart_rate": None, "elapsed_seconds": None},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_at": None,
        "reviewer_note": None,
    }
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests_phaseb/test_candidate_queue.py -v`
Expected: All PASS (25 + 3 = 28)

**Step 5: Commit**

```bash
git add candidate_queue.py tests_phaseb/test_candidate_queue.py
git commit -m "feat: candidate_queue — make_candidate builder with dedup + validation"
```

---

### Task 6: candidate_queue.py — get_avoid_lists + infer_purpose_tag

**Files:**
- Modify: `candidate_queue.py`
- Modify: `tests_phaseb/test_candidate_queue.py`

**Step 1: Write the failing tests**

Append to `tests_phaseb/test_candidate_queue.py`:

```python
class TestAvoidLists:
    def test_catalog_variants_included(self):
        en_list, no_list = cq.get_avoid_lists("interval.motivate.s2", [])
        # interval.motivate.s2 has .1="Come on!" and .2="Lovely!" in catalog
        assert "Come on!" in en_list
        assert "Lovely!" in en_list
        assert "Kom igjen!" in no_list
        assert "Herlig!" in no_list

    def test_pending_queue_included(self):
        queue = [
            {"phrase_family": "interval.motivate.s2", "status": "pending",
             "generated_text_en": "New one!", "generated_text_no": "Ny en!"},
        ]
        en_list, no_list = cq.get_avoid_lists("interval.motivate.s2", queue)
        assert "New one!" in en_list
        assert "Ny en!" in no_list

    def test_other_family_excluded(self):
        queue = [
            {"phrase_family": "easy_run.motivate.s1", "status": "pending",
             "generated_text_en": "Different!", "generated_text_no": "Annerledes!"},
        ]
        en_list, no_list = cq.get_avoid_lists("interval.motivate.s2", queue)
        assert "Different!" not in en_list


class TestInferPurposeTag:
    def test_interval_motivate(self):
        assert cq.infer_purpose_tag("interval.motivate.s2") == "motivation_in_zone"

    def test_zone_above(self):
        assert cq.infer_purpose_tag("zone.above.default") == "hr_correction_above"

    def test_unknown_family(self):
        assert cq.infer_purpose_tag("unknown.family.x") == "coaching"  # default
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests_phaseb/test_candidate_queue.py::TestAvoidLists -v`
Expected: FAIL — `AttributeError`

**Step 3: Write minimal implementation**

Add to `candidate_queue.py`:

```python
# ---------------------------------------------------------------------------
# Avoid lists (for Grok prompt context)
# ---------------------------------------------------------------------------

def get_avoid_lists(
    phrase_family: str,
    queue: List[dict],
) -> Tuple[List[str], List[str]]:
    """
    Build EN and NO avoid lists from catalog + pending queue for a family.

    Returns (en_list, no_list) of texts Grok should not repeat.
    """
    from tts_phrase_catalog import PHRASE_CATALOG

    en_list: List[str] = []
    no_list: List[str] = []
    prefix = phrase_family + "."

    # From catalog
    for entry in PHRASE_CATALOG:
        if entry["id"].startswith(prefix) or entry["id"] == phrase_family:
            en_list.append(entry["en"])
            no_list.append(entry["no"])

    # From pending queue (same family, not skipped/rejected)
    for c in queue:
        if c.get("phrase_family") == phrase_family and c.get("status") in ("pending", "approved"):
            en_text = c.get("generated_text_en", "")
            no_text = c.get("generated_text_no", "")
            if en_text and en_text not in en_list:
                en_list.append(en_text)
            if no_text and no_text not in no_list:
                no_list.append(no_text)

    return en_list, no_list


def infer_purpose_tag(phrase_family: str) -> str:
    """Infer the purpose tag from a phrase family prefix. Falls back to 'coaching'."""
    for prefix, tag in PURPOSE_TAGS.items():
        if phrase_family.startswith(prefix):
            return tag
    return "coaching"
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests_phaseb/test_candidate_queue.py -v`
Expected: All PASS (28 + 6 = 34)

**Step 5: Commit**

```bash
git add candidate_queue.py tests_phaseb/test_candidate_queue.py
git commit -m "feat: candidate_queue — avoid lists + purpose tag inference"
```

---

### Task 7: candidate_queue.py — Norwegian tone examples loader

**Files:**
- Modify: `candidate_queue.py`
- Modify: `tests_phaseb/test_candidate_queue.py`

**Step 1: Write the failing test**

Append to `tests_phaseb/test_candidate_queue.py`:

```python
class TestNorwegianToneExamples:
    def test_good_examples_not_empty(self):
        good, bad = cq.get_norwegian_tone_examples()
        assert len(good) > 0
        # Should include values from norwegian_phrase_quality.py replacements
        assert "Mer press nå!" in good or "Bra jobba." in good

    def test_bad_examples_not_empty(self):
        good, bad = cq.get_norwegian_tone_examples()
        assert len(bad) > 0
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests_phaseb/test_candidate_queue.py::TestNorwegianToneExamples -v`
Expected: FAIL — `AttributeError`

**Step 3: Write minimal implementation**

Add to `candidate_queue.py`:

```python
# ---------------------------------------------------------------------------
# Norwegian tone reference (from norwegian_phrase_quality.py)
# ---------------------------------------------------------------------------

def get_norwegian_tone_examples() -> Tuple[List[str], List[str]]:
    """
    Read good/bad examples from norwegian_phrase_quality.py replacements dict.

    Returns (good_examples, bad_examples).
    Good = replacement values (right side). Bad = replacement keys (left side).
    """
    try:
        from norwegian_phrase_quality import rewrite_norwegian_phrase
        # Access the replacements dict directly from the module source
        import norwegian_phrase_quality as npq
        # The replacements dict is defined inside rewrite_norwegian_phrase().
        # We reconstruct it here by reading the known-good/known-bad pairs.
        # These are the hardcoded pairs from the module — keep in sync.
        _replacements = {
            "forsiktig, fortsett å varme opp": "Rolig, fortsett oppvarmingen.",
            "vakkert": "Bra jobba.",
            "gi meg mer kraft": "Mer press nå!",
            "trykk hardere": "Trykk litt hardere.",
            "jevn opp": "Finn jevn rytme.",
            "fin rytme, behold": "Bra tempo!",
            "holdt": "Fortsett!",
            "mer trykk nå": "Mer press nå!",
            "øk tempoet litt": "Øk tempoet.",
            "mer innsats, du klarer dette": "Mer innsats, du klarer det!",
            "hold deg i det": "Hold deg fokusert!",
            "du klarer dette": "Du klarer det!",
            "bra jobbet, hold jevnt": "Bra jobba! Hold jevnt tempo.",
        }
        good = list(dict.fromkeys(_replacements.values()))  # dedupe, preserve order
        bad = list(_replacements.keys())
        # Also add phase-guard examples
        good.extend(["Nå øker vi trykket.", "Senk tempoet rolig."])
        return good, bad
    except ImportError:
        return [], []
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests_phaseb/test_candidate_queue.py -v`
Expected: All PASS (34 + 2 = 36)

**Step 5: Commit**

```bash
git add candidate_queue.py tests_phaseb/test_candidate_queue.py
git commit -m "feat: candidate_queue — Norwegian tone examples loader"
```

---

### Task 8: tools/generate_candidates.py — CLI tool

**Files:**
- Create: `tools/generate_candidates.py`

**Step 1: Create the CLI tool**

Create `tools/generate_candidates.py`:

```python
#!/usr/bin/env python3
"""
Generate coaching phrase candidates via Grok API.

Usage:
  python3 tools/generate_candidates.py --family interval.motivate.s2 --count 5
  python3 tools/generate_candidates.py --all-motivation --count 3
  python3 tools/generate_candidates.py --event-type easy_run_in_target_sustained --count 4
  python3 tools/generate_candidates.py --family interval.motivate.s2 --count 3 --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import candidate_queue as cq
from norwegian_phrase_quality import rewrite_norwegian_phrase


def _build_en_prompt(purpose_tag: str, avoid_en: list[str], pending_en: list[str]) -> tuple[str, str]:
    """Build system + user prompts for English candidate generation."""
    avoid_block = "\n".join(f'- "{t}"' for t in avoid_en) if avoid_en else "- (none)"
    pending_block = "\n".join(f'- "{t}"' for t in pending_en) if pending_en else ""

    system = (
        f"You write short coaching cues for runners during interval workouts.\n"
        f"Persona: personal_trainer — calm, direct, elite endurance coach.\n"
        f"Purpose: {purpose_tag}\n\n"
        f"Rules:\n"
        f"- 2-8 words, one actionable or motivational cue\n"
        f"- No questions, no explanations\n"
        f"- Never mention breathing, apps, or AI\n"
        f"- Match the energy: confident, grounded, present-tense\n\n"
        f"Existing variants (DO NOT repeat these):\n{avoid_block}"
    )
    if pending_block:
        system += f"\n\nPending candidates (also avoid):\n{pending_block}"

    user = "Write ONE new variant. Output the cue only, nothing else."
    return system, user


def _build_no_prompt(
    purpose_tag: str,
    avoid_no: list[str],
    good_examples: list[str],
    bad_examples: list[str],
) -> tuple[str, str]:
    """Build system + user prompts for Norwegian candidate generation."""
    avoid_block = "\n".join(f'- "{t}"' for t in avoid_no) if avoid_no else "- (ingen)"
    good_block = "\n".join(f'- "{t}"' for t in good_examples[:8]) if good_examples else ""
    bad_block = "\n".join(f'- "{t}"' for t in bad_examples[:4]) if bad_examples else ""

    system = (
        f"Du skriver korte coachingfraser for løpere under intervalltrening.\n"
        f"Persona: personal_trainer — rolig, direkte, elite utholdenhetscoach.\n"
        f"Formål: {purpose_tag}\n\n"
        f"Regler:\n"
        f"- 2-8 ord, én handlings- eller motivasjonsfrase\n"
        f"- Ikke spørsmål, ikke forklaringer\n"
        f"- Aldri nevn pust, apper eller AI\n"
        f"- Naturlig norsk — IKKE oversatt engelsk\n"
        f"- Bruk æ, ø, å korrekt\n"
    )
    if good_block:
        system += f"\nTonefølelse — dette er den riktige stilen:\n{good_block}\n"
    if bad_block:
        system += f"\nUNNGÅ denne typen (oversatt/stivt norsk):\n{bad_block}\n"
    system += f"\nEksisterende varianter (IKKE gjenta disse):\n{avoid_block}"

    user = "Skriv ÉN ny variant. Kun frasen, ingenting annet."
    return system, user


def _call_grok(system_prompt: str, user_prompt: str, dry_run: bool = False) -> str:
    """Call Grok API. Returns generated text (stripped). In dry_run mode returns placeholder."""
    if dry_run:
        return "[dry-run placeholder]"

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ.get("XAI_API_KEY", ""),
            base_url="https://api.x.ai/v1",
        )
        response = client.chat.completions.create(
            model=cq.CANDIDATE_MODEL_DEFAULT,
            max_tokens=cq.CANDIDATE_MAX_TOKENS,
            temperature=cq.CANDIDATE_TEMPERATURE,
            timeout=cq.CANDIDATE_TIMEOUT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = response.choices[0].message.content.strip()
        # Take first sentence only
        import re
        parts = re.split(r'(?<=[.!?])\s+', text)
        if parts:
            text = parts[0]
        # Strip surrounding quotes if Grok wraps the cue
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        return text
    except Exception as e:
        print(f"  ⚠️  Grok API error: {e}")
        return ""


def _resolve_families(args) -> list[str]:
    """Resolve CLI args to a list of phrase families."""
    if args.all_motivation:
        return list(cq.ALL_MOTIVATION_FAMILIES)
    if args.event_type:
        families = cq.EVENT_TO_FAMILIES.get(args.event_type, [])
        if not families:
            print(f"Unknown event type: {args.event_type}")
            print(f"Known: {', '.join(cq.EVENT_TO_FAMILIES.keys())}")
            sys.exit(1)
        return families
    if args.family:
        return [args.family]
    print("Must specify --family, --event-type, or --all-motivation")
    sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate coaching phrase candidates via Grok.")
    parser.add_argument("--family", help="Target phrase family (e.g. interval.motivate.s2)")
    parser.add_argument("--event-type", help="Event type (infers families)")
    parser.add_argument("--all-motivation", action="store_true", help="Generate for all motivation families")
    parser.add_argument("--count", type=int, default=3, help="Candidates per family (default: 3)")
    parser.add_argument("--persona", default="personal_trainer", help="Persona (default: personal_trainer)")
    parser.add_argument("--dry-run", action="store_true", help="Skip Grok API calls, use placeholders")
    args = parser.parse_args()

    families = _resolve_families(args)
    count_per_family = min(args.count, cq.MAX_PER_FAMILY_PER_RUN)

    queue = cq.load_queue()
    good_no, bad_no = cq.get_norwegian_tone_examples()

    total_generated = 0
    total_skipped = 0
    total_failed = 0

    print(f"Generating {count_per_family} candidates x {len(families)} families")
    print(f"Queue has {len(queue)} existing entries")
    print()

    for family in families:
        if total_generated >= cq.MAX_TOTAL_PER_RUN:
            print(f"Hit MAX_TOTAL_PER_RUN ({cq.MAX_TOTAL_PER_RUN}), stopping.")
            break

        purpose_tag = cq.infer_purpose_tag(family)
        # Determine event_type from family
        event_type = ""
        for et, fams in cq.EVENT_TO_FAMILIES.items():
            if family in fams:
                event_type = et
                break

        print(f"── {family} ({purpose_tag}) ──")

        family_count = 0
        for i in range(count_per_family):
            if total_generated >= cq.MAX_TOTAL_PER_RUN:
                break

            # Build avoid lists fresh (includes previously generated this run)
            avoid_en, avoid_no = cq.get_avoid_lists(family, queue)

            # Generate EN
            sys_en, usr_en = _build_en_prompt(purpose_tag, avoid_en, [])
            text_en = _call_grok(sys_en, usr_en, dry_run=args.dry_run)

            # Generate NO
            sys_no, usr_no = _build_no_prompt(purpose_tag, avoid_no, good_no, bad_no)
            text_no = _call_grok(sys_no, usr_no, dry_run=args.dry_run)

            # Norwegian post-processing
            if text_no and not args.dry_run:
                text_no = rewrite_norwegian_phrase(text_no)

            if not text_en and not text_no:
                print(f"  [{i+1}] ⚠️  Both empty, skipping")
                total_failed += 1
                continue

            candidate = cq.make_candidate(
                event_type=event_type,
                phrase_family=family,
                text_en=text_en,
                text_no=text_no,
                persona=args.persona,
                source="cli",
                existing_queue=queue,
            )

            queue.append(candidate)

            status = candidate["status"]
            valid = candidate["validation"]["passed"]
            if status == "skipped":
                print(f"  [{i+1}] SKIP (duplicate)")
                total_skipped += 1
            elif not valid:
                reasons = ", ".join(candidate["validation"]["reasons"])
                print(f"  [{i+1}] WARN en=\"{text_en}\" no=\"{text_no}\" ({reasons})")
                total_generated += 1
                family_count += 1
            else:
                print(f"  [{i+1}] OK   en=\"{text_en}\" no=\"{text_no}\"")
                total_generated += 1
                family_count += 1

            # Small delay between API calls
            if not args.dry_run:
                time.sleep(0.5)

    # Save
    cq.save_queue(queue)
    print()
    print(f"Done. Generated: {total_generated}, Skipped: {total_skipped}, Failed: {total_failed}")
    print(f"Queue now has {len(queue)} entries. Saved to {cq.QUEUE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 2: Test with dry run**

Run: `python3 tools/generate_candidates.py --family interval.motivate.s2 --count 2 --dry-run`

Expected output:
```
Generating 2 candidates x 1 families
Queue has 0 existing entries

── interval.motivate.s2 (motivation_in_zone) ──
  [1] WARN en="[dry-run placeholder]" no="[dry-run placeholder]" (...)
  [2] SKIP (duplicate)

Done. Generated: 1, Skipped: 1, Failed: 0
Queue now has 2 entries. Saved to output/candidate_queue.json
```

**Step 3: Verify queue file was created**

Run: `python3 -c "import json; print(json.dumps(json.load(open('output/candidate_queue.json')), indent=2)[:500])"`

Expected: JSON with candidate entries.

**Step 4: Commit**

```bash
git add tools/generate_candidates.py
git commit -m "feat: generate_candidates.py — CLI tool for Grok candidate generation"
```

---

### Task 9: tools/candidate_review.py — list + approve + reject + approve-valid

**Files:**
- Create: `tools/candidate_review.py`

**Step 1: Create the review CLI tool (core commands)**

Create `tools/candidate_review.py`:

```python
#!/usr/bin/env python3
"""
Review and manage candidate queue.

Usage:
  python3 tools/candidate_review.py list
  python3 tools/candidate_review.py list --status pending
  python3 tools/candidate_review.py approve cand_001 cand_002
  python3 tools/candidate_review.py reject cand_001 --note "too generic"
  python3 tools/candidate_review.py approve-valid
  python3 tools/candidate_review.py export --format xlsx
  python3 tools/candidate_review.py import --xlsx output/candidate_review.xlsx
  python3 tools/candidate_review.py promote --dry-run
  python3 tools/candidate_review.py promote --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import candidate_queue as cq


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def cmd_list(args) -> int:
    queue = cq.load_queue()
    if args.status:
        queue = [c for c in queue if c.get("status") == args.status]

    if not queue:
        print("No candidates found.")
        return 0

    # Table header
    print(f"{'ID':<32} {'Status':<10} {'Family':<26} {'Valid':<6} {'EN':<30} {'NO':<30}")
    print("-" * 136)
    for c in queue:
        cid = c.get("candidate_id", "?")[:30]
        status = c.get("status", "?")
        family = c.get("phrase_family", "?")[:24]
        valid = "✓" if c.get("validation", {}).get("passed") else "✗"
        en = c.get("generated_text_en", "")[:28]
        no = c.get("generated_text_no", "")[:28]
        print(f"{cid:<32} {status:<10} {family:<26} {valid:<6} {en:<30} {no:<30}")

    # Summary
    by_status = {}
    for c in cq.load_queue():
        s = c.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
    print()
    print(f"Total: {sum(by_status.values())} | " + " | ".join(f"{k}: {v}" for k, v in sorted(by_status.items())))
    return 0


# ---------------------------------------------------------------------------
# approve / reject
# ---------------------------------------------------------------------------

def cmd_approve(args) -> int:
    queue = cq.load_queue()
    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for c in queue:
        if c.get("candidate_id") in args.candidate_ids:
            if c.get("status") == "pending":
                c["status"] = "approved"
                c["reviewed_at"] = now
                count += 1
            else:
                print(f"  Skip {c['candidate_id']} — status is '{c['status']}', not 'pending'")
    cq.save_queue(queue)
    print(f"Approved {count} candidates.")
    return 0


def cmd_reject(args) -> int:
    queue = cq.load_queue()
    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for c in queue:
        if c.get("candidate_id") in args.candidate_ids:
            if c.get("status") == "pending":
                c["status"] = "rejected"
                c["reviewed_at"] = now
                c["reviewer_note"] = args.note or None
                count += 1
            else:
                print(f"  Skip {c['candidate_id']} — status is '{c['status']}', not 'pending'")
    cq.save_queue(queue)
    print(f"Rejected {count} candidates.")
    return 0


def cmd_approve_valid(args) -> int:
    queue = cq.load_queue()
    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for c in queue:
        if c.get("status") == "pending" and c.get("validation", {}).get("passed"):
            c["status"] = "approved"
            c["reviewed_at"] = now
            count += 1
    cq.save_queue(queue)
    print(f"Approved {count} valid pending candidates.")
    return 0


# ---------------------------------------------------------------------------
# promote
# ---------------------------------------------------------------------------

def cmd_promote(args) -> int:
    queue = cq.load_queue()
    approved = [c for c in queue if c.get("status") == "approved"]
    if not approved:
        print("No approved candidates to promote.")
        return 0

    print(f"Promoting {len(approved)} approved candidates:")
    for c in approved:
        print(f"  {c['phrase_family']} — en=\"{c['generated_text_en']}\" no=\"{c['generated_text_no']}\"")

    new_ids = cq.promote_to_catalog(queue, dry_run=not args.apply)
    if new_ids:
        print()
        print("New phrase IDs assigned:")
        for pid in new_ids:
            print(f"  {pid}")

    if args.apply:
        cq.save_queue(queue)
        print(f"\nPromoted and saved. Run next:")
        print(f"  python3 tools/generate_audio_pack.py --version v1 --upload")
    else:
        print(f"\nDry run. Re-run with --apply to write to tts_phrase_catalog.py.")
    return 0


# ---------------------------------------------------------------------------
# export XLSX
# ---------------------------------------------------------------------------

REVIEW_COLUMNS = ["candidate_id", "status", "phrase_family", "en", "no", "validation", "model", "reviewer_note"]
REVIEW_COL_WIDTHS = [34.0, 14.0, 28.0, 44.0, 44.0, 34.0, 16.0, 30.0]


def _xml_text(value: str) -> str:
    return escape(value).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "&#10;")


def _col_label(idx: int) -> str:
    out = ""
    current = idx
    while current > 0:
        current, rem = divmod(current - 1, 26)
        out = chr(65 + rem) + out
    return out


def _cell_ref(col_idx: int, row_idx: int) -> str:
    return f"{_col_label(col_idx)}{row_idx}"


def _cell_inline(col_idx: int, row_idx: int, value: str, style: int) -> str:
    ref = _cell_ref(col_idx, row_idx)
    return (
        f'<c r="{ref}" s="{style}" t="inlineStr">'
        f'<is><t xml:space="preserve">{_xml_text(value)}</t></is></c>'
    )


def cmd_export(args) -> int:
    queue = cq.load_queue()
    if not queue:
        print("Queue is empty.")
        return 0

    # Filter to pending only for review export
    pending = [c for c in queue if c.get("status") == "pending"]
    if not pending:
        print("No pending candidates to export.")
        return 0

    output_dir = Path(PROJECT_ROOT) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = output_dir / "candidate_review.xlsx"

    # Build sheet XML
    sheet_rows = []
    header_cells = "".join(_cell_inline(i, 1, col, 1) for i, col in enumerate(REVIEW_COLUMNS, start=1))
    sheet_rows.append(f'<row r="1" ht="24" customHeight="1">{header_cells}</row>')

    for excel_row, c in enumerate(pending, start=2):
        validation_str = ""
        v = c.get("validation", {})
        if v.get("passed"):
            validation_str = "PASS"
        else:
            validation_str = "FAIL: " + "; ".join(v.get("reasons", []))

        cells = [
            _cell_inline(1, excel_row, c.get("candidate_id", ""), 0),
            _cell_inline(2, excel_row, c.get("status", ""), 0),
            _cell_inline(3, excel_row, c.get("phrase_family", ""), 0),
            _cell_inline(4, excel_row, c.get("generated_text_en", ""), 0),
            _cell_inline(5, excel_row, c.get("generated_text_no", ""), 0),
            _cell_inline(6, excel_row, validation_str, 0),
            _cell_inline(7, excel_row, c.get("model", ""), 0),
            _cell_inline(8, excel_row, c.get("reviewer_note", "") or "", 0),
        ]
        sheet_rows.append(f'<row r="{excel_row}">{"".join(cells)}</row>')

    last_row = max(2, len(pending) + 1)
    cols_xml = "".join(
        f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>'
        for i, w in enumerate(REVIEW_COL_WIDTHS, start=1)
    )
    max_ref = _cell_ref(len(REVIEW_COLUMNS), last_row)

    # Data validation: status column (B) can be pending/approved/rejected
    data_val = (
        f'<dataValidations count="1"><dataValidation type="list" allowBlank="1" '
        f'showErrorMessage="1" sqref="B2:B{last_row}">'
        f'<formula1>"pending,approved,rejected"</formula1>'
        f"</dataValidation></dataValidations>"
    )

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{max_ref}"/>'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        '<sheetFormatPr defaultRowHeight="20"/>'
        f"<cols>{cols_xml}</cols>"
        f"<sheetData>{''.join(sheet_rows)}</sheetData>"
        f'<autoFilter ref="A1:{max_ref}"/>'
        f"{data_val}"
        "</worksheet>"
    )

    # Minimal XLSX with one sheet
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2">'
        '<font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>'
        '</fonts>'
        '<fills count="3">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/></patternFill></fill>'
        '</fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1">'
        '<alignment horizontal="center" wrapText="1"/></xf>'
        '</cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Candidates" sheetId="1" r:id="rId1"/></sheets>'
        '<calcPr calcId="0" fullCalcOnLoad="1"/>'
        '</workbook>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    pkg_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )

    with zipfile.ZipFile(xlsx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", pkg_rels)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/styles.xml", styles_xml)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)

    print(f"Exported {len(pending)} pending candidates to {xlsx_path}")
    print("Edit the 'status' column (pending → approved/rejected) and 'reviewer_note', then import.")
    return 0


# ---------------------------------------------------------------------------
# import XLSX
# ---------------------------------------------------------------------------

_XLSX_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _col_index(ref: str) -> int:
    col = 0
    for ch in ref:
        if ch.isalpha():
            col = col * 26 + (ord(ch.upper()) - 64)
        else:
            break
    return col


def _cell_text_el(cell: ET.Element) -> str:
    is_el = cell.find(f"{{{_XLSX_NS}}}is")
    if is_el is not None:
        t_el = is_el.find(f"{{{_XLSX_NS}}}t")
        if t_el is not None and t_el.text:
            return t_el.text
    v_el = cell.find(f"{{{_XLSX_NS}}}v")
    if v_el is not None and v_el.text:
        return v_el.text
    return ""


def cmd_import(args) -> int:
    xlsx_path = Path(args.xlsx)
    if not xlsx_path.is_absolute():
        xlsx_path = Path(PROJECT_ROOT) / xlsx_path
    if not xlsx_path.exists():
        print(f"File not found: {xlsx_path}")
        return 2

    # Read XLSX
    with zipfile.ZipFile(xlsx_path, "r") as zf:
        sheet_xml = zf.read("xl/worksheets/sheet1.xml")

    root = ET.fromstring(sheet_xml)
    xlsx_rows: list[dict] = []
    for row_el in root.iter(f"{{{_XLSX_NS}}}row"):
        if row_el.get("r") == "1":
            continue
        cells: dict[int, str] = {}
        for cell_el in row_el.iter(f"{{{_XLSX_NS}}}c"):
            ref = cell_el.get("r", "")
            col = _col_index(ref)
            cells[col] = _cell_text_el(cell_el)
        cid = cells.get(1, "").strip()     # A = candidate_id
        status = cells.get(2, "").strip()  # B = status
        note = cells.get(8, "").strip()    # H = reviewer_note
        if cid:
            xlsx_rows.append({"candidate_id": cid, "status": status, "reviewer_note": note})

    # Apply to queue
    queue = cq.load_queue()
    now = datetime.now(timezone.utc).isoformat()
    changes = 0
    for xlsx_row in xlsx_rows:
        for c in queue:
            if c.get("candidate_id") == xlsx_row["candidate_id"]:
                new_status = xlsx_row["status"]
                if new_status in ("approved", "rejected") and c.get("status") == "pending":
                    c["status"] = new_status
                    c["reviewed_at"] = now
                    if xlsx_row["reviewer_note"]:
                        c["reviewer_note"] = xlsx_row["reviewer_note"]
                    changes += 1
                break

    cq.save_queue(queue)
    print(f"Imported {len(xlsx_rows)} rows, applied {changes} status changes.")
    return 0


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review and manage candidate queue.")
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List candidates")
    list_cmd.add_argument("--status", help="Filter by status (pending/approved/rejected/promoted/skipped)")

    approve_cmd = sub.add_parser("approve", help="Approve specific candidates")
    approve_cmd.add_argument("candidate_ids", nargs="+", help="Candidate IDs to approve")

    reject_cmd = sub.add_parser("reject", help="Reject specific candidates")
    reject_cmd.add_argument("candidate_ids", nargs="+", help="Candidate IDs to reject")
    reject_cmd.add_argument("--note", help="Rejection reason")

    sub.add_parser("approve-valid", help="Approve all pending candidates that passed validation")

    export_cmd = sub.add_parser("export", help="Export pending candidates to XLSX for review")
    export_cmd.add_argument("--format", default="xlsx", choices=["xlsx"], help="Export format")

    import_cmd = sub.add_parser("import", help="Import reviewed XLSX back")
    import_cmd.add_argument("--xlsx", required=True, help="Path to reviewed XLSX file")

    promote_cmd = sub.add_parser("promote", help="Promote approved candidates to tts_phrase_catalog.py")
    promote_cmd.add_argument("--apply", action="store_true", help="Actually write to catalog (default: dry run)")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    dispatch = {
        "list": cmd_list,
        "approve": cmd_approve,
        "reject": cmd_reject,
        "approve-valid": cmd_approve_valid,
        "export": cmd_export,
        "import": cmd_import,
        "promote": cmd_promote,
    }
    handler = dispatch.get(args.command)
    if handler:
        return handler(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 2: Smoke test the CLI**

First create a test queue with the generate tool:

Run: `python3 tools/generate_candidates.py --family interval.motivate.s2 --count 2 --dry-run`

Then test review commands:

Run: `python3 tools/candidate_review.py list`
Expected: Table showing the 2 dry-run candidates.

Run: `python3 tools/candidate_review.py export --format xlsx`
Expected: `Exported N pending candidates to output/candidate_review.xlsx`

Run: `python3 tools/candidate_review.py promote --dry-run`
Expected: `No approved candidates to promote.` (none approved yet)

**Step 3: Commit**

```bash
git add tools/candidate_review.py
git commit -m "feat: candidate_review.py — list/approve/reject/export/import/promote CLI"
```

---

### Task 10: .gitignore update + compile check + full test run

**Files:**
- Modify: `.gitignore`

**Step 1: Add queue file to .gitignore**

Append to `.gitignore` after the audio pack section:

```
# Candidate queue (ephemeral working state)
output/candidate_queue.json
output/candidate_review.xlsx
```

**Step 2: Compile check all new files**

Run: `python3 -m py_compile candidate_queue.py && python3 -m py_compile tools/generate_candidates.py && python3 -m py_compile tools/candidate_review.py && echo "All compile OK"`
Expected: `All compile OK`

**Step 3: Run all candidate queue tests**

Run: `pytest tests_phaseb/test_candidate_queue.py -v`
Expected: All 36 tests PASS

**Step 4: Run full test suite to verify no regressions**

Run: `pytest tests_phaseb/ -q --tb=no`
Expected: No new failures introduced.

**Step 5: Clean up any dry-run queue files**

Run: `rm -f output/candidate_queue.json output/candidate_review.xlsx`

**Step 6: Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore candidate queue ephemeral files + compile check"
```

---

## Verification Checklist

After all tasks complete:

```bash
# 1. All tests pass
pytest tests_phaseb/test_candidate_queue.py -v

# 2. All files compile
python3 -m py_compile candidate_queue.py tools/generate_candidates.py tools/candidate_review.py

# 3. CLI tools have --help
python3 tools/generate_candidates.py --help
python3 tools/candidate_review.py --help

# 4. Dry-run end-to-end
python3 tools/generate_candidates.py --family interval.motivate.s2 --count 3 --dry-run
python3 tools/candidate_review.py list
python3 tools/candidate_review.py approve-valid
python3 tools/candidate_review.py promote --dry-run

# 5. No runtime changes
python3 -m py_compile main.py config.py brain_router.py
```
