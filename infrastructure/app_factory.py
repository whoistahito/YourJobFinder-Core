"""Application factory — builds the Flask app with DB + routes.

Split out of `app.py` so tests can spin up Flask against an in-memory sqlite.
`app.py` just calls `create_app()` with the prod DB URI (reached via the
autossh sidecar in prod).
"""
from __future__ import annotations

from typing import Optional

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS

# Register ORM models with SQLAlchemy metadata BEFORE pulling in `db` instance.
# (Plain `import db.models` would otherwise shadow `extension.db` below.)
import db.models  # noqa: F401
import infrastructure.job_match_repository  # noqa: F401
from db.database_service import UserManager
from extension import db, migrate
from domain.job_match_repository import JobMatchRepository
from infrastructure.job_match_repository import SqlAlchemyJobMatchRepository
from application.list_user_matches import ListUserMatches
from notifications import send_welcome_email


def create_app(
    db_uri: Optional[str] = None,
    job_match_repo: Optional[JobMatchRepository] = None,
) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri or "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    user_manager = UserManager()
    repo = job_match_repo if job_match_repo is not None else SqlAlchemyJobMatchRepository(db)

    _register_routes(app, user_manager, repo)
    return app


def _register_routes(app: Flask, user_manager: UserManager, repo: JobMatchRepository) -> None:
    @app.route("/user", methods=["POST"])
    def add_user():
        data = request.json
        email = data.get("email")
        position = data.get("position")
        location = data.get("location")
        job_type = data.get("jobType")
        country_code = data.get("countryCode")
        skills = data.get("skills")
        experience = data.get("experience")
        education = data.get("education")
        try:
            if email is None or position is None or location is None or job_type is None:
                return jsonify({"message": "Invalid request"}), 400
            user = user_manager.add_user(email, position, location, job_type, country_code, skills, experience, education)
            if user is not None:
                # Event-driven: send the confirmation email now instead of polling.
                # Don't fail the signup if SMTP hiccups — the user row is committed.
                # ponytail: synchronous send; move behind a queue if it gets slow.
                try:
                    send_welcome_email(user)
                except Exception as e:
                    print(f"welcome email failed for {email}: {e}")
                user_id = user.id
            else:
                # Duplicate signup (same email+position+location): surface the
                # existing row's id so the frontend can still open the dashboard.
                existing = user_manager.user_exists(email, position, location)
                user_id = existing.id if existing else None
            # The id is how the frontend reaches GET /users/<id>/matches — the
            # signup response is the only moment we can hand it over.
            return jsonify({"message": "User added successfully!", "user_id": user_id}), 201
        except Exception as e:
            print(e)
            return jsonify({"message": str(e)}), 500

    @app.route("/user", methods=["DELETE"])
    def delete_user():
        data = request.json
        email = data.get("email")
        position = data.get("position")
        location = data.get("location")
        try:
            if email is None or position is None or location is None:
                raise Exception
            user_manager.delete_user(email, position, location)
            return jsonify({"message": "User added successfully!"}), 201
        except Exception as e:
            print(e)
            return jsonify({"message": e}), 500

    @app.route("/confirm/<token>", methods=["GET"])
    def confirm_email(token):
        user = user_manager.confirm_user(token)
        if user:
            # uid travels along so the success page can link /dashboard/<uid>.
            return redirect(f"https://yourjobfinder.website/confirm-email/success?uid={user.id}")
        else:
            return redirect("https://yourjobfinder.website/confirm-email/error")

    @app.route("/", methods=["GET"])
    def index():
        return redirect("https://yourjobfinder.website")

    @app.route("/users/<user_id>/matches", methods=["GET"])
    def list_user_matches(user_id: str):
        matches = ListUserMatches(repo).execute(user_id)
        # Sidebar needs the user's email; None for an unknown user.
        user = user_manager.get_user(user_id)
        return jsonify({
            "user_id": user_id,
            "email": user.email if user else None,
            "matches": [
                {
                    "id": m.id,
                    "title": m.title,
                    "company": m.company,
                    "location": m.location,
                    "job_url": m.job_url,
                    "date_posted": m.date_posted,
                    "score": m.score,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in matches
            ],
        })