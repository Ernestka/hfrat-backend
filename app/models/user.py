"""User model."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class UserRole(str, Enum):
    ADMIN = "admin"
    REPORTER = "reporter"
    MONITOR = "monitor"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False,
                     default=UserRole.REPORTER, index=True)
    facility_id = db.Column(db.Integer, db.ForeignKey(
        "facilities.id"), nullable=True, index=True)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    facility = db.relationship("Facility", back_populates="users")
    __table_args__ = (
        db.CheckConstraint(
            "(role != 'REPORTER' AND facility_id IS NULL) OR role = 'REPORTER'",
            name="ck_users_facility_only_for_reporter",
        ),
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role.value if self.role else None,
            "facility_id": self.facility_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.email}>"
