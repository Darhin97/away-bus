import uuid
from typing import Any
import jwt
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from config import security_settings


ALGORITHM = security_settings.JWT_ALGORITHM
SECRET = security_settings.JWT_SECRET


# use  its dangerous for email token generation
_serializer = URLSafeTimedSerializer(security_settings.JWT_SECRET)


# generate access token
def create_token(
    data: dict[str, dict[str, Any]], expiry: timedelta = timedelta(hours=24)
) -> str:
    payload = {
        **data,
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + expiry,
    }

    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET,
            algorithms=[ALGORITHM],
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )

    except jwt.InvalidTokenError:
        # Catches signature errors, decode errors, invalid claims, etc.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


def generate_url_safe_token(data: dict, salt: str | None = None) -> str:
    return _serializer.dumps(data, salt)


def decode_url_safe_token(
    token: str, salt: str | None = None, expiry: timedelta | None = None
) -> dict | None:
    try:
        return _serializer.loads(
            token,
            salt=salt,
            max_age=expiry.total_seconds() if expiry else None,
        )
    except (BadSignature, SignatureExpired):
        return None
