from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import oauth_scheme
from database.models import Seller
from database.redis import is_jti_blacklisted
from database.session import get_session
from services.seller import SellerService
from services.shipment import ShipmentService
from utils.jwt_auth import verify_token

# async database session dep annotation
sessionDep = Annotated[AsyncSession, Depends(get_session)]


# Shipment service dep
def get_shipment_service(session: sessionDep):
    return ShipmentService(session)


# seller service dep
def get_seller_service(session: sessionDep):
    return SellerService(session)


# access token data dep
async def get_access_token(token: Annotated[str, Depends(oauth_scheme)]) -> dict:
    payload = verify_token(token)

    blacklist = await is_jti_blacklisted(payload["jti"])

    if blacklist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired token",
        )

    return payload


# logged In Seller
async def get_current_user(
    token_data: Annotated[dict, Depends(get_access_token)], session: sessionDep
):
    seller = await session.get(Seller, UUID(token_data["user"]["id"]))
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found"
        )

    return seller


# Seller Dep
SellerDep = Annotated[Seller, Depends(get_current_user)]


# shipment service dep Annotation
ShipmentServiceDep = Annotated[ShipmentService, Depends(get_shipment_service)]

# shipment service dep Annotation
SellerServiceDep = Annotated[SellerService, Depends(get_seller_service)]
