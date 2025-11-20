from datetime import datetime, timezone
from enum import Enum
from typing import List
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import ARRAY, INTEGER
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, SQLModel, Relationship, Column


# enum
class ShipmentStatus(str, Enum):
    placed = "placed"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"


class Shipment(SQLModel, table=True):
    __tablename__ = "shipment"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(
            postgresql.UUID(as_uuid=True), default=uuid4, primary_key=True
        ),
    )
    content: str
    weight: float = Field(default=0.0, le=25)
    destination: int
    status: ShipmentStatus
    estimated_delivery: datetime
    created_at: datetime = Field(
        sa_column=Column(postgresql.TIMESTAMP, default=datetime.now)
    )

    seller_id: UUID = Field(foreign_key="seller.id")
    seller: "Seller" = Relationship(
        back_populates="shipments",
        sa_relationship={
            "lazy": "selectin",
        },
    )

    delivery_partner_id: UUID = Field(foreign_key="delivery_partner.id")
    delivery_partner: "DeliveryPartner" = Relationship(
        back_populates="shipments",
        sa_relationship={
            "lazy": "selectin",
        },
    )


# class for inheritance not table
class User(SQLModel):
    name: str
    email: EmailStr
    password_hash: str = Field(exclude=True)


class Seller(User, table=True):
    __tablename__ = "seller"
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(
            postgresql.UUID(as_uuid=True), default=uuid4, primary_key=True
        ),
    )
    created_at: datetime = Field(
        sa_column=Column(postgresql.TIMESTAMP, default=datetime.now)
    )

    shipments: List[Shipment] = Relationship(
        back_populates="seller",
        sa_relationship={
            "lazy": "selectin",
        },
    )


class DeliveryPartner(User, table=True):
    __tablename__ = "delivery_partner"
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(
            postgresql.UUID(as_uuid=True), default=uuid4, primary_key=True
        ),
    )
    serviceable_zip_code: list[int] = Field(sa_column=Column(ARRAY(INTEGER)))
    max_handling_capacity: int
    created_at: datetime = Field(
        sa_column=Column(postgresql.TIMESTAMP, default=datetime.now)
    )

    shipments: List[Shipment] = Relationship(
        back_populates="delivery_partner",
        sa_relationship={
            "lazy": "selectin",
        },
    )
