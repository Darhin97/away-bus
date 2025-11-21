from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.schema import ShipmentCreate, ShipmentUpdate
from database.models import Shipment, ShipmentStatus, Seller
from services.base import BaseService
from services.delivery_partner import DeliveryPartnerService


class ShipmentService(BaseService):
    def __init__(self, session: AsyncSession, partner_service: DeliveryPartnerService):
        super().__init__(Shipment, session)
        self.partner_service = partner_service

    async def get(self, id: UUID) -> Shipment | None:
        return await self._get(id)

    async def add(self, shipment_create: ShipmentCreate, seller: Seller) -> Shipment:
        # Find delivery partner first based on destination
        partner = await self.partner_service.assign_shipment(
            shipment_create.destination
        )

        # Create shipment with all required fields including delivery_partner_id
        shipment = Shipment(
            **shipment_create.model_dump(),
            status=ShipmentStatus.placed,
            estimated_delivery=datetime.now() + timedelta(days=3),
            seller_id=seller.id,
            delivery_partner_id=partner.id,
        )

        return await self._add(shipment)

    async def update(self, shipment_update: ShipmentUpdate, id: UUID) -> Shipment:
        shipment = await self.session.get(Shipment, id)
        shipment.sqlmodel_update(shipment_update)

        return await self._update(shipment)

    async def delete(self, id: UUID) -> None:
        shipment = await self.get(id)
        if shipment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment with id {id} not found"
            )
        await self._delete(shipment)
