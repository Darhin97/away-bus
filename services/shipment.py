from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from sqlmodel import select

from api.schemas.schema import ShipmentCreate
from core.exceptions import ClientNotAuthorized
from database.models import (
    Shipment,
    ShipmentStatus,
    Seller,
    DeliveryPartner,
    ShipmentEvent,
    Review,
    TagName,
    Tag,
    ShipmentTag,
)
from services.base import BaseService
from services.delivery_partner import DeliveryPartnerService
from services.shipment_event import ShipmentEventService
from utils.jwt_auth import decode_url_safe_token


class ShipmentService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
        partner_service: DeliveryPartnerService,
        event_service: ShipmentEventService,
    ):
        super().__init__(Shipment, session)
        self.partner_service = partner_service
        self.event_service = event_service

    async def get(self, id: UUID) -> Shipment | None:
        # Load seller, delivery partner, and timeline separately
        # Then construct the response manually to avoid SQLModel Relationship issues

        # Get shipment basic data
        shipment_stmt = select(Shipment).where(Shipment.id == id)
        shipment_result = await self.session.execute(shipment_stmt)
        shipment = shipment_result.unique().scalar_one_or_none()

        if not shipment:
            return None

        # Get seller_id and delivery_partner_id from the shipment
        seller_id = shipment.seller_id
        partner_id = shipment.delivery_partner_id

        # Load seller
        seller = await self.session.get(Seller, seller_id)

        # Load delivery_partner
        partner = await self.session.get(DeliveryPartner, partner_id)

        # Load timeline events
        timeline_stmt = (
            select(ShipmentEvent)
            .where(ShipmentEvent.shipment_id == id)
            .order_by(ShipmentEvent.created_at)
        )
        timeline_result = await self.session.execute(timeline_stmt)
        timeline = list(timeline_result.scalars().all())

        # Load tags via the many-to-many relationship
        tags_stmt = (
            select(Tag)
            .join(ShipmentTag, ShipmentTag.tag_id == Tag.id)
            .where(ShipmentTag.shipment_id == id)
        )
        tags_result = await self.session.execute(tags_stmt)
        tags = list(tags_result.scalars().all())

        # Manually set the loaded relationships on the shipment object
        # Use object.__setattr__ to bypass the Relationship descriptor
        object.__setattr__(shipment, "seller", seller)
        object.__setattr__(shipment, "delivery_partner", partner)
        object.__setattr__(shipment, "timeline", timeline)
        object.__setattr__(shipment, "tags", tags)

        return shipment

    async def add(self, shipment_create: ShipmentCreate, seller: Seller) -> Shipment:
        # Find delivery partner first based on destination
        partner = await self.partner_service.assign_shipment(
            shipment_create.destination
        )

        # Create shipment with all required fields including delivery_partner_id
        new_shipment = Shipment(
            **shipment_create.model_dump(),
            estimated_delivery=datetime.now() + timedelta(days=3),
            seller_id=seller.id,
            delivery_partner_id=partner.id,
        )

        # create shipment
        shipment = await self._add(new_shipment)

        # event - use seller zip_code if available, otherwise use shipment destination
        await self.event_service.add(
            shipment,
            location=seller.zip_code or shipment.destination,
            status=ShipmentStatus.placed,
            description=f"assigned to {partner.name}",
        )

        # Reload shipment with relationships properly loaded
        return await self.get(shipment.id)

    async def update(
        self, shipment_update: dict, id: UUID, partner: DeliveryPartner
    ) -> Shipment:
        # validate logged in partner with assigned partner
        # on the shipment with given id
        shipment = await self.get(id)

        if shipment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with id {id} not found",
            )

        if shipment.delivery_partner_id != partner.id:
            raise ClientNotAuthorized()

        # shipment_update is already a dict with only non-None values
        update = shipment_update

        # Update estimated_delivery if provided
        if "estimated_delivery" in update:
            shipment.estimated_delivery = update["estimated_delivery"]

        # Create event if there are other fields besides estimated_delivery
        if len(update) > 1 or "estimated_delivery" not in update:
            await self.event_service.add(shipment=shipment, **update)

        # Update the shipment in the database
        await self._update(shipment)

        # Reload the shipment to get the updated timeline
        updated_shipment = await self.get(id)
        return updated_shipment

    # rate a shipment
    async def rate(self, token: str, rating: int, comment: str):
        token_data = decode_url_safe_token(token)

        if not token_data:
            raise ClientNotAuthorized()

        uuid = UUID(token_data["id"])
        shipment = await self.get(uuid)

        new_review = Review(
            rating=rating,
            comment=comment if comment else None,
            shipment_id=shipment.id,
        )

        self.session.add(new_review)
        await self.session.commit()

    ### adding a tag
    async def add_tag(self, id: UUID, tag_name: TagName):
        shipment = await self.get(id)
        if shipment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with id {id} not found",
            )

        # Get the tag from the database
        tag = await tag_name.tag(self.session)
        if tag is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_name.value} not found in database",
            )

        # Check if the tag is already associated with this shipment
        existing_link = await self.session.execute(
            select(ShipmentTag).where(
                ShipmentTag.shipment_id == id, ShipmentTag.tag_id == tag.id
            )
        )
        if existing_link.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag already exists on shipment",
            )

        # Create the link in the ShipmentTag table
        shipment_tag = ShipmentTag(shipment_id=id, tag_id=tag.id)
        self.session.add(shipment_tag)
        await self.session.commit()

        # Reload and return the shipment with updated tags
        return await self.get(id)

    ### removing a tag
    async def remove_tag(self, id: UUID, tag_name: TagName):
        shipment = await self.get(id)
        if shipment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with id {id} not found",
            )

        # Get the tag from the database
        tag = await tag_name.tag(self.session)
        if tag is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_name.value} not found in database",
            )

        # Find the link in the ShipmentTag table
        existing_link_result = await self.session.execute(
            select(ShipmentTag).where(
                ShipmentTag.shipment_id == id, ShipmentTag.tag_id == tag.id
            )
        )
        existing_link = existing_link_result.scalar_one_or_none()

        if not existing_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag does not exist on shipment",
            )

        # Delete the link from the ShipmentTag table
        await self.session.delete(existing_link)
        await self.session.commit()

        # Reload and return the shipment with updated tags
        return await self.get(id)

    # cancel shipment
    async def cancel(self, id: UUID, seller: Seller) -> Shipment:
        # validate seller
        shipment = await self.get(id)

        if shipment.seller_id != seller.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized"
            )

        event = await self.event_service.add(
            shipment=shipment, status=ShipmentStatus.cancelled
        )

        shipment.timeline.append(event)
        return shipment

    async def delete(self, id: UUID) -> None:
        shipment = await self.get(id)
        if shipment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with id {id} not found",
            )
        await self._delete(shipment)
