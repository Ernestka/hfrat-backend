"""Admin-only routes."""
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Facility, User, UserRole
from ..utils.decorators import admin_required
from ..utils.validators import (
    sanitize_email,
    sanitize_integer,
    sanitize_string,
    validate_facility_payload,
)

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/users")
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [user.to_dict() for user in users]})


@admin_bp.post("/facilities")
@admin_required
def create_facility():
    data = request.get_json() or {}

    # Validate payload
    errors = validate_facility_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    name = sanitize_string(data.get("name"), max_length=150)
    country = sanitize_string(data.get("country"), max_length=120) or None
    city = sanitize_string(data.get("city"), max_length=120) or None

    if Facility.query.filter_by(name=name).first():
        return jsonify({"error": "Facility already exists."}), 409

    facility = Facility(name=name, country=country, city=city)
    db.session.add(facility)
    db.session.commit()

    return jsonify({"facility": facility.to_dict()}), 201


@admin_bp.get("/facilities")
@admin_required
def list_facilities():
    facilities = Facility.query.order_by(Facility.name.asc()).all()
    return jsonify({"facilities": [facility.to_dict() for facility in facilities]})


@admin_bp.post("/users")
@admin_required
def create_user():
    data = request.get_json() or {}
    email = sanitize_email(data.get("email"))
    temp_password = data.get("password") or data.get("temporary_password")
    role_value = sanitize_string(data.get("role"), max_length=50).lower()
    facility_id = sanitize_integer(data.get("facility_id"), min_val=1)

    if not email:
        return jsonify({"error": "email is required."}), 400
    if not temp_password:
        return jsonify({"error": "temporary password is required."}), 400

    try:
        role = UserRole(role_value)
    except ValueError:
        return jsonify({"error": "Invalid role."}), 400

    if role == UserRole.REPORTER:
        if facility_id is None:
            return jsonify({"error": "facility_id is required for reporter."}), 400
        if not Facility.query.get(facility_id):
            return jsonify({"error": "Facility not found."}), 404
    else:
        facility_id = None

    new_user = User(email=email, role=role, facility_id=facility_id)
    new_user.set_password(temp_password)

    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already registered."}), 409

    return jsonify({"user": new_user.to_dict()}), 201


@admin_bp.delete("/facilities/<int:facility_id>")
@admin_required
def delete_facility(facility_id: int):
    facility = Facility.query.get(facility_id)
    if not facility:
        return jsonify({"error": "Facility not found."}), 404

    db.session.delete(facility)
    db.session.commit()
    return jsonify({"message": "Facility deleted."})
