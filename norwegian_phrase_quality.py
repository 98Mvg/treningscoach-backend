"""
Norwegian phrasing quality guard for short coaching cues.

This module keeps rewrite rules separate from endpoint logic so wording can
be tuned quickly without touching request handlers.
"""

import json
import os
from typing import Optional


_CUSTOM_REWRITE_CACHE = {
    "path": None,
    "mtime": None,
    "rewrites": {},
}


def _normalize_key(value: str) -> str:
    return " ".join((value or "").strip().split()).lower().rstrip("!.")


def _load_custom_rewrites() -> dict:
    """
    Load custom rewrites from JSON banlist.

    Format:
    {
      "exact_rewrites": {
        "bad phrase": "better phrase"
      }
    }
    """
    path = os.getenv(
        "NORWEGIAN_BANLIST_PATH",
        os.path.join(os.path.dirname(__file__), "norwegian_phrase_banlist.json"),
    )

    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = None

    if (
        _CUSTOM_REWRITE_CACHE["path"] == path
        and _CUSTOM_REWRITE_CACHE["mtime"] == mtime
    ):
        return _CUSTOM_REWRITE_CACHE["rewrites"]

    rewrites = {}
    if mtime is not None:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            raw_map = payload.get("exact_rewrites", {}) if isinstance(payload, dict) else {}
            if isinstance(raw_map, dict):
                for bad, good in raw_map.items():
                    key = _normalize_key(str(bad))
                    val = str(good).strip()
                    if key and val:
                        rewrites[key] = val
        except Exception:
            rewrites = {}

    _CUSTOM_REWRITE_CACHE["path"] = path
    _CUSTOM_REWRITE_CACHE["mtime"] = mtime
    _CUSTOM_REWRITE_CACHE["rewrites"] = rewrites
    return rewrites


def rewrite_norwegian_phrase(text: str, phase: Optional[str] = None) -> str:
    """
    Rewrite known awkward Norwegian lines to more natural coaching phrasing.

    Args:
        text: Candidate coach line in Norwegian.
        phase: Optional workout phase ("warmup", "intense", "cooldown").

    Returns:
        Corrected phrase when a rule matches, otherwise normalized input text.
    """
    if not text:
        return text

    normalized_phase = (phase or "").strip().lower()
    stripped = " ".join(text.strip().split())
    lowered = _normalize_key(stripped)

    # Phase guard: never use warmup framing in intense/cooldown.
    if normalized_phase and normalized_phase != "warmup":
        if "varme opp" in lowered or "oppvarming" in lowered:
            if normalized_phase == "intense":
                return "Nå øker vi trykket."
            if normalized_phase == "cooldown":
                return "Senk tempoet rolig."

    replacements = {
        "forsiktig, fortsett å varme opp": "Rolig, fortsett oppvarmingen.",
        "vakkert": "Bra jobba.",
        "gi meg mer kraft": "Mer trykk nå!",
        "trykk hardere": "Press hardere.",
        "jevn opp": "Finn jevn rytme.",
        "fin rytme, behold": "Bra tempo!",
        "holdt": "Fortsett!",
    }
    custom_rewrites = _load_custom_rewrites()
    if lowered in custom_rewrites:
        return custom_rewrites[lowered]
    return replacements.get(lowered, stripped)
