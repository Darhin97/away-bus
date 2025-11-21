from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlmodel import select

from api.schemas.schema import ShipmentCreate, ShipmentUpdate
from database.models import Shipment, ShipmentStatus, Seller, DeliveryPartner, ShipmentEvent
from services.base import BaseService
from services.delivery_partner import DeliveryPartnerService
from services.shipment_event import ShipmentEventService


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
        timeline_stmt = select(ShipmentEvent).where(
            ShipmentEvent.shipment_id == id
        ).order_by(ShipmentEvent.created_at)
        timeline_result = await self.session.execute(timeline_stmt)
        timeline = list(timeline_result.scalars().all())

        # Manually set the loaded relationships on the shipment object
        # Use object.__setattr__ to bypass the Relationship descriptor
        object.__setattr__(shipment, 'seller', seller)
        object.__setattr__(shipment, 'delivery_partner', partner)
        object.__setattr__(shipment, 'timeline', timeline)

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
        return shipment

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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized"
            )

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

    async def delete(self, id: UUID) -> None:
        shipment = await self.get(id)
        if shipment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with id {id} not found",
            )
        await self._delete(shipment)
