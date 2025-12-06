from typing import Any
import mailtrap as mt

from celery import Celery
from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr

from config import db_settings, notification_settings

app = Celery(
    "api_tasks",
    broker=db_settings.REDIS_URL(9),
    backend=db_settings.REDIS_URL(9),
    broker_connection_retry_on_startup=True,
)


env = Environment(loader=FileSystemLoader("templates"))

client = mt.MailtrapClient(
    token=notification_settings.MAIL_TRAP_KEY,
    sandbox=notification_settings.MAILTRAP_USE_SANDBOX,
    inbox_id=notification_settings.MAILTRAP_INBOX_ID,  # None is ignored for production
)


@app.task
def send_template_email(
    recipients: list[EmailStr],
    subject: str,
    context: dict[str, Any],
    template_name: str = "mail_placed.html",
):
    template = env.get_template(template_name)

    html_content = template.render(**context)

    # Build Mailtrap message
    mail = mt.Mail(
        sender=mt.Address(email=notification_settings.MAIL_USERNAME, name="Fast Ship"),
        to=[mt.Address(email=recipients[0])],
        subject=subject or "Your Email Delivered with FastShip",
        html=html_content,
    )

    # send email
    client.send(mail)
    return "Message sent successfully"
