import datetime
import random
from typing import Optional

# Design tokens (aligned with app theme)
BRAND_PRIMARY = "#6366f1"  # brand-500
BRAND_PRIMARY_DARK = "#4f46e5"  # brand-600
DARK_TEXT = "#111827"
SUBTEXT = "#4b5563"
SOFT_BG = "#f5f4f8"  # site soft-ui background
CARD_BG = "#ffffff"
BORDER = "#e2e8f0"
DOT_COLOR = "#d4d4dd"

# Small 6x6 dot grid png (1px dot) base64 to mimic site subtle dot pattern (safe fallback: background-color only)
DOT_GRID_DATA_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFklEQVQoU2NkYGD4z0AEYBxVSFUBAQB1TgmdOQk2kQAAAABJRU5ErkJggg=="
)

# Friendly dynamic greetings (kept minimal emoji for deliverability)
greetings = [
    "Here are some curated roles we found for you today.",
    "Fresh matches just in – take a quick scan.",
    "A focused batch of potential fits for your criteria.",
    "Today’s refined set of opportunities for you.",
    "Your monitored roles update has arrived.",
]


def get_welcome_message(confirm_url):
    """Welcome email (stacked-panels variant).
    Design shifts:
    - Uses a single outer shell and internal stacked panels separated by subtle dividers (simulating site stacked-sections) for higher legibility.
    - Hero succinct; panels: Inputs, How It Works, Principles & Next Steps (merged), Control.
    - Minimal color and concise bullet lists.
    """
    return f"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="color-scheme" content="light dark" />
<meta name="supported-color-schemes" content="light dark" />
<title>Welcome – Your Job Finder</title>
<!--[if mso]><style type="text/css">body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}</style><![endif]-->
<style>
  :root {{ color-scheme:light dark; supported-color-schemes:light dark; }}
  body {{ margin:0; padding:0; background:{SOFT_BG}; -webkit-font-smoothing:antialiased; }}
  .outer {{ background:{SOFT_BG}; }}
  .shell {{ background:#ffffff; border-radius:28px; box-shadow:0 8px 30px -10px rgba(0,0,0,0.12),0 4px 10px -2px rgba(0,0,0,0.05); }}
  .hero {{ background:#ffffff; background-image:radial-gradient(circle at 22% 18%, {BRAND_PRIMARY}25, transparent 62%), radial-gradient(circle at 80% 70%, #38bdf81a, transparent 70%); }}
  .pill {{ display:inline-block; background:#111827; color:#ffffff !important; font-size:11px; letter-spacing:1px; text-transform:uppercase; font-weight:600; padding:6px 14px; border-radius:999px; text-decoration:none; }}
  h1 {{ margin:26px 0 12px 0; font-size:30px; line-height:1.08; font-weight:700; letter-spacing:-0.5px; color:#111827; }}
  h2 {{ margin:0 0 14px 0; font-size:16px; line-height:1.35; font-weight:600; color:#111827; }}
  p {{ margin:0; font-size:14px; line-height:1.55; color:#4b5563; }}
  .stack-row {{ background:#ffffff; }}
  .stack-alt {{ background:#f8f9fc; }}
  .divider {{ height:1px; background:linear-gradient(to right, transparent, {BORDER}, transparent); line-height:1px; font-size:0; }}
  .accent-line {{ height:3px; background:linear-gradient(90deg, {BRAND_PRIMARY} 0%, {BRAND_PRIMARY_DARK} 55%, transparent 100%); border-radius:2px; line-height:0; font-size:0; }}
  ul {{ padding:0; margin:0; list-style:none; }}
  li {{ font-size:13px; line-height:1.55; margin:0 0 8px 0; color:#4b5563; }}
  .small {{ font-size:12px; line-height:1.5; color:#6b7280; }}
  a {{ color:{BRAND_PRIMARY_DARK}; text-decoration:none; font-weight:600; }}
  .btn {{ display:inline-block; background:{BRAND_PRIMARY_DARK}; color:#ffffff !important; font-size:14px; font-weight:600; padding:12px 24px; border-radius:999px; text-decoration:none; margin-top: 20px; }}
  @media (prefers-color-scheme: dark) {{
    body, .outer {{ background:#0f1115 !important; }}
    .shell {{ background:#1c1f26 !important; box-shadow:0 0 0 1px #262b33 inset !important; }}
    .hero {{ background:#1c1f26 !important; background-image:radial-gradient(circle at 22% 18%, {BRAND_PRIMARY_DARK}40, transparent 62%), radial-gradient(circle at 80% 70%, #38bdf845, transparent 70%) !important; }}
    h1,h2 {{ color:#f1f5f9 !important; }}
    p, li, .small {{ color:#cbd5e1 !important; }}
    .stack-alt {{ background:#242a33 !important; }}
    .divider {{ background:linear-gradient(to right, transparent, #334155, transparent) !important; }}
    .accent-line {{ background:linear-gradient(90deg, {BRAND_PRIMARY_DARK} 0%, {BRAND_PRIMARY} 60%, transparent 100%) !important; }}
    .pill {{ background:{BRAND_PRIMARY_DARK} !important; }}
    .btn {{ background:{BRAND_PRIMARY} !important; }}
  }}
</style>
</head>
<body>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="outer">
    <tr>
      <td align="center" style="padding:40px 14px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:660px;" class="shell">
          <!-- Hero -->
          <tr>
            <td class="hero" style="padding:56px 52px 42px 52px; border-radius:28px 28px 0 0;">
              <span class="pill">Welcome</span>
              <h1 style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Monitoring started</h1>
              <p style="max-width:540px; font-size:15px;">We now track sources for the role, type and location you specified. You’ll receive at most one concise email on days a real match appears—silence means nothing low‑quality filled your inbox.</p>
              <a href="{confirm_url}" class="btn">Confirm Email</a>
              <div class="accent-line" style="margin:32px 0 0 0;"></div>
            </td>
          </tr>
          <!-- Panel: Inputs -->
          <tr><td class="stack-row" style="padding:34px 52px 10px 52px;">
            <h2 style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">What powers matching</h2>
            <ul style="margin:0;">
              <li>Role focus & related titles</li>
              <li>Job type preference</li>
              <li>Location preference</li>
              <li>Posting recency & basic source quality filters</li>
            </ul>
            <p class="small" style="margin:10px 0 0 0;">Duplicates, expired and obvious low‑quality listings never reach you.</p>
          </td></tr>
          <tr><td style="padding:0 52px;"><div class="divider"></div></td></tr>
          <!-- Panel: How it works -->
          <tr><td class="stack-alt" style="padding:34px 52px 10px 52px;">
            <h2 style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">How it works</h2>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
              <tr>
                <td width="25%" style="padding:0 14px 26px 0; vertical-align:top;">
                  <p class="small" style="margin:0 0 4px 0; font-size:11px; letter-spacing:0.5px; font-weight:600; text-transform:uppercase; color:#111827;">1 • Define</p>
                  <p style="font-size:12px; line-height:1.55; margin:0;">You set the intent.</p>
                </td>
                <td width="25%" style="padding:0 14px 26px 0; vertical-align:top;">
                  <p class="small" style="margin:0 0 4px 0; font-size:11px; letter-spacing:0.5px; font-weight:600; text-transform:uppercase; color:#111827;">2 • Monitor</p>
                  <p style="font-size:12px; line-height:1.55; margin:0;">Sources continuously scanned.</p>
                </td>
                <td width="25%" style="padding:0 14px 26px 0; vertical-align:top;">
                  <p class="small" style="margin:0 0 4px 0; font-size:11px; letter-spacing:0.5px; font-weight:600; text-transform:uppercase; color:#111827;">3 • Filter</p>
                  <p style="font-size:12px; line-height:1.55; margin:0;">Noise & weak matches dropped.</p>
                </td>
                <td width="25%" style="padding:0 0 26px 0; vertical-align:top;">
                  <p class="small" style="margin:0 0 4px 0; font-size:11px; letter-spacing:0.5px; font-weight:600; text-transform:uppercase; color:#111827;">4 • Deliver</p>
                  <p style="font-size:12px; line-height:1.55; margin:0;">Only when a strong fit appears.</p>
                </td>
              </tr>
            </table>
          </td></tr>
          <tr><td style="padding:0 52px;"><div class="divider"></div></td></tr>
          <!-- Panel: Principles & Next -->
          <tr><td class="stack-row" style="padding:34px 52px 8px 52px;">
            <h2 style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Principles & what’s next</h2>
            <ul style="margin:0;">
              <li><strong style="color:#111827; font-weight:600;">Signal first:</strong> We prefer silence over irrelevant noise.</li>
              <li><strong style="color:#111827; font-weight:600;">Semantics:</strong> Contextual role understanding, not blind keyword tallying.</li>
              <li><strong style="color:#111827; font-weight:600;">Privacy:</strong> Data only used to match roles—never sold.</li>
              <li><strong style="color:#111827; font-weight:600;">Clean delivery:</strong> No ads. If nothing fits you get no email.</li>
            </ul>
            <p class="small" style="margin:14px 0 0 0;">If a strong match appears within ~24h you’ll receive your first batch. Quiet means nothing qualified yet.</p>
          </td></tr>
          <tr><td style="padding:0 52px;"><div class="divider"></div></td></tr>
          <!-- Panel: Control -->
          <tr><td class="stack-alt" style="padding:34px 52px 14px 52px; border-radius:0 0 28px 28px;">
            <h2 style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Your control</h2>
            <ul style="margin:0;">
              <li>Create another alert later if you need broader or narrower coverage.</li>
              <li>One‑click unsubscribe link is in every email.</li>
              <li>Use the site contact form for support (replies aren’t monitored).</li>
            </ul>
            <p class="small" style="margin:14px 0 0 0;">Tip: Keep role wording specific for higher precision.</p>
          </td></tr>
          <!-- Footer -->
          <tr>
            <td style="padding:42px 36px 48px 36px; text-align:center;">
              <p style="margin:0 0 8px 0; font-size:12px; line-height:1.5; color:#6b7280; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">© 2025 Your Job Finder • Educational project</p>
              <p style="margin:0; font-size:11px; line-height:1.5; color:#94a3b8; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">You’re receiving this because you created an alert. Adjust or unsubscribe any time.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def create_job_card(row):
    """Creates an individual job card (table block) aligned with theme.

    Expected row: JobPostingModel (the unified domain model).
    """
    title = row.title or ""
    company = row.company or ""
    location = row.location or ""
    date_posted = row.date_posted
    job_url = str(row.link)

    if isinstance(date_posted, datetime.date):
        posted_date = date_posted.strftime("%b %d, %Y")
    else:
        posted_date = "This Week"

    return f'''
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 18px 0; border-collapse:separate;">
      <tr>
        <td style="background:#ffffff;border:1px solid {BORDER};border-radius:18px;padding:20px 22px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;vertical-align:top;">
                <h3 style="margin:0 0 6px 0;font-size:17px;line-height:1.35;color:{DARK_TEXT};font-weight:600;">{title}</h3>
                <p style="margin:0 0 6px 0;font-size:14px;line-height:1.4;color:{SUBTEXT};font-weight:500;">{company}</p>
                <p style="margin:0 0 12px 0;font-size:13px;line-height:1.55;color:#6b7280;">📍 {location}<br />🕒 Posted: {posted_date}</p>
                <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td bgcolor="{BRAND_PRIMARY_DARK}" style="border-radius:999px;">
                      <a href="{job_url}" style="display:inline-block;padding:11px 20px;font-size:14px;font-weight:600;color:#ffffff;text-decoration:none;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">View Details ↗</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    '''


def get_html_template(html_content, email, position, location):
    """Nightly / daily batch email containing job cards.

    Args:
        html_content: Concatenated job card HTML blocks.
        email: Recipient email.
        position: Target position string.
        location: Target location string.
    """
    unsubscribe_url = "https://yourjobfinder.website/unsubscribe/process"
    return f'''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta name="color-scheme" content="light dark" />
  <meta name="supported-color-schemes" content="light dark" />
  <title>Your Job Matches</title>
  <!--[if mso]><style type="text/css">body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}</style><![endif]-->
  <style>
    :root {{ color-scheme: light dark; supported-color-schemes: light dark; }}
    body {{ margin:0; padding:0; background:{SOFT_BG}; -webkit-font-smoothing:antialiased; }}
    .outer {{ background:{SOFT_BG}; }}
    .card {{ background:{CARD_BG}; border-radius:28px; box-shadow:0 8px 28px -8px rgba(0,0,0,0.08); }}
    .header {{ background:{CARD_BG}; background-image:radial-gradient(circle at 25% 22%, {BRAND_PRIMARY}22, transparent 65%), radial-gradient(circle at 80% 70%, #38bdf81e, transparent 70%); }}
    .badge {{ display:inline-block; background:{DARK_TEXT}; color:#fff !important; font-size:11px; letter-spacing:1px; text-transform:uppercase; font-weight:600; padding:6px 14px; border-radius:999px; }}
    .tips {{ background:#ffffff; border:1px solid {BORDER}; border-radius:18px; }}
    a {{ color:{BRAND_PRIMARY_DARK}; }}
    @media (prefers-color-scheme: dark) {{
      body, .outer {{ background:#0f1115 !important; }}
      .card {{ background:#1c1f26 !important; box-shadow:0 0 0 1px #252a33 inset !important; }}
      .header {{ background:#1c1f26 !important; background-image:radial-gradient(circle at 25% 22%, {BRAND_PRIMARY_DARK}40, transparent 65%), radial-gradient(circle at 80% 70%, #38bdf845, transparent 70%) !important; }}
      h1,h2,h3 {{ color:#f1f5f9 !important; }}
      p, .muted {{ color:#cbd5e1 !important; }}
      .tips {{ background:#242a33 !important; border-color:#334155 !important; }}
      a {{ color:{BRAND_PRIMARY} !important; }}
    }}
  </style>
</head>
<body>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="outer">
    <tr>
      <td align="center" style="padding:34px 14px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;" class="card">
          <!-- Header -->
          <tr>
            <td class="header" style="padding:46px 46px 42px 46px; border-radius:28px 28px 0 0;">
              <span class="badge">Daily Batch</span>
              <h1 style="margin:26px 0 12px 0; font-size:28px; line-height:1.2; font-weight:700; letter-spacing:-0.5px; color:#111827; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Curated Matches</h1>
              <p style="margin:0; font-size:15px; line-height:1.55; max-width:420px; font-weight:500; color:{SUBTEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Focused roles for <span style="color:{DARK_TEXT};">{position or 'your role'}</span>{(' · ' + location) if location else ''}</p>
            </td>
          </tr>
          <!-- Intro -->
          <tr>
            <td style="padding:32px 46px 12px 46px;">
              <p style="margin:0 0 24px 0; font-size:15px; line-height:1.55; color:{SUBTEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">{random.choice(greetings)}</p>
            </td>
          </tr>
          <!-- Job Cards -->
          <tr>
            <td style="padding:0 46px 4px 46px;">{html_content}</td>
          </tr>
          <!-- Tips -->
            <tr>
              <td style="padding:10px 46px 40px 46px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="tips">
                  <tr>
                    <td style="padding:18px 22px;">
                      <p style="margin:0 0 6px 0; font-size:13px; line-height:1.5; font-weight:600; color:{DARK_TEXT}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Why you got these</p>
                      <p style="margin:0; font-size:12px; line-height:1.55; color:#6b7280; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Matched on role semantics, location, recency & source quality. Tune further by creating an additional alert with narrower scope.</p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          <!-- Footer inside card -->
          <tr>
            <td style="padding:34px 32px 46px 32px; border-top:1px solid {BORDER};">
              <p style="margin:0 0 14px 0; font-size:13px; line-height:1.55; color:#6b7280; text-align:center; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Prefer fewer emails? Create a second alert tuned differently and compare signal.</p>
              <p style="margin:0 0 16px 0; font-size:12px; line-height:1.5; color:#94a3b8; text-align:center; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">Sent to {email}. If this is incorrect, adjust by making a new alert.</p>
              <p style="margin:0; font-size:12px; line-height:1.5; color:#94a3b8; text-align:center; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
                <a href="{unsubscribe_url}?email={email}&position={position}&location={location}" style="color:{BRAND_PRIMARY_DARK}; text-decoration:none; font-weight:600;">Unsubscribe</a>
                <span style="color:#cbd5e1;"> • </span>
                <a href="https://yourjobfinder.website/terms" style="color:{BRAND_PRIMARY_DARK}; text-decoration:none; font-weight:600;">Terms</a>
                <span style="color:#cbd5e1;"> • </span>
                <a href="https://yourjobfinder.website/contact" style="color:{BRAND_PRIMARY_DARK}; text-decoration:none; font-weight:600;">Contact</a>
              </p>
            </td>
          </tr>
        </table>
        <!-- Legal line -->
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;">
          <tr>
            <td align="center" style="padding:20px 8px 12px 8px;">
              <p style="margin:0; font-size:11px; line-height:1.5; color:#94a3b8; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">© 2025 Your Job Finder. Educational project - do not reply.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
    '''


def _action_email(pill: str, title: str, body: str, cta_url: Optional[str], cta_label: str) -> str:
    """Single-panel transactional email in the welcome template's design language."""
    cta = (f'<a href="{cta_url}" class="btn">{cta_label}</a>' if cta_url else "")
    return f"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="color-scheme" content="light dark" />
<title>{title} – Your Job Finder</title>
<style>
  body {{ margin:0; padding:0; background:{SOFT_BG}; }}
  .outer {{ background:{SOFT_BG}; }}
  .shell {{ background:#ffffff; border-radius:28px; box-shadow:0 8px 30px -10px rgba(0,0,0,0.12); }}
  .hero {{ background:#ffffff; background-image:radial-gradient(circle at 22% 18%, {BRAND_PRIMARY}25, transparent 62%), radial-gradient(circle at 80% 70%, #38bdf81a, transparent 70%); }}
  .pill {{ display:inline-block; background:#111827; color:#ffffff !important; font-size:11px; letter-spacing:1px; text-transform:uppercase; font-weight:600; padding:6px 14px; border-radius:999px; text-decoration:none; }}
  h1 {{ margin:26px 0 12px 0; font-size:28px; line-height:1.08; font-weight:700; letter-spacing:-0.5px; color:#111827; }}
  p {{ margin:0; font-size:14px; line-height:1.55; color:{SUBTEXT}; }}
  .small {{ font-size:12px; line-height:1.5; color:#6b7280; }}
  .btn {{ display:inline-block; background:{BRAND_PRIMARY_DARK}; color:#ffffff !important; font-size:14px; font-weight:600; padding:12px 24px; border-radius:999px; text-decoration:none; margin-top: 20px; }}
  .accent-line {{ height:3px; background:linear-gradient(90deg, {BRAND_PRIMARY} 0%, {BRAND_PRIMARY_DARK} 55%, transparent 100%); border-radius:2px; line-height:0; font-size:0; margin-top:32px; }}
  @media (prefers-color-scheme: dark) {{
    body, .outer {{ background:#0f1115 !important; }}
    .shell {{ background:#1c1f26 !important; box-shadow:0 0 0 1px #262b33 inset !important; }}
    .hero {{ background:#1c1f26 !important; background-image:radial-gradient(circle at 22% 18%, {BRAND_PRIMARY_DARK}40, transparent 62%), radial-gradient(circle at 80% 70%, #38bdf845, transparent 70%) !important; }}
    h1 {{ color:#f1f5f9 !important; }}
    p, .small {{ color:#cbd5e1 !important; }}
    .pill {{ background:{BRAND_PRIMARY_DARK} !important; }}
    .btn {{ background:{BRAND_PRIMARY} !important; }}
  }}
</style>
</head>
<body>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="outer">
    <tr>
      <td align="center" style="padding:40px 14px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:660px;" class="shell">
          <tr>
            <td class="hero" style="padding:52px 52px 42px 52px; border-radius:28px 28px 0 0;">
              <span class="pill">{pill}</span>
              <h1 style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">{title}</h1>
              {body}
              {cta}
              <div class="accent-line"></div>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 52px; border-radius:0 0 28px 28px;">
              <p class="small" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
                Didn't request this? You can safely ignore the email.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_login_message(login_url):
    """Magic-link sign-in email: one-time, 30-minute link to the dashboard."""
    return _action_email(
        "Sign in",
        "Your sign-in link",
        """
              <p style="max-width:540px; font-size:15px;">Click below to open your matches dashboard —
              the link works once and expires in 30 minutes.</p>""",
        login_url,
        "Open my dashboard",
    )


def get_signup_nudge_message():
    """Sent to login attempts from unknown emails: no account leak, just a nudge."""
    return _action_email(
        "Hello",
        "We don't have this email yet",
        """
              <p style="max-width:540px; font-size:15px;">There is no job-alert subscription for this address.
              Set one up on the site — tell us your role, job type and location and we scan for matches daily.</p>""",
        "https://yourjobfinder.website",
        "Set up job alerts",
    )