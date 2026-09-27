from datetime import datetime

from sqlalchemy import CHAR, BigInteger, DateTime, Identity, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Link(Base):
    __tablename__ = "links"

    # GENERATED ALWAYS AS IDENTITY: Postgres assigns the id; inserting one
    # manually is an error. The public short code is derived from this id
    # (scramble -> base62), so no short_code column is stored.
    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )

    # 2048 = common practical URL limit. Also enforced in Pydantic so
    # oversized input is rejected before reaching the database.
    long_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # SHA-256 hex digest of the delete token. Always exactly 64 chars.
    # The raw token is returned to the creator once and never stored.
    delete_token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)

    # TIMESTAMPTZ: stored as an absolute moment, so IST (local) and
    # UTC (Render) servers agree on when a link expires.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # NULL = never expires.
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
