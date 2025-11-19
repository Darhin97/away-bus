from datetime import datetime, timezone
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


# enum
class ShipmentStatus(str, Enum):
    placed = "placed"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"


class Shipment(SQLModel, table=True):
    __tablename__ = "shipment"

    id: int = Field(default=None, primary_key=True)
    content: str
    weight: float = Field(default=0.0, le=25)
    destination: int
    status: ShipmentStatus
    estimated_delivery: datetime


class Seller(SQLModel, table=True):
    __tablename__ = "seller"
    id: int = Field(default=None, primary_key=True)
    name: str
    email: EmailStr
    password_hash: str
