import os


class JobMatcherCredential:
    @staticmethod
    def get_url():
        return os.environ.get("job_matcher_url")

    @staticmethod
    def get_token():
        return os.environ.get("job_matcher_token")

    @staticmethod
    def get_extractor_model():
        value = os.environ.get("extractor_model")
        return[item.strip() for item in value.split(",")]

    @staticmethod
    def get_judge_model():
        return os.environ.get("judge_model")


class GoogleScraperCredential:
    @staticmethod
    def get_google_scraper_url():
        return os.environ.get("google_scraper_url")
    @staticmethod
    def get_google_scraper_token():
        return os.environ.get("google_scraper_token")

class CloudflareCredential:
    @staticmethod
    def get_token():
        return os.environ.get("cloudflare_email_token")

    @staticmethod
    def get_account_id():
        return os.environ.get("cloudflare_account_id")

    @staticmethod
    def get_browser_token():
        return os.environ.get("cloudflare_browser_token")

    @staticmethod
    def get_welcome_from():
        return os.environ.get("cloudflare_email_welcome_from", "welcome@yourjobfinder.website")

    @staticmethod
    def get_notification_from():
        return os.environ.get("cloudflare_email_notification_from", "notification@yourjobfinder.website")




class DatabaseCredential:
    @staticmethod
    def get_db_name():
        return os.environ.get("db_name")

    @staticmethod
    def get_db_password():
        return os.environ.get("db_password")

    @staticmethod
    def get_db_username():
        return os.environ.get("db_username")

    @staticmethod
    def get_db_host():
        return os.environ.get("db_host")

    @staticmethod
    def get_db_port():
        return os.environ.get("db_port")

    @staticmethod
    def get_db_uri():
        # Direct connect to db_host:db_port. In prod that's the autossh sidecar
        # (db_host=ssh-tunnel), which forwards to the remote Postgres.
        return "postgresql://%s:%s@%s:%s/%s" % (
            DatabaseCredential.get_db_username(),
            DatabaseCredential.get_db_password(),
            DatabaseCredential.get_db_host(),
            DatabaseCredential.get_db_port(),
            DatabaseCredential.get_db_name(),
        )