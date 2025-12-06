# pydantic validation
from datetime import datetime
from random import randint
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, computed_field
from database.models import ShipmentStatus, Tag, TagName


def random_destination():
    return randint(10000, 50000)


class ShipmentSchema(BaseModel):
    content: str = Field(max_length=30)
    weight: float = Field(
        lt=25, description="weight of the shipment is in kilograms (kg)"
    )
    status: str = Field(default="placed")
    destination: int | None = Field(default_factory=random_destination)


class BaseShipment(BaseModel):
    content: str
    weight: float
    destination: int = Field(description="location zipcode", examples=[11001, 11002])


class ShipmentUpdate(BaseModel):
    location: int | None = Field(default=None)
    description: str | None = Field(default=None)
    status: ShipmentStatus | None = Field(default=None)
    estimated_delivery: datetime | None = Field(default=None)


# Pydantic schemas for nested data
class ShipmentEventRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    created_at: datetime
    location: int
    status: ShipmentStatus
    description: str | None = None


class SellerRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    email: EmailStr


class TagRead(BaseModel):
    model_config = {"from_attributes": True}

    name: TagName
    instruction: str


class ShipmentRead(BaseShipment):
    model_config = {"from_attributes": True}

    id: UUID
    timeline: list[ShipmentEventRead]
    estimated_delivery: datetime
    seller: SellerRead
    tags: list[TagRead]

    @computed_field
    @property
    def status(self) -> ShipmentStatus | None:
        """Get the latest status from timeline"""
        return self.timeline[-1].status if self.timeline else None


class ShipmentCreate(BaseShipment):
    client_contact_email: EmailStr
    client_contact_phone: int | None = Field(default=None)


class ShipmentReview(BaseShipment):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None)
