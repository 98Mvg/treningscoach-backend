#!/usr/bin/env python3
"""Generate coaching phrase candidates via Grok API.

Usage examples:
  python3 tools/generate_candidates.py --family interval.motivate.s2 --count 5
  python3 tools/generate_candidates.py --all-motivation --count 3
  python3 tools/generate_candidates.py --event-type easy_run_in_target_sustained --count 4
  python3 tools/generate_candidates.py --family interval.motivate.s2 --count 3 --dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import candidate_queue as cq
from norwegian_phrase_quality import rewrite_norwegian_phrase


def _build_en_prompt(purpose_tag: str, avoid_en: list[str], pending_en: list[str]) -> tuple[str, str]:
    avoid_block = "\n".join(f'- "{t}"' for t in avoid_en) if avoid_en else "- (none)"
    pending_block = "\n".join(f'- "{t}"' for t in pending_en) if pending_en else ""

    system = (
        "You write short coaching cues for runners during workouts.\n"
        "Persona: personal_trainer - calm, direct, elite endurance coach.\n"
        f"Purpose: {purpose_tag}\n\n"
        "Rules:\n"
        "- 2-8 words, one actionable or motivational cue\n"
        "- No questions, no explanations\n"
        "- Never mention breathing exercises, apps, or AI\n"
        "- Confident, grounded, present tense\n\n"
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
    avoid_block = "\n".join(f'- "{t}"' for t in avoid_no) if avoid_no else "- (ingen)"
    good_block = "\n".join(f'- "{t}"' for t in good_examples[:8]) if good_examples else ""
    bad_block = "\n".join(f'- "{t}"' for t in bad_examples[:4]) if bad_examples else ""

    system = (
        "Du skriver korte coachingfraser for løpere under trening.\n"
        "Persona: personal_trainer - rolig, direkte, elite utholdenhetscoach.\n"
        f"Formal: {purpose_tag}\n\n"
        "Regler:\n"
        "- 2-8 ord, en handlings- eller motivasjonsfrase\n"
        "- Ikke spørsmål, ikke forklaringer\n"
        "- Aldri nevn pusteøvelser, apper eller AI\n"
        "- Naturlig norsk, ikke oversatt engelsk\n"
        "- Bruk ae, oe, aa bare hvis unicode mangler\n"
    )
    if good_block:
        system += f"\nTonefolelse - riktig stil:\n{good_block}\n"
    if bad_block:
        system += f"\nUnnga denne typen:\n{bad_block}\n"
    system += f"\nEksisterende varianter (IKKE gjenta disse):\n{avoid_block}"

    user = "Skriv EN ny variant. Kun frasen, ingenting annet."
    return system, user


def _call_grok(system_prompt: str, user_prompt: str, dry_run: bool = False) -> str:
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
        text = (response.choices[0].message.content or "").strip()
        parts = re.split(r"(?<=[.!?])\s+", text)
        if parts and parts[0].strip():
            text = parts[0].strip()
        if text.startswith('"') and text.endswith('"') and len(text) >= 2:
            text = text[1:-1]
        return text.strip()
    except Exception as exc:
        print(f"  WARNING Grok API error: {exc}")
        return ""


def _resolve_families(args: argparse.Namespace) -> list[str]:
    if args.all_motivation:
        return list(cq.ALL_MOTIVATION_FAMILIES)
    if args.event_type:
        families = cq.EVENT_TO_FAMILIES.get(args.event_type, [])
        if not families:
            print(f"Unknown event type: {args.event_type}")
            print("Known event types: " + ", ".join(sorted(cq.EVENT_TO_FAMILIES.keys())))
            raise SystemExit(2)
        return families
    if args.family:
        return [args.family]
    print("Must specify --family, --event-type, or --all-motivation")
    raise SystemExit(2)


def _infer_event_type(family: str) -> str:
    for event_type, families in cq.EVENT_TO_FAMILIES.items():
        if family in families:
            return event_type
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate coaching phrase candidates via Grok")
    parser.add_argument("--family", help="Target phrase family (e.g. interval.motivate.s2)")
    parser.add_argument("--event-type", help="Event type (infers families)")
    parser.add_argument("--all-motivation", action="store_true", help="Generate for all motivation families")
    parser.add_argument("--count", type=int, default=3, help="Candidates per family")
    parser.add_argument("--persona", default="personal_trainer", help="Persona")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls and use placeholders")
    args = parser.parse_args()

    families = _resolve_families(args)
    count_per_family = max(1, min(int(args.count), cq.MAX_PER_FAMILY_PER_RUN))

    queue = cq.load_queue()
    good_no, bad_no = cq.get_norwegian_tone_examples()

    total_generated = 0
    total_skipped = 0
    total_failed = 0

    print(f"Generating {count_per_family} candidates x {len(families)} families")
    print(f"Queue has {len(queue)} existing entries")
    print("")

    for family in families:
        if total_generated >= cq.MAX_TOTAL_PER_RUN:
            print(f"Hit MAX_TOTAL_PER_RUN ({cq.MAX_TOTAL_PER_RUN}); stopping.")
            break

        purpose_tag = cq.infer_purpose_tag(family)
        event_type = _infer_event_type(family)
        print(f"-- {family} ({purpose_tag}) --")

        for idx in range(1, count_per_family + 1):
            if total_generated >= cq.MAX_TOTAL_PER_RUN:
                break

            avoid_en, avoid_no = cq.get_avoid_lists(family, queue)
            system_en, user_en = _build_en_prompt(purpose_tag, avoid_en, [])
            system_no, user_no = _build_no_prompt(purpose_tag, avoid_no, good_no, bad_no)

            text_en = _call_grok(system_en, user_en, dry_run=args.dry_run)
            text_no = _call_grok(system_no, user_no, dry_run=args.dry_run)

            if text_no and not args.dry_run:
                text_no = rewrite_norwegian_phrase(text_no)

            if not text_en and not text_no:
                print(f"  [{idx}] FAIL both empty")
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

            status = candidate.get("status")
            validation = candidate.get("validation", {})
            passed = bool(validation.get("passed"))

            if status == "skipped":
                print(f"  [{idx}] SKIP duplicate")
                total_skipped += 1
            elif not passed:
                reasons = ", ".join(validation.get("reasons", []))
                print(f"  [{idx}] WARN en=\"{text_en}\" no=\"{text_no}\" ({reasons})")
                total_generated += 1
            else:
                print(f"  [{idx}] OK   en=\"{text_en}\" no=\"{text_no}\"")
                total_generated += 1

            if not args.dry_run:
                time.sleep(0.5)

    cq.save_queue(queue)
    print("")
    print(f"Done. Generated: {total_generated}, Skipped: {total_skipped}, Failed: {total_failed}")
    print(f"Queue now has {len(queue)} entries. Saved to {cq.QUEUE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
