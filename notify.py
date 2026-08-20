"""
Notification channels.

- create_issue(): opens a GitHub Issue, which is your approval screen.
- send_sms_via_email(): sends a short text through your carrier's free
  email-to-SMS gateway. This is the "primary" method per your setup.
- send_via_ntfy(): commented-out fallback, ready to enable if the carrier
  gateway proves unreliable for you (see README).
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText

import requests


def create_issue(title: str, body: str) -> str | None:
    """
    Opens a GitHub Issue in the current repo using the built-in GITHUB_TOKEN.
    Returns the issue URL, or None on failure.
    """
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]  # auto-set by Actions, e.g. "you/trade-watch"

    resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        json={"title": title, "body": body, "labels": ["trade-suggestion"]},
        timeout=15,
    )

    if resp.status_code != 201:
        print(f"Failed to create issue: {resp.status_code} {resp.text}")
        return None

    return resp.json()["html_url"]


def send_sms_via_email(message: str) -> bool:
    """
    Sends `message` as a text via your carrier's email-to-SMS gateway.

    Required secrets (set in GitHub repo Settings > Secrets and variables > Actions):
      SMTP_SERVER          e.g. smtp.gmail.com
      SMTP_PORT            e.g. 587
      SMTP_USER            the email account sending the message
      SMTP_PASS            an app password (NOT your normal email password)
      SMS_GATEWAY_ADDRESS  e.g. 5551234567@vtext.com or 5551234567@mypixmessages.com

    Keep `message` short - vtext.com in particular truncates long texts.
    """
    smtp_server = os.environ["SMTP_SERVER"]
    smtp_port = int(os.environ["SMTP_PORT"])
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    gateway_address = os.environ["SMS_GATEWAY_ADDRESS"]

    msg = MIMEText(message)
    msg["From"] = smtp_user
    msg["To"] = gateway_address
    msg["Subject"] = ""  # many gateways prepend the subject to the text - keep it blank

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [gateway_address], msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send SMS via email gateway: {e}")
        return False


# --- Fallback option (disabled by default) ---
# If vtext.com / mypixmessages.com prove unreliable for your Xfinity Mobile
# line, ntfy.sh is a free, more reliable alternative. To switch:
#   1. Install the ntfy app and subscribe to a private topic name.
#   2. Add an NTFY_TOPIC secret with that topic name.
#   3. In main.py, replace the send_sms_via_email(...) call with send_via_ntfy(...).
#
# def send_via_ntfy(message: str) -> bool:
#     topic = os.environ["NTFY_TOPIC"]
#     resp = requests.post(f"https://ntfy.sh/{topic}", data=message.encode("utf-8"), timeout=15)
#     return resp.status_code == 200
