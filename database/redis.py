import time

from redis.asyncio import Redis

from config import db_settings

_token_blacklist = Redis(
    host=db_settings.REDIS_HOST,
    port=db_settings.REDIS_PORT,
    db=0,
    decode_responses=True,  # return strings instead of bytes
)


async def add_jti_to_blacklist(jti: str, exp: int):
    # Calculate remaining lifetime of the token
    now = int(time.time())
    ttl = exp - now

    if ttl <= 0:
        return  # token already expired

    await _token_blacklist.set(jti, "blacklisted")


async def is_jti_blacklisted(jti: str) -> bool:
    return await _token_blacklist.exists(jti)
