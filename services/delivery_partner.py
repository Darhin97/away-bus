from fastapi import HTTPException, status
from sqlalchemy import Sequence
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import any_
from sqlmodel import select

from api.schemas.delivery_partner import DeliveryPartnerCreate, DeliveryPartnerUpdate
from database.models import DeliveryPartner, Shipment
from services.user import UserService


class DeliveryPartnerService(UserService):
    def __init__(self, session):
        super().__init__(DeliveryPartner, session)

    async def add(self, delivery_partner: DeliveryPartnerCreate):
        return await self._add_user(delivery_partner.model_dump())

    async def get_partners_by_zipcode(self, zipcode: int) -> Sequence[DeliveryPartner]:
        result = await self.session.execute(
            select(DeliveryPartner).where(
                zipcode == any_(DeliveryPartner.serviceable_zip_codes)
            )
        )
        return result.scalars().all()

    async def assign_shipment(self, shipment: Shipment):
        eligible_delivery_partners = await self.get_partners_by_zipcode(
            shipment.destination
        )

        print("ELIGIBLE DELIVERY PARTNERS", eligible_delivery_partners)
        for partner in eligible_delivery_partners:
            if partner.current_handling_capacity > 0:
                partner.shipments.append(shipment)
                return partner

        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No delivery partner found",
        )

    async def update(self, delivery_partner: DeliveryPartner):
        return await self._update(delivery_partner)

    async def login(self, email, password):
        return await self._login_user(email, password)
