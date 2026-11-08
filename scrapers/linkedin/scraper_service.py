from typing import List

import requests
from pydantic import ValidationError

from credential import CloudflareCredential
from domain.job_posting import JobPostingModel
from scrapers.linkedin.linkedin_html import build_search_url, parse_search_html
from logger_utils import create_logger

logger = create_logger("LinkedIn Scraper")


def scrape_linkedin(keyword: str, location: str, limit: int = 10) -> List[JobPostingModel]:
    url = build_search_url(keyword, location)
    logger.info(f"Linkedin scraping for {keyword} in {location}")
    try:
        html = _render_search_html(url)
        postings = parse_search_html(html)
        logger.info(f"Found {len(postings)} postings")
        return [posting.to_job_posting() for posting in postings[:limit]]
    except requests.exceptions.HTTPError as e:
        logger.error(f"LinkedIn scraping HTTP error for '{keyword}': {e}")
        return []
    except (ValidationError, Exception) as e:
        logger.error(f"Failed to scrape LinkedIn response: {e}")
        return []


def _render_search_html(url: str) -> str:
    account_id = CloudflareCredential.get_account_id()
    token = CloudflareCredential.get_browser_token()
    if not account_id:
        raise Exception("cloudflare_account_id is not set")
    if not token:
        raise Exception("cloudflare_browser_token is not set")
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/content"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "rejectResourceTypes": ["image", "script"],
    }

    logger.info("Sending POST request to browser rendering endpoint")
    response = requests.post(endpoint, json=payload, headers=headers, timeout=120)
    response.raise_for_status()

    data = response.json()
    html = data.get("result") or ""
    if not html:
        logger.warning(
            f"Browser rendering returned no HTML (errors: {data.get('errors')})"
        )
    return html
