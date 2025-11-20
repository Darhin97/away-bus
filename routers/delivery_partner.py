from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.dependencies import (
    get_partner_access_token,
    DeliveryPartnerDep,
    DeliveryPartnerServiceDep,
)
from api.schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerRead,
    DeliveryPartnerUpdate,
)

from database.redis import add_jti_to_blacklist
from services.delivery_partner import DeliveryPartnerService

router = APIRouter(
    prefix="/partner",
    tags=["Delivery Partner"],
)


@router.post("/signup", response_model=DeliveryPartnerRead)
async def register_delivery_partner(
    seller: DeliveryPartnerCreate, service: DeliveryPartnerServiceDep
):
    return await service.add(seller)


# login delivery partner -> returns token
@router.post("/login")
async def login_delivery_partner(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: DeliveryPartnerServiceDep,
):
    token = await service.login(request_form.username, request_form.password)

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# update delivery partner
@router.post("/", response_model=DeliveryPartnerRead)
async def update_delivery_partner(
    partner_update: DeliveryPartnerUpdate,
    partner: DeliveryPartnerDep,
    service: DeliveryPartnerServiceDep,
):
    return await service.update(partner.sqlmodel_update(partner_update))


@router.get("/logout")
async def logout_delivery_partner(
    token_data: Annotated[dict, Depends(get_partner_access_token)],
):
    await add_jti_to_blacklist(token_data["jti"], token_data["exp"])
    return {
        "detail": "Successfully logged out",
    }
