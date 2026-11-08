"""Delivery-layer tests for GET /users/<user_id>/matches.

Hits the Flask test client against an in-memory sqlite app built via the
factory. Verifies the contract the frontend Dashboard will rely on:
  - 200 OK
  - matches is an array of cards with title, company, location, date_posted, score
  - matches are sorted best-fit-first
  - unknown user returns an empty array
Run: pytest tests/delivery/test_matches_api.py
"""
from datetime import datetime, timedelta, timezone

from extension import db
from infrastructure.app_factory import create_app
from infrastructure.job_match_repository import SqlAlchemyJobMatchRepository
from domain.matched_job import MatchedJob


def _persist(app, matched_job: MatchedJob):
    with app.app_context():
        SqlAlchemyJobMatchRepository(db).save(matched_job)


def _mk(mid, user_id="u-1", score=80, title="Senior Frontend Engineer",
         company="Linear", location="Remote (EU)", created_at=None):
    return MatchedJob(
        id=mid, user_id=user_id, title=title, company=company, location=location,
        job_url=f"https://x/{mid}", date_posted="2026-06-28", score=score,
        created_at=created_at or (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)),
    )


def test_default_window_excludes_matches_older_than_thirty_days():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        old = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=40)
        _persist(app, _mk(1, created_at=old))
        _persist(app, _mk(2, created_at=datetime.now(timezone.utc).replace(tzinfo=None)))
    client = app.test_client()

    default = client.get("/users/u-1/matches").get_json()["matches"]
    assert [m["id"] for m in default] == [2]

    older = client.get("/users/u-1/matches?older=1").get_json()["matches"]
    assert sorted(m["id"] for m in older) == [1, 2]


def test_get_matches_returns_200_with_card_shape():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    _persist(app, _mk(1))
    client = app.test_client()

    resp = client.get("/users/u-1/matches")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["user_id"] == "u-1"
    assert isinstance(body["matches"], list)
    card = body["matches"][0]
    for key in ("id", "title", "company", "location", "job_url", "date_posted", "score"):
        assert key in card, f"missing key {key}"
    assert card["title"] == "Senior Frontend Engineer"
    assert card["company"] == "Linear"
    assert card["location"] == "Remote (EU)"
    assert card["date_posted"] == "2026-06-28"
    assert card["score"] == 80


def test_matches_come_back_sorted_best_fit_first():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    _persist(app, _mk(1, score=82))
    _persist(app, _mk(2, score=96))
    _persist(app, _mk(3, score=88))
    client = app.test_client()

    resp = client.get("/users/u-1/matches")

    scores = [m["score"] for m in resp.get_json()["matches"]]
    assert scores == [96, 88, 82]


def test_unknown_user_returns_empty_matches_array():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    _persist(app, _mk(1, user_id="u-1"))
    client = app.test_client()

    resp = client.get("/users/does-not-exist/matches")

    assert resp.status_code == 200
    assert resp.get_json() == {"user_id": "does-not-exist", "email": None, "matches": []}


def test_unscored_match_serializes_score_as_null():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    _persist(app, _mk(1, score=None))
    client = app.test_client()

    resp = client.get("/users/u-1/matches")

    assert resp.get_json()["matches"][0]["score"] is None


def _signup(app, payload):
    """Create a real user row through the API (welcome email patched out)."""
    from unittest.mock import patch
    with app.app_context():
        with patch("infrastructure.app_factory.send_welcome_email"):
            resp = app.test_client().post("/user", json=payload)
        assert resp.status_code == 201
        return resp.get_json()["user_id"]


def test_matches_payload_includes_the_users_email():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    user_id = _signup(app, {"email": "ada@lovelace.dev", "position": "Dev",
                            "location": "Berlin", "jobType": "full-time"})
    _persist(app, _mk(1, user_id=user_id))
    client = app.test_client()

    resp = client.get(f"/users/{user_id}/matches")

    body = resp.get_json()
    assert body["email"] == "ada@lovelace.dev"