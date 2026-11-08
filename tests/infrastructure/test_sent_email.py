"""tests for the sent_at stamp: SentEmail rows written for old emails carry
NULL, every new one is stamped at send time (the dashboard's 30-day window
could then also be derived from this table).
Run: pytest tests/infrastructure/test_sent_email.py
"""
from extension import db
from infrastructure.app_factory import create_app
from db.database_service import UserEmailManager
from db.models import SentEmail


def test_add_sent_email_stamps_sent_at():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        UserEmailManager().add_sent_email("a@b.dev", "https://jobs/1", "Dev", "Berlin")

        row = SentEmail.query.one()
        assert row.sent_at is not None


def test_sent_at_is_saved_utc_naive_for_comparisons():
    app = create_app(db_uri="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        UserEmailManager().add_sent_email("a@b.dev", "https://jobs/2", "Dev", "Berlin")
        stamps = [r.sent_at for r in SentEmail.query.all()]
        assert all(stamp.tzinfo is None for stamp in stamps)
