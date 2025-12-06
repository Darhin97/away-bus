from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import ARRAY, INTEGER, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel, Relationship, Column


# enum
class ShipmentStatus(str, Enum):
    placed = "placed"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"


class TagName(str, Enum):
    EXPRESS = "express"
    STANDARD = "standard"
    FRAGILE = "fragile"
    HEAVY = "heavy"
    INTERNATIONAL = "international"
    DOMESTIC = "domestic"
    TEMPERATURE_CONTROLLED = "temperature_controlled"
    GIFT = "gift"
    RETURN = "return"
    DOCUMENT = "document"

    async def tag(self, session: AsyncSession):
        return await session.scalar(select(Tag).where(Tag.name == self.value))


class Tag(SQLModel, table=True):
    __tablename__ = "tag"
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(
            postgresql.UUID(as_uuid=True), default=uuid4, primary_key=True
        ),
    )
    name: TagName
    instruction: str

    # relationship
    shipments: List["Shipment"] = Relationship(
        back_populates="tags",
        link_model="ShipmentTag",
        sa_relationship={
            "lazy": "selectin",
        },
    )


# linking table for shipment
class ShipmentTag(SQLModel, table=True):
    __tablename__ = "shipment_tag"
    shipment_id: UUID = Field(
        foreign_key="shipment.id",
        primary_key=True,
    )
    tag_id: UUID = Field(
        foreign_key="tag.id",
        primary_key=True,
    )


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
    estimated_delivery: datetime
    client_contact_email: EmailStr
    client_contact_phone: int | None

    timeline: list["ShipmentEvent"] = Relationship(
        back_populates="shipment",
        sa_relationship={
            "lazy": "selectin",
        },
    )

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

    review: "Review" = Relationship(
        back_populates="shipment",
        sa_relationship={
            "lazy": "selectin",
        },
    )

    tags: List["Tag"] = Relationship(
        back_populates="shipments",
        link_model=ShipmentTag,
        sa_relationship={
            "lazy": "selectin",
        },
    )

    # Removed status property - it should be computed from timeline in the response schema
    # def status(self):
    #     return self.timeline[-1].status if self.timeline and len(self.timeline) > 0 else None


#     shipment event model
class ShipmentEvent(SQLModel, table=True):
    __tablename__ = "shipment_event"
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(
            postgresql.UUID(as_uuid=True), default=uuid4, primary_key=True
        ),
    )
    created_at: datetime = Field(
        sa_column=Column(postgresql.TIMESTAMP, default=datetime.now)
    )
    location: int
    status: ShipmentStatus
    description: str | None = Field(default=None)

    # relationship
    shipment_id: UUID = Field(foreign_key="shipment.id")
    shipment: Shipment = Relationship(
        back_populates="timeline",
        sa_relationship={
            "lazy": "selectin",
        },
    )


# class for inheritance not table
class User(SQLModel):
    name: str
    email: EmailStr
    email_verified: bool = Field(default=False)
    password_hash: str = Field(exclude=True)


class Seller(User, table=True):
    __tablename__ = "seller"
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(
            postgresql.UUID(as_uuid=True), default=uuid4, primary_key=True
        ),
    )
    address: str | None = Field(default=None)
    zip_code: int | None = Field(default=None)

    created_at: datetime = Field(
        sa_column=Column(postgresql.TIMESTAMP, default=datetime.now)
    )

    shipments: list[Shipment] = Relationship(
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
    serviceable_zip_codes: list[int] = Field(sa_column=Column(ARRAY(INTEGER)))
    max_handling_capacity: int
    created_at: datetime = Field(
        sa_column=Column(postgresql.TIMESTAMP, default=datetime.now)
    )

    shipments: list[Shipment] = Relationship(
        back_populates="delivery_partner",
        sa_relationship={
            "lazy": "selectin",
        },
    )

    @property
    def active_shipments(self):
        return [
            shipment
            for shipment in self.shipments
            if shipment.timeline
            and shipment.timeline[-1].status != ShipmentStatus.delivered
        ]

    @property
    def current_handling_capacity(self):
        return self.max_handling_capacity - len(self.active_shipments)


class Review(SQLModel, table=True):
    __tablename__ = "review"
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(
            postgresql.UUID(as_uuid=True), default=uuid4, primary_key=True
        ),
    )

    created_at: datetime = Field(
        sa_column=Column(postgresql.TIMESTAMP, default=datetime.now)
    )

    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None)

    shipment_id: UUID = Field(foreign_key="shipment.id")
    shipment: Shipment = Relationship(
        back_populates="review",
        sa_relationship={
            "lazy": "selectin",
        },
    )
