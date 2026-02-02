"""
Database models and setup for Treningscoach
SQLite for development, PostgreSQL for production (via DATABASE_URL env var)
"""

import os
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def get_database_url():
    """Get database URL from environment or default to SQLite"""
    return os.getenv("DATABASE_URL", "sqlite:///treningscoach.db")


def init_db(app):
    """Initialize database with Flask app"""
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url()
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
    auth_provider = db.Column(db.String(50), nullable=False)  # "google", "facebook", "vipps"
    auth_provider_id = db.Column(db.String(255), nullable=False)  # Provider's user ID

    # Preferences
    language = db.Column(db.String(5), nullable=False, default="en")  # "en" or "no"
    training_level = db.Column(db.String(20), nullable=False, default="intermediate")  # beginner/intermediate/advanced
    preferred_persona = db.Column(db.String(50), nullable=True, default="fitness_coach")

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    settings = db.relationship("UserSettings", backref="user", uselist=False, cascade="all, delete-orphan")
    workouts = db.relationship("WorkoutHistory", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "auth_provider": self.auth_provider,
            "language": self.language,
            "training_level": self.training_level,
            "preferred_persona": self.preferred_persona,
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
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "coach_voice_id_en": self.coach_voice_id_en,
            "coach_voice_id_no": self.coach_voice_id_no,
            "coaching_frequency": self.coaching_frequency
        }


# ============================================
# WORKOUT HISTORY MODEL
# ============================================

class WorkoutHistory(db.Model):
    __tablename__ = "workout_history"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    # Workout data
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    duration_seconds = db.Column(db.Integer, nullable=False, default=0)
    final_phase = db.Column(db.String(20), nullable=True)  # warmup/intense/cooldown
    avg_intensity = db.Column(db.String(20), nullable=True)  # calm/moderate/intense
    persona_used = db.Column(db.String(50), nullable=True)
    language = db.Column(db.String(5), nullable=True, default="en")

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

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
