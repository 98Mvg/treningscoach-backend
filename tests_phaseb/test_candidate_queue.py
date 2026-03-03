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


# --- Task 2: variant_key + dedup ---

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


# --- Task 3: validate_candidate ---

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


# --- Task 4: next_variant_id + promote ---

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
        """Verify _existing_variant_numbers returns actual numbers."""
        nums = cq._existing_variant_numbers("interval.motivate.s2")
        assert 1 in nums
        assert 2 in nums
        result = cq.next_variant_id("interval.motivate.s2")
        expected_next = max(nums) + 1
        assert result == f"interval.motivate.s2.{expected_next}"

    def test_easy_run_family(self):
        result = cq.next_variant_id("easy_run.motivate.s1")
        assert result == "easy_run.motivate.s1.3"  # .1 and .2 exist


class TestPromoteToCatalog:
    def test_promote_assigns_correct_ids(self):
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

    def test_promote_updates_status(self):
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


# --- Task 5: make_candidate ---

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


# --- Task 6: avoid lists + purpose tag ---

class TestAvoidLists:
    def test_catalog_variants_included(self):
        en_list, no_list = cq.get_avoid_lists("interval.motivate.s2", [])
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


# --- Task 7: Norwegian tone examples ---

class TestNorwegianToneExamples:
    def test_good_examples_not_empty(self):
        good, bad = cq.get_norwegian_tone_examples()
        assert len(good) > 0
        assert "Mer press nå!" in good or "Bra jobba." in good

    def test_bad_examples_not_empty(self):
        good, bad = cq.get_norwegian_tone_examples()
        assert len(bad) > 0
