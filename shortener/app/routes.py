from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.codes import code_to_id, id_to_code
from app.config import settings
from app.db import get_session
from app.models import Link
from app.schemas import ShortenRequest, ShortenResponse
from app.tokens import new_delete_token
from fastapi import HTTPException
from fastapi.responses import RedirectResponse

from app.cache import redis
from redis.exceptions import RedisError

CACHE_TTL_SECONDS = 24*60*60

router = APIRouter()


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
async def shorten(
    req: ShortenRequest, session: AsyncSession = Depends(get_session)
) -> ShortenResponse:
    # Policy: every request creates a new link, even for a URL that already
    # exists. Each link has its own owner (delete token) and its own expiry.
    token, token_hash = new_delete_token()

    expires_at = None
    if req.expires_in_seconds is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=req.expires_in_seconds
        )

    link = Link(
        long_url=str(req.long_url),
        delete_token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(link)
    await session.commit() 

    code = id_to_code(link.id)
    return ShortenResponse(
        code=code,
        short_url=f"{settings.base_url}/{code}",
        delete_token=token,
        expires_at=expires_at,
    )
from fastapi import Response, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.tokens import verify_token

# Reads "Authorization: Bearer <token>". auto_error=False means a missing
# header gives None instead of FastAPI's default error, so we choose the 401.
bearer = HTTPBearer(auto_error=False)


@router.delete("/{code}", status_code=204)
async def delete_link(
    code: str,
    creds: HTTPAuthorizationCredentials | None = Security(bearer),
    session: AsyncSession = Depends(get_session),
):
    if creds is None:
        raise HTTPException(
            status_code=401,
            detail="Missing delete token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    link_id = code_to_id(code)
    if link_id is None:
        raise HTTPException(status_code=404)

    link = await session.get(Link, link_id)
    if link is None:
        raise HTTPException(status_code=404)

    if not verify_token(creds.credentials, link.delete_token_hash):
        raise HTTPException(status_code=403, detail="Invalid delete token")
    key = f"link:{link_id}"


    await session.delete(link)
    await session.commit()
    try:
        await redis.delete(key)
    except RedisError:
        pass
    return Response(status_code=204)
@router.get("/{code}")
async def redirect(code: str, session: AsyncSession = Depends(get_session)):
    link_id = code_to_id(code)
    if not link_id :
        raise HTTPException(status_code=404)
    key = f"link:{link_id}"
    try:
        cached_url = await redis.get(key)
    except RedisError:
        cached_url = None
    if cached_url is not None:
        return RedirectResponse(cached_url, status_code=302)
    link = await session.get(Link, link_id)
    if link is None:
        raise HTTPException(status_code=404)
    if link.expires_at is not None and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410)
    ttl = CACHE_TTL_SECONDS
    if link.expires_at is not None:
        remaining = link.expires_at - datetime.now(timezone.utc) 
        ttl = int(min(ttl,remaining.total_seconds()))
    if ttl>=1:
        try:
            await redis.set(key,link.long_url,ex=ttl)
        except RedisError:
            pass
    return RedirectResponse(link.long_url, status_code=302)

    

    
    

