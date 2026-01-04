"""Monitor routes."""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, func

from ..extensions import db
from ..models import Facility, ResourceReport
from ..utils.decorators import monitor_required

monitor_bp = Blueprint("monitor", __name__)


@monitor_bp.get("/dashboard")
@monitor_required
def dashboard_summary():
    facilities = Facility.query.order_by(Facility.name.asc()).all()

    latest_subq = (
        db.session.query(
            ResourceReport.facility_id,
            func.max(ResourceReport.updated_at).label("latest_ts"),
        )
        .group_by(ResourceReport.facility_id)
        .subquery()
    )

    latest_reports = (
        db.session.query(ResourceReport)
        .join(
            latest_subq,
            and_(
                ResourceReport.facility_id == latest_subq.c.facility_id,
                ResourceReport.updated_at == latest_subq.c.latest_ts,
            ),
        )
        .all()
    )
    latest_by_facility = {r.facility_id: r for r in latest_reports}

    def loc_string(fac: Facility) -> str | None:
        parts = [p for p in [fac.city, fac.country] if p]
        return ", ".join(parts) if parts else None

    summary = []
    for fac in facilities:
        report = latest_by_facility.get(fac.id)
        summary.append(
            {
                "facility_id": fac.id,
                "facility_name": fac.name,
                "country": fac.country,
                "city": fac.city,
                "location": loc_string(fac),
                "icu_beds_available": getattr(report, "icu_beds_available", None),
                "ventilators_available": getattr(report, "ventilators_available", None),
                "staff_on_duty": getattr(report, "staff_on_duty", None),
                "last_update": report.updated_at.isoformat() if report else None,
                "critical": bool(report and report.icu_beds_available == 0),
            }
        )

    return jsonify({"facilities": summary})


@monitor_bp.get("/dashboard/history")
@monitor_required
def dashboard_history():
    facility_id = request.args.get("facility_id", type=int)
    days = request.args.get("days", default=7, type=int)

    if not facility_id:
        return jsonify({"error": "facility_id is required."}), 400
    if days is None or days <= 0:
        return jsonify({"error": "days must be a positive integer."}), 400

    facility = Facility.query.get(facility_id)
    if not facility:
        return jsonify({"error": "Facility not found."}), 404

    since = datetime.utcnow() - timedelta(days=days)
    reports = (
        ResourceReport.query.filter_by(facility_id=facility_id)
        .filter(ResourceReport.updated_at >= since)
        .order_by(ResourceReport.updated_at.asc())
        .all()
    )

    return jsonify(
        {
            "facility": {
                "id": facility.id,
                "name": facility.name,
                "country": facility.country,
                "city": facility.city,
            },
            "days": days,
            "reports": [report.to_dict() for report in reports],
        }
    )
