"""Reporter routes."""
import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from ..extensions import db
from ..models import Facility, ResourceReport
from ..utils.decorators import reporter_required
from ..utils.validators import sanitize_integer, validate_report_payload

reporter_bp = Blueprint("reporter", __name__)


def _parse_identity():
    """Parse JWT identity, handling both dict and JSON string formats."""
    identity = get_jwt_identity()
    if isinstance(identity, str):
        try:
            return json.loads(identity)
        except (json.JSONDecodeError, TypeError):
            return {}
    return identity or {}


@reporter_bp.post("/reports")
@reporter_required
def create_report():
    identity = _parse_identity()
    role = identity.get("role")
    reporter_facility_id = identity.get("facility_id")
    data = request.get_json() or {}

    errors = validate_report_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    facility_id = sanitize_integer(data.get("facility_id"), min_val=1)
    if facility_id is None:
        return jsonify({"error": "Invalid facility_id."}), 400

    if role == "reporter":
        if not reporter_facility_id:
            return jsonify({"error": "Reporter is not linked to a facility."}), 403
        if reporter_facility_id != facility_id:
            return jsonify({"error": "Reporter can only submit for their facility."}), 403

    facility = Facility.query.get(facility_id)
    if not facility:
        return jsonify({"error": "Facility not found."}), 404

    # Sanitize resource values
    icu_beds = sanitize_integer(
        data.get("icu_beds_available"), min_val=0, max_val=10000)
    ventilators = sanitize_integer(
        data.get("ventilators_available"), min_val=0, max_val=10000)
    staff = sanitize_integer(data.get("staff_on_duty"),
                             min_val=0, max_val=10000)

    # Upsert: overwrite latest snapshot for this facility.
    report = ResourceReport.query.filter_by(facility_id=facility_id).first()
    payload = {
        "icu_beds_available": icu_beds,
        "ventilators_available": ventilators,
        "staff_on_duty": staff,
    }

    if report:
        for field, value in payload.items():
            setattr(report, field, value)
    else:
        report = ResourceReport(facility_id=facility_id, **payload)
        db.session.add(report)

    db.session.commit()

    return jsonify({"report": report.to_dict()}), 201


@reporter_bp.get("/reports/me")
@reporter_required
def get_my_latest_report():
    identity = _parse_identity()
    role = identity.get("role")
    facility_id = identity.get("facility_id")

    if role == "reporter":
        if not facility_id:
            return jsonify({"error": "Reporter is not linked to a facility."}), 403
    else:
        # Admins/monitors must specify facility_id in query for this endpoint.
        facility_id = request.args.get("facility_id", type=int)
        if not facility_id:
            return jsonify({"error": "facility_id is required for this request."}), 400

    report = (
        ResourceReport.query.filter_by(facility_id=facility_id)
        .order_by(ResourceReport.updated_at.desc())
        .first()
    )
    if not report:
        return jsonify({"error": "No report found."}), 404

    return jsonify({"report": report.to_dict()})
