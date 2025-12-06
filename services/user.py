from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import app_settings
from database.models import User
from services.base import BaseService
from utils.hashing import verify_password, hash_password
from utils.jwt_auth import create_token, generate_url_safe_token, decode_url_safe_token
from worker.tasks import send_template_email


class UserService(BaseService):
    def __init__(self, model: User, session: AsyncSession):
        self.model = model
        self.session = session

    async def _get_by_email(self, email) -> User | None:
        return await self.session.scalar(
            select(self.model).where(self.model.email == email),
        )

    async def _add_user(self, data: dict, router_prefix):
        user = self.model(**data, password_hash=hash_password(data["password"]))

        new_user = await self._add(user)
        token = generate_url_safe_token({"email": user.email, "id": str(user.id)})

        send_template_email.delay(
            recipients=[new_user.email],
            subject="Verify Your Account with Fastship",
            context={
                "username": new_user.name,
                "verification_url": f"http://{app_settings.APP_DOMAIN}/{router_prefix}/verify?token={token}",
            },
            template_name="mail_email_verify.html",
        )

        return new_user

    async def verify_email(self, token: str):
        token_data = decode_url_safe_token(token)

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token",
            )

        uuid = UUID(token_data["id"])
        user = await self._get(uuid)
        user.email_verified = True

        await self._update(user)

    # generates token
    async def _login_user(self, email, password) -> str:
        # validate the credentials
        user = await self._get_by_email(email)

        pwd = verify_password(password, user.password_hash)

        if user is None or not pwd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email or password is incorrect",
            )

        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not verified",
            )

        payload = {
            "user": {
                "name": user.name,
                "id": str(user.id),
            }
        }
        token = create_token(payload)

        return token

    async def send_password_reset_link(self, email, router_prefix):
        user = await self._get_by_email(email)

        token = generate_url_safe_token({"id": str(user.id)}, salt="password-reset")

        send_template_email.delay(
            recipients=[user.email],
            subject="Fastship Password Reset Link",
            context={
                "username": user.name,
                "reset_url": f"http://{app_settings.APP_DOMAIN}/{router_prefix}/reset_password_form?token={token}",
            },
            template_name="mail_password_reset.html",
        )

    async def reset_password(self, token: str, new_password: str) -> bool:
        token_data = decode_url_safe_token(
            token, salt="password-reset", expiry=timedelta(hours=2)
        )
        if not token_data:
            return False

        user = await self._get(UUID(token_data["id"]))
        user.password_hash = hash_password(new_password)

        await self._update(user)

        return True
