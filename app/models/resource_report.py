"""Resource report model."""
from __future__ import annotations

from datetime import datetime

from ..extensions import db


class ResourceReport(db.Model):
    __tablename__ = "resource_reports"

    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey(
        "facilities.id"), nullable=False, index=True)
    icu_beds_available = db.Column(db.Integer, nullable=False, default=0)
    ventilators_available = db.Column(db.Integer, nullable=False, default=0)
    staff_on_duty = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    facility = db.relationship("Facility", back_populates="reports")

    __table_args__ = (
        db.CheckConstraint("icu_beds_available >= 0",
                           name="ck_reports_icu_beds_non_negative"),
        db.CheckConstraint("ventilators_available >= 0",
                           name="ck_reports_ventilators_non_negative"),
        db.CheckConstraint("staff_on_duty >= 0",
                           name="ck_reports_staff_non_negative"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "facility_id": self.facility_id,
            "icu_beds_available": self.icu_beds_available,
            "ventilators_available": self.ventilators_available,
            "staff_on_duty": self.staff_on_duty,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<ResourceReport {self.id}>"
