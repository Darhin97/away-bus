# pydantic validation
from datetime import datetime
from enum import Enum
from random import randint
from uuid import UUID

from pydantic import BaseModel, Field
from database.models import ShipmentStatus, Seller


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
    destination: int


class ShipmentUpdate(BaseModel):
    status: ShipmentStatus | None = Field(default=None)
    estimated_delivery: datetime | None = Field(default=None)


class ShipmentRead(BaseShipment):
    id: UUID
    status: ShipmentStatus
    estimated_delivery: datetime
    seller: Seller


class ShipmentCreate(BaseShipment):
    pass
