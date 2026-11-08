"""Delivery tests for GET /users/<user_id>/profile (dashboard profile drawer).

The response mirrors the signup form: role, job type, location, plus the
optional boost data (skills / experiences / educations).
Run: pytest tests/delivery/test_profile_api.py
"""
from unittest.mock import patch

from db.database_service import UserManager
from extension import db
from infrastructure.app_factory import create_app

SIGNUP = {"email": "ada@lovelace.dev", "position": "Dev", "location": "Berlin",
          "jobType": "full-time", "skills": ["Python", "SQL"],
          "experience": ["3 years Backend"], "education": ["BSc CS"]}


def _signup(app, payload=SIGNUP):
    with app.app_context():
        with patch("infrastructure.app_factory.send_welcome_email"):
            resp = app.test_client().post("/user", json=payload)
        assert resp.status_code == 201
        return resp.get_json()["user_id"]


def test_profile_returns_exactly_what_the_user_signed_up_with():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    uid = _signup(app)

    resp = app.test_client().get(f"/users/{uid}/profile")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["email"] == "ada@lovelace.dev"
    assert body["position"] == "Dev"
    assert body["location"] == "Berlin"
    assert body["job_type"] == "full-time"
    assert body["skills"] == ["Python", "SQL"]
    assert body["experiences"] == ["3 years Backend"]
    assert body["educations"] == ["BSc CS"]


def test_profile_without_boost_data_has_empty_lists():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    uid = _signup(app, {"email": "plain@x.dev", "position": "PM", "location": "Paris", "jobType": "internship"})

    body = app.test_client().get(f"/users/{uid}/profile").get_json()
    assert body["skills"] == []
    assert body["experiences"] == []
    assert body["educations"] == []


def test_unknown_user_profile_is_404():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    assert app.test_client().get("/users/does-not-exist/profile").status_code == 404
