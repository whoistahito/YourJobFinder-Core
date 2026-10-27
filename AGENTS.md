# AGENTS.md

## Big picture (what runs)
- Two entrypoints:
  - **API**: `app.py` (Flask) exposes `/user` create/delete, `/confirm/<token>` redirect, and `/users/<id>/matches`. Sends the confirmation email in-request on signup.
  - **Scheduled job**: `main.py` is a **one-shot** — a single scrape+match+email pass over confirmed users, then exits. A platform scheduler (Coolify Scheduled Task → `python main.py`, daily) drives the cadence; it is no longer a resident loop. The pipeline lives in `notifications.py`.
- DB is **Flask-SQLAlchemy** (`extension.py`) with migrations via **Flask-Migrate/Alembic** (`migrations/`).

## Repo map (start here)
- `app.py`: Flask app + routes; initializes `db` + `migrate`; creates `UserManager()`.
- `main.py`: one-shot scheduled-job entrypoint — wraps `notifications.notify_all_confirmed_users()` in `app.app_context()` and exits.
- `notifications.py`: the notification pipeline (`send_welcome_email`, `notify_user`, `notify_all_confirmed_users`). No `app` import / no `app_context()` wrapping — callers supply the context (the Flask request for the signup welcome email; `main.py` for the daily batch).
- `db/models.py`: `User` (+ `Skill`/`Experience`/`Education`) and `SentEmail` (composite PK).
- `db/database_service.py`: thin managers (`UserManager`, `UserEmailManager`) around SQLAlchemy queries/commits.
- `scrapers/google_scraper_service.py`: posts to an external Google scraping API using bearer token.
- `scrapers/google_scraper_models.py`: Pydantic models `GoogleJobPosting` and `GoogleScrapeResponse`.
- `job_matching/job_matching_service.py`: calls the external job-matching API; exposes `match(job_description, user_profile) -> float`.
- `job_matching/job_matching_models.py`: Pydantic models `UserProfile`, `Requirements`, `SimilarityScore`, `JobMatchingResponse`.
- `email_manager.py`: `send_email(body, subject, to, is_html=True, sender=None)` via Cloudflare Email Service. `sender` is the from-address (welcome@ for signup, notification@ for job updates); defaults to the welcome sender.
- `html_render.py`: HTML-heavy templates (welcome email + daily "job cards").

## File notes
### `main.py` / `notifications.py`
- `main.py` is the **one-shot** scheduled-job entrypoint: `with app.app_context(): notify_all_confirmed_users()`, then exits. Run it on a schedule (Coolify Scheduled Task), not as a resident process.
- Confirmation emails are **event-driven**: `send_welcome_email(user)` is called from the `POST /user` handler (`app_factory.py`) right after the user row commits. No polling, no `is_new` sweep.
- `JOB_MATCH_THRESHOLD = 0.35` (in `notifications.py`) — jobs scoring below this are silently skipped. Set to `0.0` to disable filtering.
- Helper `_has_profile(user) -> bool`: returns `True` if the user has at least one skill, experience, or education row.
- Helper `_build_user_profile(user) -> UserProfile`: converts the SQLAlchemy `User` relations into a `UserProfile` Pydantic model (skills → `skills`, experiences → `experiences`, educations → `qualifications`).
- Notification pipeline (`notify_user()`):
  1. Scrape jobs via `scrape_google(position, location, 10)`.
  2. Build `UserProfile` once (only if `_has_profile(user)` is true).
  3. For each job: skip if already sent; if user has a profile **and** the job has a `description`, call `match()` and skip if score < threshold; fail-open on matcher errors.
  4. Render job cards, email, record sent URLs.

### `scrapers/google_scraper_service.py`
- Thin client for the external Google scraping API.
- `scrape_google(title, location, limit=10)`:
  - Builds query string: `"{title} jobs in {location}"`.
  - **Throttles calls**: at least 60s elapse between any two requests (`_throttle()` in the service, process-wide, applies to every caller including the daily per-user loop); the interval also counts failed calls because a failed call still hits the scraper API.
  - `POST`s to `google_scraper_url` with JSON `{query, limit}` and `Authorization: Bearer <google_scraper_token>`.
  - Raises on non-2xx (`response.raise_for_status()`) and parses the JSON into `GoogleScrapeResponse`.
- Expectation: this module does **not** scrape directly; it delegates to a separate service behind `google_scraper_url`.

### `job_matching/job_matching_service.py`
- Thin client for the external job-matching/scoring API.
- `match(job_description: str, user_profile: UserProfile) -> float`:
  - `POST`s to `job_matcher_url` with `Authorization: Bearer <job_matcher_token>`.
  - Payload includes `modelId` (extractor model), an `extractionPipeline` dict (extractor + judge model IDs), `inputText` (job description), and `userProfile` (serialized via `.model_dump()`).
  - Parses response into `JobMatchingResponse` and returns `similarityScore.score` (0.0–1.0).
  - Raises on HTTP errors; callers should handle exceptions and fail-open.

## Key data flows (follow the call chain)
- **Create user**: `POST /user` → `UserManager.add_user(...)` (returns the new `User`, or `None` if a duplicate) → inserts `users` row with `is_confirmed=False`, `confirmation_token=<uuid>` and optional related rows. On success the handler calls `notifications.send_welcome_email(user)` in-request (failure is logged, signup still 201).
- **Confirm user**: `GET /confirm/<token>` → `UserManager.confirm_user(token)` sets `is_confirmed=True` and clears token, then `app.py` redirects to `https://yourjobfinder.website/...`.
- **Scheduled daily notify**: `python main.py` → `notify_all_confirmed_users()` → for each confirmed user → `notify_user(user)`:
  1. `scrape_google(position, location, 10)` → list of `GoogleJobPosting`.
  2. Build `UserProfile` from user's skills/experiences/educations (skipped if profile is empty).
  3. Per job: skip if `UserEmailManager.is_sent(...)` → optionally call `job_matching.match(description, profile)` → skip if score < `JOB_MATCH_THRESHOLD`.
  4. `create_job_card(job)` × N → `get_html_template(...)` → `send_email(...)`.
  5. `UserEmailManager.add_sent_email(...)` for each sent job.

## Configuration / env vars (see `credential.py`)
- DB: `db_host`, `db_port`, `db_name`, `db_username`, `db_password` (`credential.get_db_uri()` builds the URI). In prod `db_host=ssh-tunnel` — the app connects to the **autossh sidecar** (`docker-compose.yml`), which forwards to the remote Postgres. The app has no SSH code; the sidecar's tunnel is configured via `SSH_HOST`, `SSH_USER`, `SSH_PORT`, `SSH_DB_HOST`, `SSH_DB_PORT`. The private key is **not** an env var — it lives on the backend host at `/data/jobfinder/id_ed25519` (chmod 600) and is mounted read-only into the sidecar as `/keys` (a **directory** mount; override the host dir with `SSH_KEY_DIR`). Env-injected keys were abandoned: Coolify truncates long env values and flattens multi-line ones, and its single-*file* bind mounts are created as directories — only a directory mount is reliable. The matching public key is in the DB server's root `authorized_keys`.
- Email (Cloudflare Email Service): `cloudflare_email_token`, `cloudflare_account_id`, `cloudflare_email_welcome_from`, `cloudflare_email_notification_from`.
- Scraper API: `google_scraper_url`, `google_scraper_token`.
- Job Matcher API: `job_matcher_url`, `job_matcher_token`, `extractor_model`, `judge_model`.

## Project-specific conventions / gotchas
- The worker does DB work only inside `with app.app_context():` blocks (see `main.py`). If you add DB access elsewhere in the worker, keep this pattern.
- Duplicate prevention is **DB-backed** (`SentEmail` composite primary key: `email + job_url + position + location`). This is why `UserEmailManager.is_sent(...)` requires all 4 fields.
- Job cards expect a `GoogleJobPosting` object (see `html_render.create_job_card`); fields accessed: `title`, `company`, `location`, `date_posted`, `link`.
- `scrapers/` and `job_matching/` are proper Python packages (each has an `__init__.py`). Always import them with their full package path (e.g. `from scrapers.google_scraper_service import scrape_google`).
- Job matching is **opt-in per user**: users without any skills/experiences/educations skip the matcher entirely and receive all scraped jobs. Users with a profile but whose scraped jobs lack a `description` field also skip matching for those jobs.
- The matcher is **fail-open**: if the external matching API errors, the job is included anyway to avoid users missing opportunities. Log the error and move on.
- Deployment URLs are embedded in code/templates (`yourjobfinder.website`, `api.yourjobfinder.website`). If you change domains, search/replace across `app.py`, `main.py`, `html_render.py`.

## Developer workflows (verified from repo files)
- Dependencies are defined in `pyproject.toml` (requires Python `>=3.13`) and there is a `uv.lock` → prefer `uv`.
- Common commands:
  - `uv venv && uv sync`
  - Run API locally: `uv run python app.py` (Flask dev server on `:5000`)
  - Run the daily job once (unbuffered logs): `uv run python -u main.py`
  - Apply migrations: `uv run flask db upgrade`
- Deployment: Docker (`Dockerfile` + `docker-compose.yml`) on Coolify. The `web` service runs `gunicorn app:app -c gunicorn_config.py` (binds `0.0.0.0:8080`); a `migrate` service applies migrations on each deploy; the daily `python main.py` runs via a Coolify Scheduled Task. See `.env.example` for env vars.
