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
ACTIVE_APP_STORE_STATUSES = {"active", "trial", "grace_period"}


def _utcnow_naive() -> datetime:
    """Return UTC as naive datetime for existing DB columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalized_user_id(value: str | None) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def user_has_active_app_store_subscription(user_id: str | None) -> bool:
    normalized_user_id = _normalized_user_id(user_id)
    if not normalized_user_id:
        return False

    now = _utcnow_naive()
    active_state = (
        AppStoreSubscriptionState.query.filter(
            AppStoreSubscriptionState.user_id == normalized_user_id,
            AppStoreSubscriptionState.status.in_(tuple(ACTIVE_APP_STORE_STATUSES)),
            db.or_(
                AppStoreSubscriptionState.expires_at.is_(None),
                AppStoreSubscriptionState.expires_at > now,
            ),
            AppStoreSubscriptionState.revocation_date.is_(None),
        )
        .order_by(
            AppStoreSubscriptionState.expires_at.desc().nullslast(),
            AppStoreSubscriptionState.updated_at.desc(),
        )
        .first()
    )
    return active_state is not None


def get_database_url():
    """Get database URL from environment or default to SQLite"""
    configured = (os.getenv("DATABASE_URL") or "").strip()
    if configured:
        if configured.startswith("postgres://"):
            return configured.replace("postgres://", "postgresql+psycopg://", 1)
        if configured.startswith("postgresql://") and "+psycopg" not in configured:
            return configured.replace("postgresql://", "postgresql+psycopg://", 1)
        return configured

    instance_dir = Path(getattr(config, "INSTANCE_DIR", Path(__file__).resolve().parent / "instance"))
    sqlite_path = instance_dir / "treningscoach.db"
    return f"sqlite:///{sqlite_path.as_posix()}"


def should_auto_create_schema(database_url: str | None = None) -> bool:
    """Only auto-create schema for local SQLite development."""
    resolved_url = (database_url or get_database_url()).strip().lower()
    return resolved_url.startswith("sqlite:///")


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
        if should_auto_create_schema(database_url):
            db.create_all()
        else:
            app.logger.info(
                "Skipping db.create_all() for external database; schema is expected to be managed by Alembic migrations."
            )


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
    coaching_scores = db.relationship("CoachingScore", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        subscription_tier = "free"
        if config.user_has_premium_override(user_id=self.id, email=self.email):
            subscription_tier = "premium"
        elif self.subscription is not None:
            raw_tier = str(getattr(self.subscription, "tier", "") or "").strip().lower()
            if raw_tier == "premium":
                subscription_tier = "premium"
        elif user_has_active_app_store_subscription(self.id):
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
    coaching_score = db.relationship("CoachingScore", backref="workout", uselist=False, cascade="all, delete-orphan")

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


class CoachingScore(db.Model):
    __tablename__ = "coaching_scores"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    workout_id = db.Column(db.String(36), db.ForeignKey("workout_history.id"), nullable=False, unique=True, index=True)
    score = db.Column(db.Integer, nullable=False)
    hr_score = db.Column(db.Integer, nullable=True)
    breath_score = db.Column(db.Integer, nullable=True)
    duration_score = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "workout_id": self.workout_id,
            "score": self.score,
            "hr_score": self.hr_score,
            "breath_score": self.breath_score,
            "duration_score": self.duration_score,
            "created_at": self.created_at.isoformat(),
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
# APP STORE SUBSCRIPTION STATE
# ============================================

class AppStoreSubscriptionState(db.Model):
    __tablename__ = "app_store_subscription_states"

    original_transaction_id = db.Column(db.String(128), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    transaction_id = db.Column(db.String(128), nullable=True, unique=True, index=True)
    product_id = db.Column(db.String(255), nullable=True)
    bundle_id = db.Column(db.String(255), nullable=True)
    environment = db.Column(db.String(32), nullable=True)
    status = db.Column(db.String(32), nullable=False, default="unknown", index=True)
    ownership_type = db.Column(db.String(64), nullable=True)
    notification_type = db.Column(db.String(64), nullable=True)
    notification_subtype = db.Column(db.String(64), nullable=True)
    app_account_token = db.Column(db.String(64), nullable=True)
    purchase_date = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)
    revocation_date = db.Column(db.DateTime, nullable=True, index=True)
    last_transaction_signed_at = db.Column(db.DateTime, nullable=True)
    last_notification_signed_at = db.Column(db.DateTime, nullable=True)
    last_notification_uuid = db.Column(db.String(64), nullable=True)
    source = db.Column(db.String(32), nullable=False, default="unknown")
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive, onupdate=_utcnow_naive)


class AppStoreServerNotification(db.Model):
    __tablename__ = "app_store_server_notifications"

    notification_uuid = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    original_transaction_id = db.Column(db.String(128), nullable=True, index=True)
    transaction_id = db.Column(db.String(128), nullable=True, index=True)
    notification_type = db.Column(db.String(64), nullable=True)
    notification_subtype = db.Column(db.String(64), nullable=True)
    environment = db.Column(db.String(32), nullable=True)
    signed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow_naive, index=True)


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
