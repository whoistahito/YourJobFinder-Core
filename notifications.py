"""Notification pipeline — scrape, match, email, record.

No `app` import and no `app_context()` wrapping in here: callers provide the
context (a Flask request for the per-signup welcome email; main.py's one-shot
for the daily batch). That keeps this importable from app_factory without a
circular import.
"""
from datetime import datetime, timezone
from typing import Optional

from db.database_service import UserManager, UserEmailManager
from email_manager import send_email
from credential import CloudflareCredential
from html_render import create_job_card, get_html_template, get_welcome_message
from logger_utils import create_logger
from scrapers.google_scraper_service import scrape_google
from scrapers.linkedin.scraper_service import scrape_linkedin
from job_matching.job_matching_service import match
from job_matching.job_matching_models import UserProfile
from domain.matched_job import MatchedJob
from domain.job_posting import JobPostingModel
from infrastructure.job_match_repository import SqlAlchemyJobMatchRepository
from extension import db

logger = create_logger("notifications")

JOB_MATCH_THRESHOLD = 0.35


def send_welcome_email(user) -> None:
    """Confirmation/welcome email, sent in-request when a user signs up."""
    confirm_url = f"https://api.yourjobfinder.website/confirm/{user.confirmation_token}"
    send_email(
        get_welcome_message(confirm_url),
        "Welcome to Your Job Finder! Please Confirm Email",
        user.email,
        is_html=True,
        sender=CloudflareCredential.get_welcome_from(),
    )


def find_jobs(
        search_term: str,
        location: str,
        job_type: Optional[str],
        country_code: Optional[str] = None,
) -> list[JobPostingModel]:
    # Google first, then LinkedIn on top; both scrapers fail-open to [] (unified JobPostingModel).
    jobs = scrape_google(search_term, location, 10, country_code=country_code)
    jobs.extend(scrape_linkedin(search_term, location, 10))
    return _dedupe_by_link(jobs)


def _dedupe_by_link(jobs) -> list:
    # Per-run dedupe: the same job can surface on both Google and LinkedIn.
    # Cross-run dedupe stays DB-backed via the SentEmail key.
    seen = set()
    unique = []
    for job in jobs:
        link = str(job.link)
        if link in seen:
            continue
        seen.add(link)
        unique.append(job)
    return unique


def _safe_str(value: Optional[str]) -> str:
    return value or ""


def get_user_profile(user) -> Optional[UserProfile]:
    """Convert the SQLAlchemy User relations into a UserProfile Pydantic model."""
    if not (user.skills or user.experiences or user.educations):
        return None

    return UserProfile(
        skills=[s.skill for s in user.skills],
        experiences=[e.experience for e in user.experiences],
        qualifications=[e.education for e in user.educations],
    )


def notify_jobs(
        jobs: list[JobPostingModel],
        email: str,
        position: str,
        location: str,
):
    """
    Send notification email if there are filtered jobs based on refined criteria.
    """
    if not jobs:
        raise Exception("No jobs found based on the criteria.")

    sorted_jobs = sorted(
        jobs,
        key=lambda job: _safe_str(job.date_posted),
        reverse=True,
    )

    html_content = ''.join(create_job_card(job) for job in sorted_jobs)
    html_template = get_html_template(html_content, email, position, location)
    send_email(
        html_template,
        "Found some job opportunities for you!",
        email,
        is_html=True,
        sender=CloudflareCredential.get_notification_from(),
    )


def notify_all_confirmed_users() -> None:
    """One pass over every confirmed user. Caller supplies the app context."""
    for user in UserManager().get_confirmed_users():
        try:
            notify_user(user)
        except Exception as e:
            logger.exception(f"notify_user failed for {user.email}: {e}")


def notify_user(user):
    found_jobs = find_jobs(user.position, user.location, user.job_type, country_code=getattr(user, 'country_code', None))
    if not found_jobs:
        logger.error("No jobs found based on the criteria.")
        return

    user_profile = get_user_profile(user)
    job_match_repo = SqlAlchemyJobMatchRepository(db)

    matched = []  # (job, score_value) — persisted only after the email is sent
    for job in found_jobs:
        job_url = job.link
        if UserEmailManager().is_sent(user.email, job_url, user.position, user.location):
            continue

        # job matching if user has profile and job has description
        score_value = None
        if user_profile and job.description:
            try:
                logger.info(f"Matching: {job.title}")
                score = match(job.description, user_profile)
                if score < JOB_MATCH_THRESHOLD:
                    logger.info(
                        f"Skipping '{job.title}' for {user.email} "
                        f"— match score {score:.2f} < threshold {JOB_MATCH_THRESHOLD}"
                    )
                    continue
                logger.info(
                    f"'{job.title}' passed match filter for {user.email} "
                    f"— score {score:.2f}"
                )
                score_value = int(round(score * 100))
            except Exception as e:
                logger.exception(
                    f"Job matching failed for '{job.title}': {e} — including job anyway"
                )

        matched.append((job, score_value))

    if not matched:
        return

    # Send first; only record (sent-email + dashboard match) once the send succeeds,
    # so a failed send doesn't leave dashboard rows for an email the user never got.
    # ponytail: the two writes below commit per-job, not in one txn — a crash between
    # them can drop a dashboard row (job still marked sent). Wrap in a single txn if
    # that matters; the costly duplicate-on-send-failure case is already gone.
    notify_jobs([job for job, _ in matched], user.email, user.position, user.location)
    for job, score_value in matched:
        UserEmailManager().add_sent_email(
            user.email, job.link, user.position, user.location
        )
        job_match_repo.save(MatchedJob(
            id=None, user_id=user.id, title=job.title, company=job.company,
            location=job.location, job_url=job.link, date_posted=job.date_posted,
            score=score_value, created_at=datetime.now(timezone.utc),
        ))
