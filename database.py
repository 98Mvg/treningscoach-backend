"""
Database models and setup for Treningscoach
SQLite for development, PostgreSQL for production (via DATABASE_URL env var)
"""

import os
import uuid
from pathlib import Path
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
import config

db = SQLAlchemy()


def _utcnow_naive() -> datetime:
    """Return UTC as naive datetime for existing DB columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_database_url():
    """Get database URL from environment or default to SQLite"""
    configured = (os.getenv("DATABASE_URL") or "").strip()
    if configured:
        return configured

    instance_dir = Path(getattr(config, "INSTANCE_DIR", Path(__file__).resolve().parent / "instance"))
    sqlite_path = instance_dir / "treningscoach.db"
    return f"sqlite:///{sqlite_path.as_posix()}"


def init_db(app):
    """Initialize database with Flask app"""
    database_url = get_database_url()
    if database_url.startswith("sqlite:///") and "://" in database_url and not os.getenv("DATABASE_URL"):
        Path(getattr(config, "INSTANCE_DIR", Path(__file__).resolve().parent / "instance")).mkdir(
            parents=True,
            exist_ok=True,
        )
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()


# ============================================
# USER MODEL
# ============================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    display_name = db.Column(db.String(255), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)

    # Auth
    auth_provider = db.Column(db.String(50), nullable=False)  # "apple", "email", "google", "facebook", "vipps"
    auth_provider_id = db.Column(db.String(255), nullable=False)  # Provider's user ID

    # Preferences
    language = db.Column(db.String(5), nullable=False, default="en")  # "en" or "no"
    training_level = db.Column(db.String(20), nullable=False, default="intermediate")  # beginner/intermediate/advanced
    preferred_persona = db.Column(db.String(50), nullable=True, default="personal_trainer")

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive, onupdate=_utcnow_naive)

    # Relationships
    settings = db.relationship("UserSettings", backref="user", uselist=False, cascade="all, delete-orphan")
    profile = db.relationship("UserProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    subscription = db.relationship("UserSubscription", backref="user", uselist=False, cascade="all, delete-orphan")
    workouts = db.relationship("WorkoutHistory", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        subscription_tier = "free"
        if self.subscription is not None:
            raw_tier = str(getattr(self.subscription, "tier", "") or "").strip().lower()
            if raw_tier == "premium":
                subscription_tier = "premium"
        return {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "auth_provider": self.auth_provider,
            "language": self.language,
            "training_level": self.training_level,
            "preferred_persona": self.preferred_persona,
            "subscription_tier": subscription_tier,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# ============================================
# USER SETTINGS MODEL
# ============================================

class UserSettings(db.Model):
    __tablename__ = "user_settings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True)

    # Voice preferences
    coach_voice_id_en = db.Column(db.String(255), nullable=True)
    coach_voice_id_no = db.Column(db.String(255), nullable=True)

    # Coaching preferences
    coaching_frequency = db.Column(db.String(20), nullable=True, default="normal")  # low/normal/high

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive, onupdate=_utcnow_naive)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "coach_voice_id_en": self.coach_voice_id_en,
            "coach_voice_id_no": self.coach_voice_id_no,
            "coaching_frequency": self.coaching_frequency
        }


# ============================================
# USER PROFILE MODEL
# ============================================

class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    name = db.Column(db.String(255), nullable=True)
    sex = db.Column(db.String(32), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    max_hr_bpm = db.Column(db.Integer, nullable=True)
    resting_hr_bpm = db.Column(db.Integer, nullable=True)
    profile_updated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive, onupdate=_utcnow_naive)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "sex": self.sex,
            "age": self.age,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "max_hr_bpm": self.max_hr_bpm,
            "resting_hr_bpm": self.resting_hr_bpm,
            "profile_updated_at": self.profile_updated_at.isoformat() if self.profile_updated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================
# WORKOUT HISTORY MODEL
# ============================================

class WorkoutHistory(db.Model):
    __tablename__ = "workout_history"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    # Workout data
    date = db.Column(db.DateTime, nullable=False, default=_utcnow_naive)
    duration_seconds = db.Column(db.Integer, nullable=False, default=0)
    final_phase = db.Column(db.String(20), nullable=True)  # warmup/intense/cooldown
    avg_intensity = db.Column(db.String(20), nullable=True)  # calm/moderate/intense
    persona_used = db.Column(db.String(50), nullable=True)
    language = db.Column(db.String(5), nullable=True, default="en")

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "duration_seconds": self.duration_seconds,
            "final_phase": self.final_phase,
            "avg_intensity": self.avg_intensity,
            "persona_used": self.persona_used,
            "language": self.language,
            "created_at": self.created_at.isoformat()
        }


# ============================================
# REFRESH TOKEN MODEL (ROTATION + REVOCATION)
# ============================================

class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    family_id = db.Column(db.String(36), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive)
    last_used_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True, index=True)
    replaced_by_hash = db.Column(db.String(64), nullable=True)
    issued_ip = db.Column(db.String(64), nullable=True)
    issued_user_agent = db.Column(db.String(512), nullable=True)

    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > _utcnow_naive()


class EmailAuthCode(db.Model):
    __tablename__ = "email_auth_codes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    code_hash = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive, index=True)
    used_at = db.Column(db.DateTime, nullable=True, index=True)


# ============================================
# USER SUBSCRIPTION MODEL
# ============================================

class UserSubscription(db.Model):
    __tablename__ = "user_subscriptions"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), primary_key=True)
    tier = db.Column(db.String(20), nullable=False, default="free")
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive, onupdate=_utcnow_naive)


# ============================================
# RATE LIMIT COUNTER MODEL
# ============================================

class RateLimitCounter(db.Model):
    __tablename__ = "rate_limit_counters"

    subject_key = db.Column(db.String(255), primary_key=True)
    rule_name = db.Column(db.String(120), primary_key=True)
    window_start = db.Column(db.Integer, primary_key=True)
    window_seconds = db.Column(db.Integer, nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive, onupdate=_utcnow_naive, index=True)


# ============================================
# WAITLIST SIGNUP MODEL
# ============================================

class WaitlistSignup(db.Model):
    __tablename__ = "waitlist_signups"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    language = db.Column(db.String(10), nullable=False, default="en")
    source = db.Column(db.String(50), nullable=False, default="website")
    ip_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "language": self.language,
            "source": self.source,
            "ip_hash": self.ip_hash,
            "created_at": self.created_at.isoformat(),
        }
