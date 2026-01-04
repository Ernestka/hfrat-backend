"""Facility model."""
from __future__ import annotations

from datetime import datetime

from ..extensions import db


class Facility(db.Model):
    __tablename__ = "facilities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True, index=True)
    country = db.Column(db.String(120), nullable=True, index=True)
    city = db.Column(db.String(120), nullable=True, index=True)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)

    reports = db.relationship(
        "ResourceReport", back_populates="facility", lazy="dynamic")
    users = db.relationship("User", back_populates="facility", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "city": self.city,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Facility {self.name}>"
