from uuid import UUID

from pydantic import BaseModel, EmailStr


class BaseSeller(BaseModel):
    name: str
    email: EmailStr


class SellerRead(BaseSeller):
    id: UUID


class SellerCreate(BaseSeller):
    password: str
