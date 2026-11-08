from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class JobPostingModel:
    # Unified posting shape the pipeline consumes; each scraper maps its own
    # source-specific model into this before results leave the scrapers package.
    title: str
    company: str
    link: str
    location: Optional[str] = None
    date_posted: Optional[str] = None
    employment_type: Optional[str] = None
    description: Optional[str] = None
