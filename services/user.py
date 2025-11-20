from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.base import BaseService
from utils.hashing import verify_password, hash_password
from utils.jwt_auth import create_token


class UserService(BaseService):
    def __init__(self, model: User, session: AsyncSession):
        # get DB session to perform database operation
        self.session = session
        self.model = model

    async def _get_by_email(self, email) -> User | None:
        return await self.session.scalar(
            select(self.model).where(self.model.email == email),
        )

    async def _add_user(self, data: dict):
        user = self.model(**data, password_hash=hash_password(data["password"]))
        return await self._add(user)

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

        payload = {
            "user": {
                "name": user.name,
                "id": str(user.id),
            }
        }
        token = create_token(payload)

        return token
