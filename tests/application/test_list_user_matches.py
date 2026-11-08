"""Application-layer tests for ListUserMatches.

The use case depends only on the repository *interface*, so we feed it an
in-memory fake. Nothing here touches Flask, SQLAlchemy, or the network.
Run: pytest tests/application/test_list_user_matches.py
"""
from datetime import datetime, timezone

from domain.matched_job import MatchedJob
from domain.job_match_repository import JobMatchRepository
from application.list_user_matches import ListUserMatches


class InMemoryJobMatchRepository(JobMatchRepository):
    def __init__(self):
        self._rows: list[MatchedJob] = []

    def list_for_user(self, user_id: str, since=None) -> list[MatchedJob]:
        return [m for m in self._rows if m.user_id == user_id]

    def save(self, matched_job: MatchedJob) -> MatchedJob:
        self._rows = [m for m in self._rows if m.id != matched_job.id]
        self._rows.append(matched_job)
        return matched_job


def _mk(mid, score):
    return MatchedJob(
        id=mid, user_id="u-1", title=f"t{mid}", company="c", location="l",
        job_url=f"u{mid}", date_posted=None, score=score,
        created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
    )


def test_returns_matches_belonging_only_to_that_user():
    repo = InMemoryJobMatchRepository()
    repo.save(_mk(1, 80))
    repo.save(MatchedJob(
        id=2, user_id="u-2", title="other", company="c", location="l",
        job_url="u2", date_posted=None, score=70,
        created_at=datetime(2026, 6, 28, tzinfo=timezone.utc),
    ))
    use_case = ListUserMatches(repo)

    result = use_case.execute("u-1")

    assert len(result) == 1
    assert result[0].user_id == "u-1"


def test_matches_are_returned_best_fit_first():
    repo = InMemoryJobMatchRepository()
    repo.save(_mk(1, 82))   # lowest score
    repo.save(_mk(2, 96))   # best
    repo.save(_mk(3, 88))
    use_case = ListUserMatches(repo)

    result = use_case.execute("u-1")

    assert [m.score for m in result] == [96, 88, 82]


def test_unscored_matches_sort_after_scored_ones():
    repo = InMemoryJobMatchRepository()
    repo.save(_mk(1, None))
    repo.save(_mk(2, 50))
    repo.save(_mk(3, None))
    use_case = ListUserMatches(repo)

    result = use_case.execute("u-1")

    assert result[0].score == 50
    assert all(m.score is None for m in result[1:])


def test_unknown_user_returns_empty_list():
    repo = InMemoryJobMatchRepository()
    repo.save(_mk(1, 80))
    use_case = ListUserMatches(repo)

    assert use_case.execute("nobody") == []


def test_repository_is_the_port_not_the_implementation() -> None:
    """If JobMatchRepository stops being an interface, this test yells."""
    # Abstract methods must not have a body the implementation inherits.
    for name in ("list_for_user", "save"):
        assert getattr(JobMatchRepository, name).__isabstractmethod__ is True