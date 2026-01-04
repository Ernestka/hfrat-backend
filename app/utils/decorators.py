"""Custom decorators for role-based access control."""
from __future__ import annotations

import json
from functools import wraps
from typing import Iterable

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request


def _get_identity_dict():
    """Parse JWT identity, handling both dict and JSON string formats."""
    identity = get_jwt_identity()
    if isinstance(identity, str):
        try:
            return json.loads(identity)
        except (json.JSONDecodeError, TypeError):
            return {}
    return identity or {}


def _role_guard(allowed_roles: Iterable[str]):
    allowed = set(allowed_roles)

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            identity = _get_identity_dict()
            if identity.get("role") not in allowed:
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def role_required(roles: Iterable[str]):
    """Generic role guard; kept for compatibility."""
    return _role_guard(roles)


def admin_required(fn):
    return _role_guard({"admin"})(fn)


def reporter_required(fn):
    # Admins can act on reporter endpoints for oversight/support.
    return _role_guard({"reporter", "admin"})(fn)


def monitor_required(fn):
    # Admins can act on monitor endpoints as well.
    return _role_guard({"monitor", "admin"})(fn)
