import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings

FROM_NAME = "ATELIER-ARANIER"


def send_email(to: str, subject: str, html_body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((FROM_NAME, settings.SMTP_FROM))
    msg["To"] = to
    msg.set_content("Este correo requiere un cliente compatible con HTML.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)
