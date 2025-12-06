from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.seller_schema import SellerCreate
from database.models import Seller
from services.user import UserService


class SellerService(UserService):
    def __init__(self, session: AsyncSession):
        super().__init__(Seller, session)

    async def add(self, seller_create: SellerCreate) -> Seller:
        return await self._add_user(seller_create.model_dump(), "seller")

    # login is same as token
    async def login(self, email, password) -> str:
        # validate the credentials
        return await self._login_user(email, password)
