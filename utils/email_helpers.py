import logging

import resend
from flask import current_app

logger = logging.getLogger(__name__)

# ── HTML email template ──────────────────────────────────────────────

_RESET_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body {{
      margin: 0; padding: 0;
      background-color: #0B1F17;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}
    .wrapper {{
      max-width: 480px; margin: 0 auto; padding: 40px 24px;
    }}
    .card {{
      background-color: #1F4D3A;
      border-radius: 12px;
      padding: 36px 28px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 22px; font-weight: 700;
      color: #F4F1E9;
      letter-spacing: 0.02em;
    }}
    p {{
      margin: 0 0 24px;
      font-size: 14px; line-height: 1.6;
      color: #C8C4B5;
    }}
    .btn {{
      display: inline-block;
      padding: 14px 32px;
      background-color: #FFB627;
      color: #0B1F17;
      text-decoration: none;
      font-size: 14px; font-weight: 700;
      border-radius: 8px;
      letter-spacing: 0.04em;
    }}
    .fallback {{
      margin-top: 20px;
      font-size: 12px; color: #8A9A8A;
      word-break: break-all;
    }}
    .fallback a {{
      color: #FFB627;
    }}
    hr {{
      border: none; border-top: 1px solid rgba(244,241,233,0.1);
      margin: 24px 0;
    }}
    .footer {{
      font-size: 11px; color: #6B7E6B;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="card">
      <h1>Reset your password</h1>
      <p>
        We received a request to reset the password for your PitchTrack account.
        Click the button below to set a new one. This link expires in 30 minutes.
      </p>
      <a href="{reset_url}" class="btn">Reset Password</a>
      <div class="fallback">
        If the button didn't render, copy and paste this link into your browser:<br />
        <a href="{reset_url}">{reset_url}</a>
      </div>
      <hr />
      <p style="font-size:12px;color:#8A9A8A;margin:0;">
        If you didn't request a password reset, you can safely ignore this email.
      </p>
    </div>
    <div class="footer">
      PitchTrack &bull; Football League Tracker
    </div>
  </div>
</body>
</html>
"""

_RESET_TEXT = """\
Reset your password

We received a request to reset the password for your PitchTrack account.
Follow the link below to set a new one. This link expires in 30 minutes.

{reset_url}

If you didn't request a password reset, you can safely ignore this email.
"""


def send_password_reset_email(to_email: str, reset_url: str) -> bool:
    """
    Send a password-reset email via Resend.

    Args:
        to_email: Recipient email address.
        reset_url: Full password-reset URL (including token and email query params).

    Returns:
        True if the email was accepted by Resend, False on failure.
    """
    api_key = current_app.config.get("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY not configured — skipping email to %s", to_email)
        return False

    from_email = current_app.config.get("RESEND_FROM_EMAIL", "noreply@yourdomain.com")

    resend.api_key = api_key

    try:
        response = resend.Emails.send({
            "from": from_email,
            "to": [to_email],
            "subject": "Reset your PitchTrack password",
            "html": _RESET_HTML.format(reset_url=reset_url),
            "text": _RESET_TEXT.format(reset_url=reset_url),
        })
        logger.info("Password-reset email sent to %s — Resend ID: %s", to_email, response.get("id"))
        return True
    except Exception:
        logger.exception("Failed to send password-reset email to %s", to_email)
        return False
