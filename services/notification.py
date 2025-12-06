from typing import Any

import mailtrap as mt
from fastapi import BackgroundTasks
from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr

from config import notification_settings


# -- Load template --


class NotificationService:
    def __init__(self, tasks: BackgroundTasks):
        self.tasks = tasks
        self.client = mt.MailtrapClient(
            token=notification_settings.MAIL_TRAP_KEY,
            sandbox=notification_settings.MAILTRAP_USE_SANDBOX,
            inbox_id=notification_settings.MAILTRAP_INBOX_ID,  # None is ignored for production
        )

    async def send_email(
        self,
        recipients: list[EmailStr],
        subject: str,
        body: str,
    ):
        mail = mt.Mail(
            sender=mt.Address(
                email=notification_settings.MAIL_USERNAME, name="Fast Ship"
            ),
            to=[mt.Address(email=recipients[0])],
            subject=subject or "Your Email Delivered with FastShip",
            text=body,
        )
        # response = self.client.send(mail)
        self.tasks.add_task(self.client.send, mail)

        # return {"detail": "Mail sent for ✅"}

    async def send_template_email(
        self,
        recipients: list[EmailStr],
        subject: str,
        context: dict[str, Any],
        template_name: str = "mail_placed.html",
    ):
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template(template_name)

        # Render with variables
        # html_content = template.render(
        #     seller=context["seller"] or None,
        #     partner=context["partner"] or None,
        #     verification_url=context["verification_url"] or None,
        #     username=context["username"] or None,
        #     id=context["id"] or None,
        # )
        html_content = template.render(**context)

        mail = mt.Mail(
            sender=mt.Address(
                email=notification_settings.MAIL_USERNAME, name="Fast Ship"
            ),
            to=[mt.Address(email=recipients[0])],
            subject=subject or "Your Email Delivered with FastShip",
            html=html_content,
        )

        self.tasks.add_task(self.client.send, mail)
