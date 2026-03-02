# Candidate Queue System — Design Document

> **Date:** 2026-03-02
> **Status:** Approved
> **Scope:** Offline candidate variant generation + approval workflow for coaching phrases

## Goal

Create a CLI-driven workflow to generate, review, and promote new coaching phrase variants without any live Grok calls during workouts. During workouts: only pre-generated MP3 via phrase_id. After workouts (or in dev mode): generate candidate text variants, review, approve, and feed them into the existing audio pack pipeline.

## Architecture

```
generate_candidates.py (CLI)
  → Grok generates EN + NO text per candidate
  → validate_coaching_text() + norwegian_phrase_quality.py post-process
  → dedup via variant_key
  → append to candidate_queue.json

candidate_review.py (CLI)
  → list / approve / reject / export XLSX / import XLSX
  → promote --apply → writes to tts_phrase_catalog.py

Existing pipeline takes over:
  → generate_audio_pack.py --version v1 --upload
  → iOS AudioPackSyncManager picks up new manifest
```

## Non-Goals (v1)

- No post-workout auto-generation (schema supports it, trigger not built)
- No web UI for review
- No runtime changes to main.py, zone_event_motor, or workout flow
- No multi-model comparison (Grok only for v1)

---

## 1. Queue Schema

Each candidate in `output/candidate_queue.json`:

```json
{
  "candidate_id": "cand_20260302_143022_001",
  "status": "pending",
  "event_type": "interval_in_target_sustained",
  "phrase_family": "interval.motivate.s2",
  "generated_text_en": "You're locked in!",
  "generated_text_no": "Du er i flytsonen!",
  "languages": ["en", "no"],
  "model": "grok-3-mini",
  "model_params": {"temperature": 0.9, "max_tokens": 24},
  "persona": "personal_trainer",
  "source": "cli",
  "variant_key": "a3f8c1...",
  "validation": {"passed": true, "reasons": []},
  "context": {
    "phase": "work",
    "intensity": "moderate",
    "session_id": null,
    "heart_rate": null,
    "elapsed_seconds": null
  },
  "created_at": "2026-03-02T14:30:22Z",
  "reviewed_at": null,
  "reviewer_note": null
}
```

### Field reference

| Field | Type | Description |
|---|---|---|
| `candidate_id` | string | Timestamp-based unique ID (`cand_YYYYMMDD_HHMMSS_NNN`) |
| `status` | enum | `pending` / `approved` / `rejected` / `promoted` / `skipped` |
| `event_type` | string | Zone event type (e.g. `interval_in_target_sustained`) |
| `phrase_family` | string | Target family (e.g. `interval.motivate.s2`) |
| `generated_text_en` | string | English candidate text |
| `generated_text_no` | string | Norwegian candidate text |
| `languages` | list | `["en", "no"]` — which languages were generated |
| `model` | string | Model used (e.g. `grok-3-mini`) |
| `model_params` | dict | `{temperature, max_tokens}` |
| `persona` | string | `personal_trainer` or `toxic_mode` |
| `source` | string | `cli` (v1) or `post_workout` (future) |
| `variant_key` | string | SHA256 of `(event_type + phrase_family + en + no + persona)` for dedup |
| `validation` | dict | `{passed: bool, reasons: [str]}` from `validate_coaching_text()` |
| `context` | dict | Nullable session context fields for future auto-generation |
| `created_at` | string | ISO 8601 timestamp |
| `reviewed_at` | string? | ISO 8601 timestamp of review |
| `reviewer_note` | string? | Free-text note on approval/rejection |

### Status lifecycle

```
[generated] → pending
  → approved → promoted (after promote --apply)
  → rejected (terminal)
  → skipped  (duplicate detected at generation time)
```

---

## 2. CLI Tool: generate_candidates.py

### Usage

```bash
# Generate 5 candidates for interval motivation stage 2
python3 tools/generate_candidates.py --family interval.motivate.s2 --count 5

# Generate 3 candidates for all motivation families
python3 tools/generate_candidates.py --all-motivation --count 3

# Generate for a specific event type (infers families)
python3 tools/generate_candidates.py --event-type easy_run_in_target_sustained --count 4
```

### Generation flow per candidate

1. Build "avoid list" from existing catalog variants + pending queue entries for that family
2. Call Grok for EN text (with avoid list + purpose tag)
3. Call Grok for NO text (with Norwegian avoid list + tone examples from `norwegian_phrase_quality.py`)
4. Run `rewrite_norwegian_phrase()` on NO text as post-processing
5. Run `validate_coaching_text(mode="realtime")` on both EN and NO
6. Compute `variant_key` → check for duplicates in queue + catalog
7. If duplicate → store with `status="skipped"`, `skip_reason="duplicate"`
8. If validation fails → store with `validation.passed=false` and reasons
9. If passes → store with `status="pending"`

### Safety caps

- `MAX_TOTAL_PER_RUN = 30`
- `MAX_PER_FAMILY_PER_RUN = 10`

### Grok parameters

- Model: `grok-3-mini`
- `max_tokens`: 24
- `temperature`: 0.9
- Timeout: 10s

---

## 3. Prompt Design

### English prompt

```
System: You write short coaching cues for runners during interval workouts.
Persona: personal_trainer — calm, direct, elite endurance coach.
Purpose: {purpose_tag}
Phase context: {phase}

Rules:
- 2-8 words, one actionable or motivational cue
- No questions, no explanations
- Never mention breathing, apps, or AI
- Match the energy: confident, grounded, present-tense

Existing variants (DO NOT repeat these):
{avoid_list_en}

Pending candidates (also avoid):
{pending_list_en}

Write ONE new variant. Output the cue only, nothing else.
```

### Norwegian prompt

```
System: Du skriver korte coachingfraser for løpere under intervalltrening.
Persona: personal_trainer — rolig, direkte, elite utholdenhetscoach.
Formål: {purpose_tag}

Regler:
- 2-8 ord, én handlings- eller motivasjonsfrase
- Ikke spørsmål, ikke forklaringer
- Aldri nevn pust, apper eller AI
- Naturlig norsk — IKKE oversatt engelsk
- Bruk æ, ø, å korrekt

Tonefølelse — dette er den riktige stilen:
- "Mer press nå!"
- "Trykk litt hardere."
- "Bra jobba!"
- "Finn jevn rytme."
- "Øk tempoet."
- "Du klarer det!"
- "Hold deg fokusert!"
- "Nå øker vi trykket."

UNNGÅ denne typen (oversatt/stivt norsk):
- "Vakkert" (for formelt)
- "Gi meg mer kraft" (uklart)
- "Holdt" (ufullstendig)
- "Jevn opp" (unaturlig)

Eksisterende varianter (IKKE gjenta disse):
{avoid_list_no}

Skriv ÉN ny variant. Kun frasen, ingenting annet.
```

Norwegian tone examples and anti-examples are read from `norwegian_phrase_quality.py` at generation time to stay in sync.

### Purpose tag inference

| Family prefix | Purpose tag |
|---|---|
| `interval.motivate` | `motivation_in_zone` |
| `easy_run.motivate` | `motivation_in_zone` |
| `zone.above` | `hr_correction_above` |
| `zone.below` | `hr_correction_below` |
| `zone.silence` | `silence_filler` |
| `zone.breath` | `breath_guidance` |

---

## 4. Review & Approval Workflow

### CLI review

```bash
# Show pending candidates
python3 tools/candidate_review.py list

# Approve specific candidates
python3 tools/candidate_review.py approve cand_20260302_143022_001 cand_20260302_143022_003

# Reject with note
python3 tools/candidate_review.py reject cand_20260302_143022_002 --note "too generic"

# Approve all pending that passed validation
python3 tools/candidate_review.py approve-valid
```

### XLSX round-trip

```bash
# Export to XLSX for review
python3 tools/candidate_review.py export --format xlsx

# Edit status column in Excel, then import back
python3 tools/candidate_review.py import --xlsx output/candidate_review.xlsx
```

XLSX columns: `candidate_id | status | phrase_family | en | no | validation | model | reviewer_note`. Only `status` and `reviewer_note` are editable. Text changes are not supported — reject and regenerate instead.

### Promote to catalog

```bash
# Dry run
python3 tools/candidate_review.py promote --dry-run

# Apply — appends to tts_phrase_catalog.py, marks as promoted
python3 tools/candidate_review.py promote --apply
```

Promote logic:
1. Read all `status == "approved"` candidates
2. For each, find next available variant number in that `phrase_family` (e.g. `.s2.1` and `.s2.2` exist → new gets `.s2.3`)
3. Append to `PHRASE_CATALOG` in `tts_phrase_catalog.py` via source editing
4. Update candidate `status` to `"promoted"`
5. Print summary of new IDs assigned

After promote, existing pipeline takes over:
```bash
python3 tools/generate_audio_pack.py --version v1 --upload
# iOS AudioPackSyncManager picks up new manifest automatically
```

---

## 5. File Structure & Module Boundaries

### New files

| File | Purpose |
|---|---|
| `candidate_queue.py` | Shared library: queue I/O, schema, dedup, variant numbering |
| `tools/generate_candidates.py` | CLI: generate candidates via Grok → queue |
| `tools/candidate_review.py` | CLI: list/approve/reject/export/import/promote |
| `tests_phaseb/test_candidate_queue.py` | Unit tests for queue logic |

### Existing files modified

| File | Change |
|---|---|
| `.gitignore` | Add `output/candidate_queue.json` |

### Module boundaries

```
candidate_queue.py (pure library, no Grok/API deps)
├── load_queue() → list[dict]
├── save_queue(candidates)
├── compute_variant_key(event_type, family, en, no, persona) → str
├── next_variant_id(family) → str
├── validate_candidate(en_text, no_text, persona) → {passed, reasons}
├── promote_to_catalog(approved_candidates) → list[new_ids]
└── Constants: QUEUE_PATH, MAX_TOTAL_PER_RUN, MAX_PER_FAMILY_PER_RUN, PURPOSE_TAGS

generate_candidates.py (CLI — depends on candidate_queue + brain_router)
├── --family / --all-motivation / --event-type
├── --count N
├── --model (default: grok)
└── Writes to candidate_queue.json

candidate_review.py (CLI — depends on candidate_queue + tts_phrase_catalog)
├── list / approve / reject / approve-valid
├── export --format xlsx
├── import --xlsx
└── promote --dry-run / --apply
```

Zero Grok/API dependencies in `candidate_queue.py` — keeps tests fast and logic reusable.

---

## 6. Config & Constants

All in `candidate_queue.py` (tool-only, not runtime):

```python
QUEUE_PATH = "output/candidate_queue.json"
MAX_TOTAL_PER_RUN = 30
MAX_PER_FAMILY_PER_RUN = 10
CANDIDATE_MODEL_DEFAULT = "grok-3-mini"
CANDIDATE_TEMPERATURE = 0.9
CANDIDATE_MAX_TOKENS = 24
CANDIDATE_TIMEOUT = 10

PURPOSE_TAGS = {
    "interval.motivate": "motivation_in_zone",
    "easy_run.motivate": "motivation_in_zone",
    "zone.above":        "hr_correction_above",
    "zone.below":        "hr_correction_below",
    "zone.silence":      "silence_filler",
    "zone.breath":       "breath_guidance",
}
```

No `config.py` changes — these constants are tool-only, not runtime.

---

## 7. Test Plan

### `tests_phaseb/test_candidate_queue.py`

| Test | Verifies |
|---|---|
| `test_compute_variant_key_deterministic` | Same inputs → same hash |
| `test_compute_variant_key_differs` | Different text → different hash |
| `test_next_variant_id_empty_family` | No existing variants → `.1` |
| `test_next_variant_id_increments` | `.1` and `.2` exist → `.3` |
| `test_next_variant_id_with_gaps` | `.1` and `.3` exist → `.4` (max+1) |
| `test_validate_candidate_passes` | Valid 3-word cue passes |
| `test_validate_candidate_too_long` | 20-word cue fails with reason |
| `test_validate_candidate_forbidden_phrase` | "breathing exercise" fails |
| `test_duplicate_detection_in_queue` | Same variant_key in queue → skipped |
| `test_duplicate_detection_against_catalog` | Text already in catalog → skipped |
| `test_load_save_roundtrip` | Write queue, read back, identical |
| `test_promote_assigns_correct_ids` | Approved candidates get next variant numbers |
| `test_promote_updates_status` | Promoted candidates → `status="promoted"` |
| `test_max_per_family_cap` | Exceeding cap stops generation for that family |

No Grok/API calls in tests — all pure functions. CLI tools are integration-tested manually.
