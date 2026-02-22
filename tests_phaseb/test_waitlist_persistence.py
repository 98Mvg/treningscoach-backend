import hashlib
import os
import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from database import WaitlistSignup, db


def test_waitlist_signup_persists_to_database():
    client = main.app.test_client()
    email = f"waitlist-{uuid.uuid4().hex[:12]}@example.com"
    remote_ip = "10.0.0.10"

    response = client.post(
        "/waitlist",
        json={"email": email, "language": "no", "source": "website"},
        environ_overrides={"REMOTE_ADDR": remote_ip},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True

    with main.app.app_context():
        row = WaitlistSignup.query.filter_by(email=email).first()
        assert row is not None
        assert row.language == "no"
        assert row.source == "website"
        db.session.delete(row)
        db.session.commit()


def test_waitlist_rate_limit_uses_database_window():
    client = main.app.test_client()
    remote_ip = "10.0.0.11"
    ip_hash = hashlib.sha256(remote_ip.encode()).hexdigest()
    seeded_ids = []

    with main.app.app_context():
        for i in range(5):
            row = WaitlistSignup(
                email=f"seed-{uuid.uuid4().hex[:8]}-{i}@example.com",
                language="en",
                source="website",
                ip_hash=ip_hash,
                created_at=datetime.utcnow() - timedelta(minutes=10),
            )
            db.session.add(row)
            db.session.flush()
            seeded_ids.append(row.id)
        db.session.commit()

    response = client.post(
        "/waitlist",
        json={"email": f"new-{uuid.uuid4().hex[:10]}@example.com", "language": "en"},
        environ_overrides={"REMOTE_ADDR": remote_ip},
    )

    assert response.status_code == 429
    payload = response.get_json()
    assert payload["error"] == "Rate limit exceeded"

    with main.app.app_context():
        for row_id in seeded_ids:
            row = db.session.get(WaitlistSignup, row_id)
            if row is not None:
                db.session.delete(row)
        db.session.commit()
