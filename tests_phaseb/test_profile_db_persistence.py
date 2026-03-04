import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from database import db, User, UserProfile


def test_user_profile_model_persists_and_serializes():
    with main.app.app_context():
        email = f"profile_test_{datetime.now(tz=timezone.utc).timestamp()}@example.com"
        user = User(
            email=email,
            display_name="Profile Tester",
            auth_provider="google",
            auth_provider_id=email,
            language="en",
            training_level="beginner",
        )
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(
            user_id=user.id,
            name="Marius",
            sex="male",
            age=29,
            height_cm=182.0,
            weight_kg=79.0,
            max_hr_bpm=192,
            resting_hr_bpm=52,
            profile_updated_at=datetime.now(tz=timezone.utc),
        )
        db.session.add(profile)
        db.session.commit()

        stored = UserProfile.query.filter_by(user_id=user.id).first()
        assert stored is not None
        payload = stored.to_dict()
        assert payload["name"] == "Marius"
        assert payload["max_hr_bpm"] == 192
        assert payload["resting_hr_bpm"] == 52

        # cleanup
        db.session.delete(stored)
        db.session.delete(user)
        db.session.commit()
