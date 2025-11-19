from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.seller_schema import SellerCreate
from config import security_settings
from database.models import Seller
from utils.hashing import hash_password, verify_password
from utils.jwt_auth import create_token


class SellerService:
    def __init__(self, session: AsyncSession):
        # get DB session to perform database operation
        self.session = session

    async def add(self, credentials: SellerCreate) -> Seller:
        seller = Seller(
            **credentials.model_dump(exclude=["password"]),
            password_hash=hash_password(credentials.password)
        )
        self.session.add(seller)
        await self.session.commit()
        await self.session.refresh(seller)
        return seller

    # login is same as token
    async def login(self, email, password) -> str:
        # validate the credentials
        result = await self.session.execute(select(Seller).where(Seller.email == email))
        seller = result.scalar()

        pwd = verify_password(password, seller.password_hash)

        if seller is None or not pwd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email or password is incorrect",
            )

        payload = {
            "user": {
                "name": seller.name,
                "email": seller.email,
            }
        }
        token = create_token(payload)

        return token
