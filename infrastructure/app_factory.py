"""Application factory — builds the Flask app with DB + routes.

Split out of `app.py` so tests can spin up Flask against an in-memory sqlite.
`app.py` just calls `create_app()` with the prod DB URI (reached via the
autossh sidecar in prod).
"""
from __future__ import annotations

import re
import secrets
import time
from typing import Optional
from datetime import datetime, timedelta, timezone

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
from email_manager import send_email
from credential import CloudflareCredential
from html_render import get_login_message, get_signup_nudge_message


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


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_LOGIN_WINDOW_S = 900
_LOGIN_LIMIT = 3

# in-memory only (resets per worker restart) — enough to stop link spam
_login_hits: dict[str, list[float]] = {}


def _mail_ok(email: str) -> bool:
    now = time.monotonic()
    hits = [t for t in _login_hits.get(email, []) if now - t < _LOGIN_WINDOW_S]
    if len(hits) >= _LOGIN_LIMIT:
        _login_hits[email] = hits
        return False
    hits.append(now)
    _login_hits[email] = hits
    return True


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

    @app.route("/login", methods=["POST"])
    def request_login_link():
        data = request.json or {}
        email = str(data.get("email") or "").strip().lower()
        if not _EMAIL_RE.match(email):
            return jsonify({"message": "Enter a valid email address."}), 400
        if not _mail_ok(email):
            return jsonify({"message": "Too many attempts — try again later."}), 429

        users = user_manager.find_users_by_email(email)
        sender = CloudflareCredential.get_welcome_from()
        try:
            if not users:
                # Same 200 for known and unknown emails: no enumeration signal.
                send_email(
                    get_signup_nudge_message(),
                    "Start scanning for your job matches",
                    email,
                    sender=sender,
                )
            elif confirmed := next((u for u in users if u.is_confirmed), None):
                token = secrets.token_urlsafe(32)
                expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)
                user_manager.set_login_token(confirmed.id, token, expires)
                send_email(
                    get_login_message(f"https://api.yourjobfinder.website/auth/{token}"),
                    "Your sign-in link for Your Job Finder",
                    email,
                    sender=sender,
                )
            else:
                # Registered but never confirmed: resend the confirmation.
                send_welcome_email(users[0])
        except Exception as e:
            print(e)
            return jsonify({"message": "Could not send the email. Please try again shortly."}), 500

        return jsonify({
            "message": "If that email has a subscription, a sign-in link is on its way. Check your inbox."
        }), 200

    @app.route("/auth/<token>", methods=["GET"])
    def login_via_token(token):
        user = user_manager.consume_login_token(token)
        if user:
            return redirect(f"https://yourjobfinder.website/dashboard/{user.id}")
        return redirect("https://yourjobfinder.website/login?state=expired")

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