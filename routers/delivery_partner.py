from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
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

from database.models import DeliveryPartner
from database.redis import add_jti_to_blacklist

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
    update = partner_update.model_dump(exclude_unset=True)

    if not update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided to update"
        )

    # Fetch the partner fresh in the service's session to avoid session conflicts
    partner_from_service_session = await service.session.get(
        DeliveryPartner, partner.id
    )

    if not partner_from_service_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Delivery Partner not found"
        )

    # Update only the fields that were explicitly provided
    for key, value in update.items():
        setattr(partner_from_service_session, key, value)

    return await service.update(partner_from_service_session)


# verify delivery partner email
@router.get("/verify")
async def verify_partner_email(token: str, service: DeliveryPartnerServiceDep):
    await service.verify_email(token)
    return {
        "detail": "Account is verified",
    }


@router.get("/logout")
async def logout_delivery_partner(
    token_data: Annotated[dict, Depends(get_partner_access_token)],
):
    await add_jti_to_blacklist(token_data["jti"], token_data["exp"])
    return {
        "detail": "Successfully logged out",
    }
