from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.cache import redis
from app.db import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis.aclose()
    await engine.dispose()


app = FastAPI(title="URL Shortener", lifespan=lifespan)


@app.get("/health")
async def health():
    checks = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {type(e).__name__}"

    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {type(e).__name__}"

    healthy = all(v == "ok" for v in checks.values())
    return JSONResponse(status_code=200 if healthy else 503, content=checks)


# Routes for POST /shorten, DELETE /{code} and GET /{code} get added in
# Pieces 4-5. GET /{code} is a catch-all, so it must be registered LAST,
# after /health and every other fixed path.
