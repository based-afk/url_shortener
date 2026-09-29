from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.config import settings

MAX_URL_LENGTH = 2048          # matches VARCHAR(2048) in the links table
MIN_EXPIRY_SECONDS = 60        # 1 minute
MAX_EXPIRY_SECONDS = 31536000  # 365 days

_OWN_HOST = urlparse(settings.base_url).hostname


class ShortenRequest(BaseModel):
    # HttpUrl rejects anything that isn't a well-formed http(s) URL
    # before the handler even runs -> automatic 422 response.
    long_url: HttpUrl

    # Omit for a link that never expires.
    expires_in_seconds: int | None = Field(
        default=None, ge=MIN_EXPIRY_SECONDS, le=MAX_EXPIRY_SECONDS
    )

    @field_validator("long_url")
    @classmethod
    def check_url(cls, v: HttpUrl) -> HttpUrl:
        if len(str(v)) > MAX_URL_LENGTH:
            raise ValueError(f"URL must be at most {MAX_URL_LENGTH} characters")
        # Stop short links pointing at our own short links (redirect loops).
        if v.host == _OWN_HOST:
            raise ValueError("Cannot shorten a URL on this service's own domain")
        return v


class ShortenResponse(BaseModel):
    code: str
    short_url: str
    # Returned exactly once. Only its hash is stored, so it can never be
    # shown again — the client must save it to be able to delete the link.
    delete_token: str
    expires_at: datetime | None
