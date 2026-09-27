from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis.asyncio import Redis

from app.config import settings

redis = Redis.from_url(settings.redis_url, decode_responses=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis.aclose()


app = FastAPI(title="Rate Limiter", lifespan=lifespan)


class CheckRequest(BaseModel):
    client_id: str  # e.g. "create:ip:203.0.113.9" — built by the caller


class CheckResponse(BaseModel):
    allowed: bool
    remaining: int
    retry_after_seconds: float | None = None  # feeds the Retry-After header on 429


@app.post("/check", response_model=CheckResponse)
async def check(req: CheckRequest):
    # Piece 6: call ratelimit.check(...) here.
    raise HTTPException(status_code=501, detail="Not implemented yet")


@app.get("/health")
async def health():
    try:
        await redis.ping()
        return {"redis": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"redis": f"error: {type(e).__name__}"})
