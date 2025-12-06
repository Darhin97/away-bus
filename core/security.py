# from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer  # , HTTPBearer

# from sqlalchemy.sql.annotation import Annotated

# from utils.jwt_auth import verify_token

oauth_scheme_seller = OAuth2PasswordBearer(
    tokenUrl="/seller/login", scheme_name="Seller"
)
oauth_scheme_partner = OAuth2PasswordBearer(
    tokenUrl="/partner/login", scheme_name="Delivery Partner"
)


# # manual implementation of bearer token -> when not using oauth@ password bearer
# class AccessTokenBearer(HTTPBearer):
#     async def __call__(self, request):
#         auth_credentials = await super().__call__(request)
#         token = auth_credentials.credentials
#
#         token_data = verify_token(token)
#
#         return token_data
#
#
# access_token_bearer = AccessTokenBearer()
#
# Annotated[dict, Depends(access_token_bearer)]
