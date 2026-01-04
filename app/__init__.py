"""Flask application factory."""
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request
from flask_jwt_extended.exceptions import JWTExtendedException
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from .config import config_by_name
from .extensions import cors, db, jwt, migrate
from .routes import register_blueprints
from .seed import register_seed_commands


def create_app(config_name: str | None = None) -> Flask:
    """Application factory for the Flask app."""
    app = Flask(__name__)

    env = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(
        env, config_by_name["development"]))

    # Initialize extensions
    # Build allowed origins list - always include Netlify and localhost for dev
    allowed_origins = app.config.get("CORS_ORIGINS", [])
    # Ensure production domains are included
    if env == "production":
        if "https://hfrat.netlify.app" not in allowed_origins:
            allowed_origins = list(allowed_origins) + \
                ["https://hfrat.netlify.app"]

    cors.init_app(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": False,
            "max_age": 3600
        }
    })
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Auto-create tables on startup (for Render free tier without shell access)
    try:
        with app.app_context():
            db.create_all()
            # Auto-seed admin if not exists
            from .models import User
            admin = User.query.filter_by(email="admin@example.com").first()
            if not admin:
                admin = User(email="admin@example.com", role="admin")
                admin.set_password("Admin@123")
                db.session.add(admin)
                db.session.commit()
                app.logger.info(
                    "Created default admin user: admin@example.com")
    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")

    # Configure logging
    configure_logging(app)

    # Register middleware for secure headers
    register_security_middleware(app)

    register_blueprints(app)
    register_error_handlers(app)
    register_shellcontext(app)
    register_seed_commands(app)

    @app.get("/")
    def index():
        return {
            "name": "HFRAT API",
            "version": "1.0.0",
            "status": "running",
            "environment": env,
            "endpoints": {
                "auth": "/api/auth",
                "admin": "/api/admin",
                "reporter": "/api/reporter",
                "monitor": "/api/monitor",
                "health": "/health"
            }
        }

    @app.get("/health")
    def health_check():
        try:
            # Test database connection
            db.session.execute(db.text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"

        return {
            "status": "ok",
            "environment": env,
            "database": db_status,
            "cors_origins": app.config.get("CORS_ORIGINS", [])
        }

    return app


def configure_logging(app: Flask) -> None:
    """Configure application logging."""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists("logs"):
            os.mkdir("logs")

        # File handler for application logs
        file_handler = RotatingFileHandler(
            "logs/hfrat.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("HFRAT application startup")
    else:
        # Console logging for development
        app.logger.setLevel(logging.DEBUG)


def register_security_middleware(app: Flask) -> None:
    """Register middleware for security headers."""
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Enforce HTTPS (only in production)
        if not app.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

    @app.before_request
    def log_request_info():
        """Log incoming request information."""
        if not app.debug:
            app.logger.info(
                "Request: %s %s - IP: %s - User-Agent: %s",
                request.method,
                request.path,
                request.remote_addr,
                request.headers.get("User-Agent", "Unknown")
            )


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        app.logger.warning("Bad request: %s", str(error))
        message = error.description if hasattr(
            error, "description") else "Bad request"
        return jsonify({"error": message}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        app.logger.warning("Unauthorized access attempt: %s", str(error))
        return jsonify({"error": "Unauthorized. Please log in."}), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        app.logger.warning(
            "Forbidden access attempt: %s - Path: %s",
            request.remote_addr,
            request.path
        )
        return jsonify({"error": "Forbidden. You don't have permission to access this resource."}), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        app.logger.info("Resource not found: %s", request.path)
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server errors."""
        app.logger.error(
            "Internal server error: %s - Path: %s",
            str(error),
            request.path,
            exc_info=True
        )
        db.session.rollback()  # Rollback any failed database transactions
        return jsonify({"error": "Internal server error. Please try again later."}), 500

    @app.errorhandler(JWTExtendedException)
    def handle_jwt_error(error):
        """Handle JWT-specific errors."""
        app.logger.warning("JWT error: %s", str(error))
        return jsonify({"error": "Authentication failed. Please log in again."}), 401

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        """Handle database errors."""
        app.logger.error(
            "Database error: %s - Path: %s",
            str(error),
            request.path,
            exc_info=True
        )
        db.session.rollback()
        return jsonify({"error": "Database error occurred. Please try again."}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle any unexpected errors."""
        # Don't catch HTTPExceptions, let them be handled by their specific handlers
        if isinstance(error, HTTPException):
            return error

        app.logger.critical(
            "Unexpected error: %s - Path: %s",
            str(error),
            request.path,
            exc_info=True
        )
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred. Please contact support."}), 500


def register_shellcontext(app: Flask) -> None:
    from .models import Facility, ResourceReport, User

    @app.shell_context_processor
    def shell_context():
        return {"db": db, "User": User, "Facility": Facility, "ResourceReport": ResourceReport}
