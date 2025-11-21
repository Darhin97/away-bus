from fastapi import HTTPException, status
from sqlalchemy import Sequence, func
from sqlalchemy.sql.expression import any_
from sqlmodel import select

from api.schemas.delivery_partner import DeliveryPartnerCreate, DeliveryPartnerUpdate
from database.models import DeliveryPartner, Shipment, ShipmentStatus
from services.user import UserService


class DeliveryPartnerService(UserService):
    def __init__(self, session):
        super().__init__(DeliveryPartner, session)

    async def add(self, delivery_partner: DeliveryPartnerCreate):
        return await self._add_user(delivery_partner.model_dump())

    async def get_partners_by_zipcode(self, zipcode: int) -> Sequence[DeliveryPartner]:
        result = await self.session.execute(
            select(DeliveryPartner)
            .where(zipcode == any_(DeliveryPartner.serviceable_zip_codes))
        )
        return result.scalars().all()

    async def assign_shipment(self, destination: int):
        eligible_delivery_partners = await self.get_partners_by_zipcode(destination)

        # Find partner with available capacity
        for partner in eligible_delivery_partners:
            # Count active shipments for this partner (not delivered)
            active_count_result = await self.session.execute(
                select(func.count(Shipment.id))
                .where(
                    Shipment.delivery_partner_id == partner.id,
                    Shipment.status != ShipmentStatus.delivered
                )
            )
            active_shipments_count = active_count_result.scalar() or 0
            current_capacity = partner.max_handling_capacity - active_shipments_count

            if current_capacity > 0:
                return partner

        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No delivery partner found",
        )

    async def update(self, delivery_partner: DeliveryPartner):
        return await self._update(delivery_partner)

    async def login(self, email, password):
        return await self._login_user(email, password)
