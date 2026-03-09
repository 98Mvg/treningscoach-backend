#!/usr/bin/env python3
"""Offline verification for the additive Supabase business-platform scaffold.

This script does not connect to Supabase. It validates:
- the migration file contains the required tables/columns
- export artifacts exist
- exported JSON shapes match the expected mirror/import contract
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = REPO_ROOT / "supabase/migrations/20260309_000001_business_platform.sql"
EXPORT_DIR = REPO_ROOT / "output/supabase_export"

REQUIRED_TABLE_COLUMNS = {
    "profiles": ["clerk_user_id", "legacy_user_id", "email", "language", "training_level", "created_at"],
    "workout_sessions": ["profile_id", "legacy_session_id", "started_at", "ended_at", "workout_type", "device", "notes"],
    "workout_metrics": ["session_id", "coaching_score", "avg_hr", "zones_json", "summary_json"],
    "entitlements": [
        "profile_id",
        "is_pro",
        "source",
        "status",
        "current_period_end",
        "premium_talk_to_coach",
        "premium_extended_history",
        "premium_advanced_analysis",
        "premium_multiple_coaches",
    ],
    "identity_links": ["legacy_user_id", "clerk_user_id"],
    "email_events": ["profile_id", "template", "recipient_email", "provider", "provider_message_id", "metadata_json"],
}

REQUIRED_EXPORT_FILES = {
    "profiles.json": {"legacy_user_id", "email", "language", "training_level", "created_at"},
    "workout_sessions.json": {
        "legacy_session_id",
        "legacy_user_id",
        "started_at",
        "ended_at",
        "workout_type",
        "device",
        "notes",
    },
    "workout_metrics.json": {"legacy_session_id", "coaching_score", "avg_hr", "zones_json", "summary_json"},
    "entitlements.json": None,
    "identity_links.json": None,
    "email_events.json": {"recipient_email", "template", "provider", "sent_at", "metadata_json"},
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_migration() -> None:
    content = MIGRATION_PATH.read_text(encoding="utf-8")
    for table_name, columns in REQUIRED_TABLE_COLUMNS.items():
        require(f"create table if not exists {table_name}" in content, f"missing table {table_name}")
        for column in columns:
            require(column in content, f"missing column {column} in migration for {table_name}")


def verify_export_file(filename: str, required_keys: set[str] | None) -> None:
    path = EXPORT_DIR / filename
    require(path.exists(), f"missing export file {filename}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, list), f"{filename} must contain a JSON array")
    if required_keys is None or not payload:
        return
    first = payload[0]
    require(isinstance(first, dict), f"{filename} first item must be an object")
    missing = sorted(required_keys - set(first.keys()))
    require(not missing, f"{filename} missing keys: {', '.join(missing)}")


def main() -> int:
    verify_migration()
    for filename, required_keys in REQUIRED_EXPORT_FILES.items():
        verify_export_file(filename, required_keys)
    print("Supabase business-platform verification passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
