from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import oauth_scheme_seller, oauth_scheme_partner
from database.models import Seller, DeliveryPartner
from database.redis import is_jti_blacklisted
from database.session import get_session
from services.delivery_partner import DeliveryPartnerService
from services.seller import SellerService
from services.shipment import ShipmentService
from services.shipment_event import ShipmentEventService
from utils.jwt_auth import verify_token

# async database session dep annotation
sessionDep = Annotated[AsyncSession, Depends(get_session)]


# Shipment service dep
def get_shipment_service(
    session: sessionDep,
):
    return ShipmentService(
        session, DeliveryPartnerService(session), ShipmentEventService(session)
    )


# seller service dep
def get_seller_service(session: sessionDep):
    return SellerService(session)


# access token data dep
async def _get_access_token(token: str) -> dict:
    payload = verify_token(token)

    blacklist = await is_jti_blacklisted(payload["jti"])

    if blacklist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired token",
        )

    return payload


# seller access token
async def get_seller_access_token(token: Annotated[str, Depends(oauth_scheme_seller)]):
    return await _get_access_token(token)


# partner access token
async def get_partner_access_token(
    token: Annotated[str, Depends(oauth_scheme_partner)],
):
    return await _get_access_token(token)


# logged In Seller
async def get_current_seller(
    token_data: Annotated[dict, Depends(get_seller_access_token)],
    session: sessionDep,
):
    seller = await session.get(Seller, UUID(token_data["user"]["id"]))
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found"
        )

    return seller


# logged In partner
async def get_current_partner(
    token_data: Annotated[dict, Depends(get_partner_access_token)],
    session: sessionDep,
):
    partner = await session.get(DeliveryPartner, UUID(token_data["user"]["id"]))
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Delivery Partner not found"
        )

    return partner


# delivery partner service
def get_delivery_partner_service(session: sessionDep):
    return DeliveryPartnerService(session)


# Seller Dep
SellerDep = Annotated[Seller, Depends(get_current_seller)]

# Delivery Partner Dep
DeliveryPartnerDep = Annotated[DeliveryPartner, Depends(get_current_partner)]


# shipment service dep Annotation
ShipmentServiceDep = Annotated[ShipmentService, Depends(get_shipment_service)]

# shipment service dep Annotation
SellerServiceDep = Annotated[SellerService, Depends(get_seller_service)]

# delivery partner service dep Annotation
DeliveryPartnerServiceDep = Annotated[
    DeliveryPartnerService, Depends(get_delivery_partner_service)
]
