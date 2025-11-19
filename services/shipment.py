from datetime import datetime, timedelta
from typing import Any, Coroutine
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.schema import ShipmentCreate, ShipmentUpdate
from database.models import Shipment, ShipmentStatus, Seller


class ShipmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: UUID) -> type[Shipment] | None:
        return await self.session.get(Shipment, id)

    async def add(self, shipment_create: ShipmentCreate, seller: Seller) -> Shipment:
        shipment = Shipment(
            **shipment_create.model_dump(),
            status=ShipmentStatus.placed,
            estimated_delivery=datetime.now() + timedelta(days=3),
            seller_id=seller.id,
        )
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def update(self, shipment_update: ShipmentUpdate, id: UUID) -> Shipment:
        shipment = await self.session.get(Shipment, id)
        shipment.sqlmodel_update(shipment_update)

        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def delete(self, id: UUID) -> None:
        await self.session.delete(self.get(id))
        await self.session.commit()
