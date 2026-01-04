"""Entry point for running the Flask app."""
import os

from app import create_app

# Determine environment from FLASK_ENV (defaults to 'development')
env = os.getenv("FLASK_ENV", "development")

# Create the app instance - this is what gunicorn imports as run:app
app = create_app(env)

if __name__ == "__main__":
    # Only enable debug mode when running directly in development
    debug = env == "development"
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug)
