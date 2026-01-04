"""Blueprint registration."""
from flask import Flask

from .admin import admin_bp
from .auth import auth_bp
from .monitor import monitor_bp
from .reporter import reporter_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(reporter_bp, url_prefix="/api/reporter")
    app.register_blueprint(monitor_bp, url_prefix="/api/monitor")
