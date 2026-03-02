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
