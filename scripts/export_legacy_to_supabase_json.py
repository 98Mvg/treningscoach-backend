#!/usr/bin/env python3
"""Export current SQLAlchemy data into JSON files shaped for Supabase import.

This is intentionally one-way and offline-safe. It does not write to Supabase.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from database import User, UserProfile, WorkoutHistory, WaitlistSignup
from main import app

OUTPUT_DIR = Path('output/supabase_export')


@dataclass
class ProfileRow:
    legacy_user_id: str
    email: str | None
    language: str | None
    training_level: str | None
    created_at: str | None


@dataclass
class WorkoutSessionRow:
    legacy_session_id: str
    legacy_user_id: str | None
    started_at: str | None
    ended_at: str | None
    workout_type: str | None
    device: str | None
    notes: str | None


@dataclass
class WorkoutMetricRow:
    legacy_session_id: str
    coaching_score: int | None
    avg_hr: int | None
    zones_json: dict[str, Any]
    summary_json: dict[str, Any]


@dataclass
class EmailEventRow:
    recipient_email: str | None
    template: str
    provider: str
    sent_at: str | None
    metadata_json: dict[str, Any]


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None



def export() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        profiles = [
            ProfileRow(
                legacy_user_id=str(user.id),
                email=user.email,
                language=(user.profile.language if user.profile else None),
                training_level=(user.profile.training_level if user.profile else None),
                created_at=iso(user.created_at),
            )
            for user in User.query.order_by(User.id.asc()).all()
        ]

        workouts = [
            WorkoutSessionRow(
                legacy_session_id=str(workout.id),
                legacy_user_id=str(workout.user_id) if workout.user_id else None,
                started_at=iso(workout.created_at),
                ended_at=iso(workout.created_at),
                workout_type=workout.workout_type,
                device='ios',
                notes=None,
            )
            for workout in WorkoutHistory.query.order_by(WorkoutHistory.id.asc()).all()
        ]

        metrics = [
            WorkoutMetricRow(
                legacy_session_id=str(workout.id),
                coaching_score=workout.coach_score,
                avg_hr=workout.avg_hr,
                zones_json={},
                summary_json={
                    'duration_seconds': workout.duration,
                    'calories': workout.calories,
                    'persona': workout.persona,
                    'language': workout.language,
                },
            )
            for workout in WorkoutHistory.query.order_by(WorkoutHistory.id.asc()).all()
        ]

        waitlist_emails = [
            EmailEventRow(
                recipient_email=signup.email,
                template='waitlist_confirmation',
                provider='resend',
                sent_at=iso(signup.created_at),
                metadata_json={'source': 'waitlist_signup'},
            )
            for signup in WaitlistSignup.query.order_by(WaitlistSignup.id.asc()).all()
        ]

        entitlements: list[dict[str, Any]] = []
        identity_links: list[dict[str, Any]] = []

    (OUTPUT_DIR / 'profiles.json').write_text(json.dumps([asdict(row) for row in profiles], indent=2), encoding='utf-8')
    (OUTPUT_DIR / 'workout_sessions.json').write_text(json.dumps([asdict(row) for row in workouts], indent=2), encoding='utf-8')
    (OUTPUT_DIR / 'workout_metrics.json').write_text(json.dumps([asdict(row) for row in metrics], indent=2), encoding='utf-8')
    (OUTPUT_DIR / 'email_events.json').write_text(json.dumps([asdict(row) for row in waitlist_emails], indent=2), encoding='utf-8')
    (OUTPUT_DIR / 'entitlements.json').write_text(json.dumps(entitlements, indent=2), encoding='utf-8')
    (OUTPUT_DIR / 'identity_links.json').write_text(json.dumps(identity_links, indent=2), encoding='utf-8')


if __name__ == '__main__':
    export()
