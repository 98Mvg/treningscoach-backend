"""
Norwegian phrasing quality guard for short coaching cues.

This module keeps rewrite rules separate from endpoint logic so wording can
be tuned quickly without touching request handlers.
"""

from typing import Optional


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
    lowered = stripped.lower().rstrip("!.")

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
    }
    return replacements.get(lowered, stripped)
