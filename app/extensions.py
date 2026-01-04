"""Flask extension instances."""
import json
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()


@jwt.user_identity_loader
def user_identity_lookup(user_data):
    """Convert user dict to JSON string for JWT identity."""
    if isinstance(user_data, dict):
        return json.dumps(user_data)
    return str(user_data)


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Load user from JWT identity."""
    identity = jwt_data["sub"]
    try:
        return json.loads(identity) if isinstance(identity, str) else identity
    except (json.JSONDecodeError, TypeError):
        return {"id": identity, "role": None, "facility_id": None}
