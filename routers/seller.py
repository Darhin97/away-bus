from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.dependencies import SellerServiceDep
from api.schemas.seller_schema import SellerCreate, SellerRead
from core.security import oauth_scheme

router = APIRouter(
    prefix="/seller",
    tags=["seller"],
)


@router.post("/signup", response_model=SellerRead)
async def register_seller(seller: SellerCreate, service: SellerServiceDep):
    return await service.add(seller)


# login seller -> returns token
@router.post("/login")
async def login_seller(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: SellerServiceDep,
):
    token = await service.login(request_form.username, request_form.password)

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/dashboard")
async def dashboard(token: Annotated[str, Depends(oauth_scheme)]):
    return {
        "token": token,
    }
