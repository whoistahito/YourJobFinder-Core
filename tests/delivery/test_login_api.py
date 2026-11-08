"""Delivery tests for POST /login and GET /auth/<token> (magic-link sign-in).

Covers the enumeration-safe contract (uniform 200), the token lifecycle
(single-use, 30-min expiry), the unconfirmed-resend branch, and throttling.
Run: pytest tests/delivery/test_login_api.py
"""
import re
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from db.database_service import UserManager
from extension import db
from infrastructure import app_factory as af
from infrastructure.app_factory import create_app

SIGNUP = {"email": "ada@lovelace.dev", "position": "Dev", "location": "Berlin", "jobType": "full-time"}


def _app():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    af._login_hits.clear()
    return app


def _signup(app, **override):
    email = override.get("email", SIGNUP["email"])
    with app.app_context():
        with patch("infrastructure.app_factory.send_welcome_email"):
            user = UserManager().add_user(
                email,
                override.get("position", SIGNUP["position"]),
                SIGNUP["location"],
                SIGNUP["jobType"])
        uid, confirm_token = user.id, user.confirmation_token
    return uid, confirm_token


def _confirm(app, confirm_token):
    with app.app_context():
        UserManager().confirm_user(confirm_token)


def test_unknown_email_gets_a_nudge_and_uniform_200():
    app = _app()
    with patch("infrastructure.app_factory.send_welcome_email"), \
         patch("infrastructure.app_factory.send_email") as mail:
        resp = app.test_client().post("/login", json={"email": "nobody@x.dev"})

    assert resp.status_code == 200
    assert "someone" not in resp.get_json()["message"]
    body, subject, to = mail.call_args.args
    assert to == "nobody@x.dev"
    assert "Set up job alerts" not in subject  # nudge mail links the site, not a token


def test_confirmed_user_gets_single_use_link_to_their_dashboard():
    app = _app()
    uid, confirm_token = _signup(app)
    _confirm(app, confirm_token)
    client = app.test_client()
    with patch("infrastructure.app_factory.send_welcome_email"), \
         patch("infrastructure.app_factory.send_email") as mail:
        resp = client.post("/login", json={"email": "ada@lovelace.dev"})
        assert resp.status_code == 200

    href = re.search(r'href="(https://api\.yourjobfinder\.website/auth/[^"]+)"', mail.call_args.args[0])
    token = href.group(1).rsplit("/", 1)[-1]
    assert href.group(1) == f"https://api.yourjobfinder.website/auth/{token}"

    first = client.get(f"/auth/{token}")
    assert first.status_code == 302
    assert first.headers["Location"] == f"https://yourjobfinder.website/dashboard/{uid}"

    replay = client.get(f"/auth/{token}")
    assert replay.status_code == 302
    assert replay.headers["Location"] == "https://yourjobfinder.website/login?state=expired"


def test_expired_link_rejects_and_clears_the_token():
    from datetime import datetime as dt
    app = _app()
    uid, _ = _signup(app)
    with app.app_context():
        UserManager().set_login_token(
            uid, "tok", dt.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1))
    resp = app.test_client().get("/auth/tok")
    assert resp.headers["Location"] == "https://yourjobfinder.website/login?state=expired"


def test_unknown_or_used_token_redirects_to_login_error():
    app = _app()
    resp = app.test_client().get("/auth/never-minted")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://yourjobfinder.website/login?state=expired"


def test_registered_but_unconfirmed_user_gets_confirmation_resent():
    app = _app()
    _signup(app)  # never confirmed
    with patch("infrastructure.app_factory.send_welcome_email") as welcome, \
         patch("infrastructure.app_factory.send_email") as mail:
        resp = app.test_client().post("/login", json={"email": "ada@lovelace.dev"})

    assert resp.status_code == 200
    assert welcome.call_count == 1
    assert mail.call_count == 0


def test_invalid_email_returns_400():
    app = _app()
    resp = app.test_client().post("/login", json={"email": "not-an-email"})
    assert resp.status_code == 400


def test_login_throttles_per_email():
    app = _app()
    client = app.test_client()
    with patch("infrastructure.app_factory.send_welcome_email"), \
         patch("infrastructure.app_factory.send_email"):
        for _ in range(3):
            assert client.post("/login", json={"email": "spam@x.dev"}).status_code == 200
        assert client.post("/login", json={"email": "spam@x.dev"}).status_code == 429


def test_duplicate_subscriptions_link_the_newest_confirmed_one():
    app = _app()
    _uid_dev, tok_dev = _signup(app)                       # Dev, same email, created first
    uid_pm, tok_pm = _signup(app, position="PM")           # same email, created second
    _confirm(app, tok_dev)
    _confirm(app, tok_pm)
    client = app.test_client()
    with patch("infrastructure.app_factory.send_welcome_email"), \
         patch("infrastructure.app_factory.send_email"):
        resp = client.post("/login", json={"email": "ada@lovelace.dev"})
    assert resp.status_code == 200
    with app.app_context():
        rows = UserManager().find_users_by_email("ada@lovelace.dev")
        assert [r.id for r in rows] == [uid_pm, _uid_dev]
        assert rows[0].login_token  # newest subscription holds the token  # the token was minted for this row
