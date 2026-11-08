"""Signup now sends the confirmation email in-request (event-driven), replacing
the old worker poll. Verify it fires once per new user and not for duplicates,
and that the response carries the user_id for the dashboard link.
Run: pytest tests/delivery/test_signup_welcome_email.py
"""
from unittest.mock import patch

from extension import db
from infrastructure.app_factory import create_app

PAYLOAD = {"email": "a@b.com", "position": "Dev", "location": "Berlin", "jobType": "full"}


def _client():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    return app.test_client()


def test_signup_sends_welcome_email_once_and_not_for_duplicates():
    client = _client()
    with patch("infrastructure.app_factory.send_welcome_email") as send:
        assert client.post("/user", json=PAYLOAD).status_code == 201
        assert send.call_count == 1
        # Same email/position/location → add_user returns None → no second email.
        assert client.post("/user", json=PAYLOAD).status_code == 201
        assert send.call_count == 1


def test_signup_response_returns_the_user_id():
    client = _client()
    with patch("infrastructure.app_factory.send_welcome_email"):
        first = client.post("/user", json=PAYLOAD)
        duplicate = client.post("/user", json=PAYLOAD)

    # New signup → the created user's id…
    body = first.get_json()
    assert body["user_id"]
    new_id = body["user_id"]
    # …duplicate signup → the *existing* user's id, so "already subscribed"
    # users can still open the dashboard.
    assert duplicate.get_json()["user_id"] == new_id


def test_signup_succeeds_even_if_email_send_fails():
    client = _client()
    with patch("infrastructure.app_factory.send_welcome_email", side_effect=RuntimeError("smtp down")):
        assert client.post("/user", json=PAYLOAD).status_code == 201
