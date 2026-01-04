"""Authentication routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    jwt_required,
)
from sqlalchemy.exc import IntegrityError

from ..extensions import db, jwt
from ..models import Facility, User, UserRole
from ..utils.validators import (
    sanitize_email,
    sanitize_integer,
    sanitize_string,
    validate_user_payload,
)

auth_bp = Blueprint("auth", __name__)
revoked_tokens: set[str] = set()


@jwt.token_in_blocklist_loader
def is_token_revoked(jwt_header, jwt_payload):
    return jwt_payload.get("jti") in revoked_tokens


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    errors = validate_user_payload(data, require_password=True)
    if errors:
        return jsonify({"errors": errors}), 400

    email = sanitize_email(data.get("email"))
    password = data.get("password")
    role_value = sanitize_string(
        data.get("role") or UserRole.REPORTER.value, max_length=50).lower()
    facility_id = sanitize_integer(data.get("facility_id"), min_val=1)

    if data.get("facility_id") is not None and facility_id is None:
        return jsonify({"error": "facility_id must be a positive integer."}), 400

    try:
        role = UserRole(role_value)
    except ValueError:
        return jsonify({"error": "Invalid role."}), 400

    if role != UserRole.REPORTER and facility_id is not None:
        return jsonify({"error": "facility_id allowed only for reporter role."}), 400

    if facility_id is not None and not Facility.query.get(facility_id):
        return jsonify({"error": "Facility not found."}), 404

    user = User(email=email, role=role, facility_id=facility_id)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already registered."}), 409

    token = create_access_token(
        identity={"id": user.id, "role": user.role.value,
                  "facility_id": user.facility_id}
    )
    return (
        jsonify(
            {
                "access_token": token,
                "role": user.role.value,
                "facility_id": user.facility_id,
                "user": user.to_dict(),
            }
        ),
        201,
    )


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    errors = validate_user_payload(data, require_password=True)
    if errors:
        return jsonify({"errors": errors}), 400

    email = sanitize_email(data.get("email"))
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials."}), 401

    token = create_access_token(
        identity={"id": user.id, "role": user.role.value,
                  "facility_id": user.facility_id}
    )
    return jsonify({"access_token": token, "role": user.role.value, "facility_id": user.facility_id}), 200


@auth_bp.post("/logout")
@jwt_required()
def logout():
    jti = get_jwt().get("jti")
    if jti:
        revoked_tokens.add(jti)
    # Placeholder: persist revocation list (e.g., Redis/DB) in production.
    return jsonify({"message": "Logged out"}), 200
