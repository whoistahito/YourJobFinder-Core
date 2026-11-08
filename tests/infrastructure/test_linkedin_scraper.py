# No network: requests.post is monkeypatched, parsing runs against a small sample of the
# LinkedIn guest search fragment. Run: pytest tests/infrastructure/test_linkedin_scraper.py
import requests

from domain.job_posting import JobPostingModel
from scrapers.linkedin.linkedin_html import build_search_url, parse_search_html
from scrapers.linkedin.models import LinkedInJobPosting
from scrapers.linkedin.scraper_service import scrape_linkedin

# Two valid cards (h3 + span title variants, link with tracking params) and one
# card missing the company, which must be skipped.
SAMPLE_HTML = """
<div class="base-card relative job-search-card"
     data-entity-urn="urn:li:jobPosting:4010">
  <a class="base-card__full-link"
     href="https://de.linkedin.com/jobs/view/python-developer-at-acme-4010?refId=abc&amp;originalSubdomain=de">
    <span class="sr-only">Python Developer</span>
  </a>
  <div class="base-search-card__info">
    <h3 class="base-search-card__title"> Python Developer </h3>
    <h4 class="base-search-card__subtitle">
      <a class="hidden-nested-link">Acme GmbH</a>
    </h4>
    <span class="job-search-card__location">Hamburg, Germany</span>
    <time class="job-search-card__list-date" datetime="2026-06-05">2 days ago</time>
  </div>
</div>
<div class="base-card relative job-search-card"
     data-entity-urn="urn:li:jobPosting:4011">
  <a class="base-card__full-link"
     href="https://de.linkedin.com/jobs/view/data-engineer-at-brv-4011?refId=abc">
    <span class="sr-only">Data Engineer</span>
  </a>
  <div class="base-search-card__info">
    <span class="base-search-card__title">Data Engineer</span>
    <h4 class="base-search-card__subtitle"><a>BRV GmbH</a></h4>
    <span class="job-search-card__location">Berlin, Germany</span>
    <time datetime="2026-06-01">6 days ago</time>
  </div>
</div>
<div class="base-card relative job-search-card"
     data-entity-urn="urn:li:jobPosting:4012">
  <a class="base-card__full-link" href="https://de.linkedin.com/jobs/view/no-company-4012"></a>
  <div class="base-search-card__info">
    <span class="base-search-card__title">Mystery Role</span>
  </div>
</div>
"""


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_build_search_url_encodes_keyword_and_location():
    url = build_search_url("Java Developer", "Hamburg")
    assert url == (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        "?keywords=Java%20Developer&location=Hamburg&start=0"
    )


def test_build_search_url_without_keyword_omits_param():
    url = build_search_url("", "Hamburg")
    assert "keywords" not in url
    assert url.startswith("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search")
    assert "location=Hamburg" in url
    assert "start=0" in url


def test_parse_search_html_extracts_postings():
    postings = parse_search_html(SAMPLE_HTML)
    assert len(postings) == 2

    first, second = postings
    assert first.title == "Python Developer"
    assert first.company == "Acme GmbH"
    assert first.location == "Hamburg, Germany"
    # Tracking params are stripped so the link stays stable for dedupe.
    assert str(first.link) == "https://de.linkedin.com/jobs/view/python-developer-at-acme-4010"
    assert first.date_posted == "2026-06-05"

    assert second.title == "Data Engineer"
    assert second.company == "BRV GmbH"
    assert second.date_posted == "2026-06-01"


def test_parse_search_html_skips_incomplete_card():
    postings = parse_search_html(SAMPLE_HTML)
    assert "4012" not in "".join(str(p.link) for p in postings)


def test_scrape_linkedin_posts_to_browser_rendering(monkeypatch):
    monkeypatch.setenv("cloudflare_account_id", "acct123")
    monkeypatch.setenv("cloudflare_browser_token", "tok")
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return _FakeResponse({"result": SAMPLE_HTML, "success": True})

    monkeypatch.setattr("scrapers.linkedin.scraper_service.requests.post", fake_post)

    postings = scrape_linkedin("python developer", "Hamburg", limit=10)

    assert captured["url"] == "https://api.cloudflare.com/client/v4/accounts/acct123/browser-rendering/content"
    assert captured["headers"] == {
        "Authorization": "Bearer tok",
        "Content-Type": "application/json",
    }
    assert captured["json"]["url"].startswith(
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    )
    assert captured["json"]["rejectResourceTypes"] == ["image", "script"]
    # The service hands unified JobPostingModels back, not LinkedInJobPostings.
    assert len(postings) == 2
    assert all(isinstance(p, JobPostingModel) for p in postings)
    assert postings[0].title == "Python Developer"
    assert postings[0].description is None


def test_to_job_posting_maps_to_core_model():
    posting = parse_search_html(SAMPLE_HTML)[0]

    core = posting.to_job_posting()

    assert isinstance(core, JobPostingModel)
    assert core.title == "Python Developer"
    assert core.company == "Acme GmbH"
    assert core.location == "Hamburg, Germany"
    assert core.link == "https://de.linkedin.com/jobs/view/python-developer-at-acme-4010"
    assert core.date_posted == "2026-06-05"


def test_scrape_linkedin_respects_limit(monkeypatch):
    monkeypatch.setenv("cloudflare_account_id", "acct123")
    monkeypatch.setenv("cloudflare_browser_token", "tok")
    monkeypatch.setattr(
        "scrapers.linkedin.scraper_service.requests.post",
        lambda url, json=None, headers=None, timeout=None: _FakeResponse({"result": SAMPLE_HTML}),
    )
    postings = scrape_linkedin("python", "Hamburg", limit=1)
    assert [p.title for p in postings] == ["Python Developer"]


def test_scrape_linkedin_http_error_returns_empty_list(monkeypatch):
    monkeypatch.setenv("cloudflare_account_id", "acct123")
    monkeypatch.setenv("cloudflare_browser_token", "tok")

    def failing_post(url, json=None, headers=None, timeout=None):
        raise requests.exceptions.HTTPError("503 Server Error")

    monkeypatch.setattr("scrapers.linkedin.scraper_service.requests.post", failing_post)
    assert scrape_linkedin("python", "Hamburg") == []
