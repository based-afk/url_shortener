from redis.asyncio import Redis

from app.config import settings

# Plain connection only. Cache-aside logic is Piece 5 — written by hand.
redis = Redis.from_url(settings.redis_url, decode_responses=True)
