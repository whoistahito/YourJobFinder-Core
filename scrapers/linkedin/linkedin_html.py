from typing import List
from urllib.parse import urlencode, quote

from bs4 import BeautifulSoup
from pydantic import ValidationError

from scrapers.linkedin.models import LinkedInJobPosting
from logger_utils import create_logger

logger = create_logger("LinkedIn Scraper")

# Guest (logged-out) search fragment: one call returns ~25 job-card <li> elements.
LINKEDIN_GUEST_SEARCH_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
)


def build_search_url(keyword: str, location: str, start: int = 0) -> str:
    params = {}
    if keyword and keyword.strip():
        params["keywords"] = keyword.strip()
    if location and location.strip():
        params["location"] = location.strip()
    params["start"] = start
    return f"{LINKEDIN_GUEST_SEARCH_URL}?{urlencode(params, quote_via=quote)}"


def parse_search_html(html: str) -> List[LinkedInJobPosting]:
    soup = BeautifulSoup(html or "", "html.parser")
    postings: List[LinkedInJobPosting] = []

    for card in soup.select("div.base-card"):
        posting = _parse_card(card)
        if posting is None:
            continue
        postings.append(posting)

    return postings


def _parse_card(card) -> "LinkedInJobPosting | None":
    anchor = card.select_one("a.base-card__full-link")
    title_el = (
        card.select_one("span.base-search-card__title")
        or card.select_one("h3.base-search-card__title")
    )
    company_el = card.select_one("h4.base-search-card__subtitle")
    location_el = card.select_one("span.job-search-card__location")
    time_el = card.select_one("time")

    if not (anchor and title_el and company_el):
        logger.warning("Skipping LinkedIn card with missing title/company/link")
        return None

    # Strip tracking params (refId, ...) so the link stays stable for the SentEmail dedupe key.
    raw_link = (anchor.get("href") or "").split("?", 1)[0]
    date_posted = (time_el.get("datetime") or time_el.get_text(strip=True)) if time_el else None

    data = {
        "title": title_el.get_text(strip=True),
        "company": company_el.get_text(strip=True),
        "location": location_el.get_text(strip=True) if location_el else None,
        "link": raw_link,
        "date_posted": date_posted,
    }
    try:
        return LinkedInJobPosting.model_validate(data)
    except ValidationError as e:
        logger.warning(f"Skipping LinkedIn job due to validation error: {e}")
        return None
