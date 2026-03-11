import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tts_phrase_catalog import validate_welcome_catalog


def test_current_welcome_catalog_is_valid():
    errors = validate_welcome_catalog()
    assert errors == []


def test_empty_welcome_catalog_is_valid():
    assert validate_welcome_catalog([]) == []


def test_welcome_validation_detects_non_contiguous_group():
    sample = [
        {
            "id": "welcome.standard.1",
            "en": "Hello one.",
            "no": "Hei en.",
            "persona": "personal_trainer",
            "priority": "core",
        },
        {
            "id": "welcome.standard.3",
            "en": "Hello three.",
            "no": "Hei tre.",
            "persona": "personal_trainer",
            "priority": "core",
        },
    ]
    errors = validate_welcome_catalog(sample)
    assert any("Non-contiguous numbering in welcome.standard" in err for err in errors)
