from fastapi_mail import FastMail, ConnectionConfig, MessageSchema

from config import notification_settings

fastmail = FastMail(ConnectionConfig(**notification_settings.model_dump()))

fastmail.send_message(message=MessageSchema)
