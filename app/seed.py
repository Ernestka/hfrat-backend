"""Seed helpers for the application."""
import os
import click

from .extensions import db
from .models import User, Facility


def register_seed_commands(app):
    @app.cli.command("seed-admin")
    @click.option("--email", default=None, help="Admin email address")
    @click.option("--password", default=None, help="Admin password")
    def seed_admin(email: str | None, password: str | None):
        """Seed a default admin user."""
        seed_email = email or os.getenv(
            "DEFAULT_ADMIN_EMAIL", "admin@example.com")
        seed_password = password or os.getenv(
            "DEFAULT_ADMIN_PASSWORD", "change-me")

        existing = User.query.filter_by(email=seed_email).first()
        if existing:
            app.logger.info("Admin already exists: %s", seed_email)
            return

        admin_user = User(email=seed_email, role="admin")
        admin_user.set_password(seed_password)

        db.session.add(admin_user)
        db.session.commit()

        app.logger.info("Created admin user: %s", seed_email)

    @app.cli.command("seed-facilities")
    def seed_facilities():
        """Seed sample facilities."""
        facilities_data = [
            {"name": "City General Hospital", "country": "USA", "city": "New York"},
            {"name": "St. Mary's Medical Center",
                "country": "USA", "city": "Los Angeles"},
            {"name": "Royal Victoria Hospital", "country": "UK", "city": "London"},
            {"name": "Toronto General Hospital",
                "country": "Canada", "city": "Toronto"},
            {"name": "Sydney Medical Center",
                "country": "Australia", "city": "Sydney"},
        ]

        created_count = 0
        for fac_data in facilities_data:
            existing = Facility.query.filter_by(name=fac_data["name"]).first()
            if existing:
                app.logger.info("Facility already exists: %s",
                                fac_data["name"])
                continue

            facility = Facility(**fac_data)
            db.session.add(facility)
            created_count += 1
            app.logger.info("Created facility: %s", fac_data["name"])

        if created_count > 0:
            db.session.commit()
            app.logger.info("Created %d facilities", created_count)
        else:
            app.logger.info("No new facilities created")

    @app.cli.command("seed-users")
    def seed_users():
        """Seed sample REPORTER and MONITOR users."""
        # First ensure we have facilities
        facilities = Facility.query.all()
        if not facilities:
            app.logger.warning(
                "No facilities found. Please run 'flask seed-facilities' first.")
            return

        users_data = [
            {
                "email": "reporter1@example.com",
                "password": "reporter123",
                "role": "reporter",
                "facility_name": "City General Hospital"
            },
            {
                "email": "reporter2@example.com",
                "password": "reporter123",
                "role": "reporter",
                "facility_name": "St. Mary's Medical Center"
            },
            {
                "email": "reporter3@example.com",
                "password": "reporter123",
                "role": "reporter",
                "facility_name": "Royal Victoria Hospital"
            },
            {
                "email": "monitor1@example.com",
                "password": "monitor123",
                "role": "monitor",
                "facility_name": None
            },
            {
                "email": "monitor2@example.com",
                "password": "monitor123",
                "role": "monitor",
                "facility_name": None
            },
        ]

        created_count = 0
        for user_data in users_data:
            existing = User.query.filter_by(email=user_data["email"]).first()
            if existing:
                app.logger.info("User already exists: %s", user_data["email"])
                continue

            facility_id = None
            if user_data["facility_name"]:
                facility = Facility.query.filter_by(
                    name=user_data["facility_name"]).first()
                if facility:
                    facility_id = facility.id
                else:
                    app.logger.warning(
                        "Facility '%s' not found for user %s",
                        user_data["facility_name"],
                        user_data["email"]
                    )
                    continue

            user = User(
                email=user_data["email"],
                role=user_data["role"],
                facility_id=facility_id
            )
            user.set_password(user_data["password"])
            db.session.add(user)
            created_count += 1
            app.logger.info("Created %s user: %s",
                            user_data["role"], user_data["email"])

        if created_count > 0:
            db.session.commit()
            app.logger.info("Created %d users", created_count)
        else:
            app.logger.info("No new users created")

    @app.cli.command("seed-all")
    def seed_all():
        """Seed all data: admin, facilities, and users."""
        app.logger.info("Starting complete database seeding...")

        # Seed admin
        app.logger.info("Seeding admin user...")
        with app.app_context():
            seed_admin.callback(None, None)

        # Seed facilities
        app.logger.info("Seeding facilities...")
        with app.app_context():
            seed_facilities.callback()

        # Seed users
        app.logger.info("Seeding sample users...")
        with app.app_context():
            seed_users.callback()

        app.logger.info("Database seeding complete!")
