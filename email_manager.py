import html
import re

from cloudflare import Cloudflare

from logger_utils import create_logger
from credential import CloudflareCredential

logger = create_logger("email_manager")

_TAG_RE = re.compile(r"<[^>]+>")


def _html_to_text(body: str) -> str:
    """Crude plain-text alternative for the multipart email (deliverability)."""
    return html.unescape(_TAG_RE.sub("", body)).strip()


def send_email(body, subject, receiver_email, is_html=True, sender=None):
    """Send a transactional email via Cloudflare Email Service.

    `sender` is the from-address (e.g. welcome@ vs notification@); defaults to
    the welcome sender. Both current callers pass HTML; we derive a text part
    for deliverability.
    """
    if is_html:
        html_body, text_body = body, _html_to_text(body)
    else:
        html_body, text_body = None, body

    try:
        client = Cloudflare(api_token=CloudflareCredential.get_token())
        response = client.email_sending.send(
            account_id=CloudflareCredential.get_account_id(),
            from_=sender or CloudflareCredential.get_welcome_from(),
            to=receiver_email,
            subject=subject,
            html=html_body,
            text=text_body,
        )
        logger.info(f"Email sent to {receiver_email}: delivered={getattr(response, 'delivered', None)}")
    except Exception as e:
        logger.error(f"Error while sending email to {receiver_email}: {e}")
