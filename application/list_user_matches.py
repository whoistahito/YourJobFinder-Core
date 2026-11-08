"""ListUserMatches — the application use case behind GET /users/<id>/matches.

Depends only on the JobMatchRepository interface. Returned matches are sorted
best-fit-first. Unscored matches (None) sort after every scored one.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from domain.job_match_repository import JobMatchRepository
from domain.matched_job import MatchedJob


def _sort_key(job: MatchedJob):
    # None sorts last; scored ones sort higher-first.
    score = job.score
    if score is None:
        return (1, 0)
    return (0, -score)


class ListUserMatches:
    def __init__(self, repo: JobMatchRepository):
        self._repo = repo

    def execute(self, user_id: str, since: Optional[datetime] = None) -> list[MatchedJob]:
        if not user_id:
            return []
        return sorted(self._repo.list_for_user(user_id, since), key=_sort_key)