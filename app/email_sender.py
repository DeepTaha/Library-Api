import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime, timezone

import aiosmtplib

GMAIL_USER      = os.getenv("GMAIL_USER")
GMAIL_PASSWORD  = os.getenv("GMAIL_APP_PASSWORD")
REPORT_RECIPIENT = os.getenv("REPORT_RECIPIENT")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


async def send_borrowing_report(username: str, pdf_bytes: bytes) -> None:
    """
    Send a borrowing report PDF as an email attachment.
    Sender and recipient are both read from environment variables.
    """
    if not GMAIL_USER or not GMAIL_PASSWORD:
        raise RuntimeError("GMAIL_USER and GMAIL_APP_PASSWORD must be set in .env")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename  = f"borrowing_report_{username}_{timestamp}.pdf"

    msg = MIMEMultipart()
    msg["From"]    = GMAIL_USER
    msg["To"]      = REPORT_RECIPIENT
    msg["Subject"] = f"Library Borrowing Report — {username} ({timestamp})"

    body = MIMEText(
        f"Hi,\n\n"
        f"Please find attached the borrowing report for user '{username}'.\n"
        f"Generated on {datetime.now(timezone.utc).strftime('%d %b %Y at %I:%M %p UTC')}.\n\n"
        f"— Library Book Borrowing System",
        "plain",
    )
    msg.attach(body)

    attachment = MIMEBase("application", "pdf")
    attachment.set_payload(pdf_bytes)
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition",
        f'attachment; filename="{filename}"',
    )
    msg.attach(attachment)

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=GMAIL_USER,
        password=GMAIL_PASSWORD,
        start_tls=True,
    )
