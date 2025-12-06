from typing import Annotated

from fastapi import APIRouter, Depends, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from starlette.templating import Jinja2Templates

from api.dependencies import SellerServiceDep, get_seller_access_token
from api.schemas.seller_schema import SellerCreate, SellerRead
from config import app_settings

from database.redis import add_jti_to_blacklist
from utils.libs import TEMPLATE_DIR

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


# verify seller email
@router.get("/verify")
async def verify_seller_email(token: str, service: SellerServiceDep):
    await service.verify_email(token)
    return {
        "detail": "Account is verified",
    }


# seller password reset
@router.get("/forgot_password")
async def forgot_password(email: EmailStr, service: SellerServiceDep):
    await service.send_password_reset_link(email, router_prefix="seller")
    return {
        "detail": "Check email for password reset link",
    }


### password reset form
@router.get("/reset_password_form")
async def reset_password_form(request: Request, token: str):
    templates = Jinja2Templates(TEMPLATE_DIR)

    return templates.TemplateResponse(
        request=request,
        name="reset.html",
        context={
            "reset_url": f"http://{app_settings.APP_DOMAIN}{router.prefix}/reset_password?token={token}",
        },
    )


# seller reset page
@router.post("/reset_password")
async def reset_password(
    request: Request,
    token: str,
    password: Annotated[str, Form()],
    service: SellerServiceDep,
):
    is_success = await service.reset_password(token, password)

    templates = Jinja2Templates(TEMPLATE_DIR)

    return templates.TemplateResponse(
        request=request,
        name=(
            "password/reset_success.html"
            if is_success
            else "password/reset_failed.html"
        ),
    )


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
