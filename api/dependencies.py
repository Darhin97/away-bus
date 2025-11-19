from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session
from services.seller import SellerService
from services.shipment import ShipmentService

# async database session dep annotation
sessionDep = Annotated[AsyncSession, Depends(get_session)]


# Shipment service dep
def get_shipment_service(session: sessionDep):
    return ShipmentService(session)


# seller service dep
def get_seller_service(session: sessionDep):
    return SellerService(session)


# shipment service dep Annotation
ShipmentServiceDep = Annotated[ShipmentService, Depends(get_shipment_service)]

# shipment service dep Annotation
SellerServiceDep = Annotated[SellerService, Depends(get_seller_service)]
