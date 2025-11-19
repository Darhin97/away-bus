import jwt
from datetime import datetime, timedelta

from config import security_settings


ALGORITHM = security_settings.JWT_ALGORITHM
SECRET = security_settings.JWT_SECRET


def create_token(data: dict):
    payload = {
        **data,
        "exp": datetime.now() + timedelta(hours=24),
    }

    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def verify_token(token: str):
    return jwt.decode(token, SECRET, algorithms=["HS256"])
