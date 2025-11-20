from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.dependencies import SellerServiceDep, get_seller_access_token
from api.schemas.seller_schema import SellerCreate, SellerRead

from database.redis import add_jti_to_blacklist


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


@router.get("/logout")
async def logout_seller(token_data: Annotated[dict, Depends(get_seller_access_token)]):
    await add_jti_to_blacklist(token_data["jti"], token_data["exp"])
    return {
        "detail": "Successfully logged out",
    }


# @router.get("/dashboard", response_model=SellerRead)
# async def dashboard(token: Annotated[str, Depends(oauth_scheme)], session: sessionDep):
#
#     payload = verify_token(token)
#
#     seller = await session.get(Seller, payload["user"]["id"])
#     if seller is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found"
#         )
#
#     return seller
