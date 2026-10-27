import time
import requests
from pydantic import ValidationError

from credential import GoogleScraperCredential
from scrapers.google_scraper_models import GoogleScrapeResponse
from logger_utils import create_logger

logger = create_logger("Google Scraper")

MIN_CALL_INTERVAL_SECONDS = 60
_last_call_at: float | None = None


def _throttle() -> None:
    """Wait until MIN_CALL_INTERVAL_SECONDS passed since the previous scraper call."""
    global _last_call_at
    if _last_call_at is not None:
        wait = MIN_CALL_INTERVAL_SECONDS - (time.monotonic() - _last_call_at)
        if wait > 0:
            logger.info(f"Throttling Google scraper: sleeping {wait:.0f}s between calls")
            time.sleep(wait)
    _last_call_at = time.monotonic()


def scrape_google(title: str, location: str, limit: int = 10, country_code: str = None) -> GoogleScrapeResponse:
    token = GoogleScraperCredential.get_google_scraper_token()
    url = GoogleScraperCredential.get_google_scraper_url()
    query = f"{title} jobs in {location}"
    payload = {
        "query": query,
        "limit": limit,
    }
    if country_code:
        payload["country"] = country_code
    headers = {
        "Authorization": f"Bearer {token}",
    }
    logger.info(f"Scraping for {title}")
    _throttle()
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Found {len(data['jobs'])} jobs")
        return GoogleScrapeResponse.from_json(data)
    except requests.exceptions.HTTPError as e:
        logger.error(f"Scraper HTTP error for '{title}': {e}")
        return GoogleScrapeResponse()
    except (ValidationError, Exception) as e:
        logger.error(f"Failed to parse scraper response: {e}")
        return GoogleScrapeResponse()
