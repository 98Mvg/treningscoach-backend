import os
import sys
import importlib
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import norwegian_phrase_quality as npq
from norwegian_phrase_quality import rewrite_norwegian_phrase


def test_rewrite_known_awkward_lines():
    assert rewrite_norwegian_phrase("Vakkert.", phase="intense") == "Bra jobba."
    assert rewrite_norwegian_phrase("Gi meg mer kraft!", phase="intense") == "Mer trykk nå!"
    assert rewrite_norwegian_phrase("Trykk hardere.", phase="intense") == "Press hardere."
    assert rewrite_norwegian_phrase("Jevn opp.", phase="intense") == "Finn jevn rytme."
    assert rewrite_norwegian_phrase("Fin rytme, behold!", phase="intense") == "Bra tempo!"
    assert rewrite_norwegian_phrase("Holdt.", phase="intense") == "Fortsett!"


def test_phase_guard_rewrites_warmup_wording_in_intense():
    assert rewrite_norwegian_phrase("Forsiktig, fortsett å varme opp.", phase="intense") == "Nå øker vi trykket."


def test_phase_guard_rewrites_warmup_wording_in_cooldown():
    assert rewrite_norwegian_phrase("Fortsett oppvarming.", phase="cooldown") == "Senk tempoet rolig."


def test_unmatched_phrase_passes_through():
    phrase = "Hold rytmen."
    assert rewrite_norwegian_phrase(phrase, phase="intense") == phrase


def test_custom_banlist_override_is_applied(monkeypatch, tmp_path):
    banlist = tmp_path / "no_banlist.json"
    banlist.write_text(
        json.dumps({"exact_rewrites": {"holdt": "Kjør på videre!"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setenv("NORWEGIAN_BANLIST_PATH", str(banlist))
    importlib.reload(npq)

    assert npq.rewrite_norwegian_phrase("Holdt.", phase="intense") == "Kjør på videre!"
