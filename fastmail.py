# import asyncio

# from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType

from config import notification_settings

# fastmail = FastMail(ConnectionConfig(**notification_settings.model_dump()))
#
#
# async def send_mail():
#     await fastmail.send_message(
#         message=MessageSchema(
#             recipients=["kobbyudemy@gmail.com"],
#             subject="Your Email Delivered with FastShip",
#             body="Things are about to get interesting....",
#             subtype=MessageType.plain,
#         )
#     )
#
#     print("Email sent successfully")

# using mailtrap

import mailtrap as mt

client = mt.MailtrapClient(
    token=notification_settings.MAIL_TRAP_KEY,
    sandbox=notification_settings.MAILTRAP_USE_SANDBOX,
    inbox_id=notification_settings.MAILTRAP_INBOX_ID,  # None is ignored for production
)


mail = mt.Mail(
    sender=mt.Address(email=notification_settings.MAIL_USERNAME, name="Fast Ship"),
    to=[mt.Address(email="johnbrownn1900@gmail.com")],
    subject="Your Email Delivered with FastShip",
    text="Things are about to get interesting....",
)

response = client.send(mail)


# # run coroutine
# asyncio.run(send_mail())
