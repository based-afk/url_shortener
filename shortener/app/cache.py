from redis.asyncio import Redis

from app.config import settings

redis = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_timeout=0.1,          # give up on a slow command after 100ms
    socket_connect_timeout=0.1,  # give up connecting after 100ms
)