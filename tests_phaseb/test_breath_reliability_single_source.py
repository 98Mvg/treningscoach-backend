import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import breath_analyzer as breath_analyzer_module
from breath_analyzer import BreathAnalyzer
from breath_reliability import derive_breath_quality_samples, summarize_breath_quality


def test_breath_analyzer_does_not_own_countdown_or_zone_event_scheduling():
    source = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "breath_analyzer.py")).read_text()
    lowered = source.lower()
    forbidden_tokens = (
        "interval_countdown_",
        "warmup_countdown",
        "countdown_fired_map",
        "evaluate_zone_tick(",
    )
    for token in forbidden_tokens:
        assert token not in lowered, f"breath_analyzer must remain audio-only; found scheduling token: {token}"


def test_derive_breath_quality_samples_normalizes_and_includes_current_signal():
    samples = derive_breath_quality_samples(
        breath_data={"signal_quality": 1.3},
        recent_samples=[0.2, "0.6", None, "-1"],
        include_current_signal=True,
    )
    assert samples == [0.2, 0.6, 0.0, 1.0]


def test_summarize_breath_quality_reliable_uses_shared_thresholds():
    summary = summarize_breath_quality(
        breath_data={"signal_quality": 0.9},
        recent_samples=[0.8, 0.85, 0.82, 0.88, 0.86],
        config_module=config,
    )
    assert summary["sample_count"] >= int(getattr(config, "CS_BREATH_MIN_RELIABLE_SAMPLES", 6))
    assert summary["reliable"] is True
    assert summary["quality_state"] == "reliable"


def test_summarize_breath_quality_degraded_when_signal_exists_but_not_reliable():
    summary = summarize_breath_quality(
        breath_data={"signal_quality": 0.23},
        recent_samples=[0.2, 0.21, 0.19],
        config_module=config,
    )
    assert summary["reliable"] is False
    assert summary["quality_state"] == "degraded"


def test_mfcc_extraction_is_skipped_when_disabled(monkeypatch):
    analyzer = BreathAnalyzer(sample_rate=16000, enable_mfcc=False)
    called = {"mfcc": 0}

    class _StubFeature:
        @staticmethod
        def rms(**kwargs):
            return np.zeros((1, 10), dtype=np.float32)

        @staticmethod
        def spectral_centroid(**kwargs):
            return np.zeros((1, 10), dtype=np.float32)

        @staticmethod
        def zero_crossing_rate(*args, **kwargs):
            return np.zeros((1, 10), dtype=np.float32)

        @staticmethod
        def spectral_rolloff(**kwargs):
            return np.zeros((1, 10), dtype=np.float32)

        @staticmethod
        def mfcc(**kwargs):
            called["mfcc"] += 1
            raise AssertionError("MFCC should be disabled")

    monkeypatch.setattr(breath_analyzer_module.librosa, "feature", _StubFeature, raising=False)

    def _mfcc_should_not_run(*args, **kwargs):
        called["mfcc"] += 1
        raise AssertionError("MFCC should be disabled")

    monkeypatch.setattr(analyzer, "_compute_mfcc", _mfcc_should_not_run)
    features = analyzer._extract_features(np.zeros(16000, dtype=np.float32))
    assert features["mfcc"] is None
    assert called["mfcc"] == 0


def test_mfcc_extraction_runs_when_enabled(monkeypatch):
    analyzer = BreathAnalyzer(sample_rate=16000, enable_mfcc=True)
    called = {"mfcc": 0}

    class _StubFeature:
        @staticmethod
        def rms(**kwargs):
            return np.zeros((1, 10), dtype=np.float32)

        @staticmethod
        def spectral_centroid(**kwargs):
            return np.zeros((1, 10), dtype=np.float32)

        @staticmethod
        def zero_crossing_rate(*args, **kwargs):
            return np.zeros((1, 10), dtype=np.float32)

        @staticmethod
        def spectral_rolloff(**kwargs):
            return np.zeros((1, 10), dtype=np.float32)

        @staticmethod
        def mfcc(**kwargs):
            return np.zeros((13, 10), dtype=np.float32)

    monkeypatch.setattr(breath_analyzer_module.librosa, "feature", _StubFeature, raising=False)

    def _fake_mfcc(*args, **kwargs):
        called["mfcc"] += 1
        return np.zeros((13, 10), dtype=np.float32)

    monkeypatch.setattr(analyzer, "_compute_mfcc", _fake_mfcc)
    features = analyzer._extract_features(np.zeros(16000, dtype=np.float32))
    assert features["mfcc"] is not None
    assert called["mfcc"] == 1
