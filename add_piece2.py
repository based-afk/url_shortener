#!/usr/bin/env python3
"""
Piece 2: adds the SQLAlchemy model and Alembic migration setup.

Run from INSIDE the project folder (the one containing docker-compose.yml):
    python add_piece2.py

New files are skipped if they already exist.
shortener/Dockerfile is REPLACED (so migrations run on startup) — the old
version is saved as shortener/Dockerfile.bak.
"""

import shutil
from pathlib import Path

FILES: dict[str, str] = {}

# ------------------------------------------------------------------- model

FILES["shortener/app/models.py"] = r'''
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
'''

# ----------------------------------------------------------------- alembic

FILES["shortener/alembic.ini"] = r"""
[alembic]
script_location = alembic
prepend_sys_path = .
# sqlalchemy.url is deliberately NOT set here. env.py reads DATABASE_URL
# from the environment, so credentials never end up in a committed file.

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

FILES["shortener/alembic/env.py"] = r'''
"""
Alembic environment, async version (we use asyncpg, not a sync driver).
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic compares this against the live DB when autogenerating migrations.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (alembic upgrade --sql)."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
'''

# Template Alembic uses when you later run: alembic revision --autogenerate
FILES["shortener/alembic/script.py.mako"] = r'''
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''

FILES["shortener/alembic/versions/0001_create_links.py"] = r'''
"""create links table

Revision ID: 0001
Revises:
Create Date: 2026-09-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "links",
        sa.Column(
            "id", sa.BigInteger(), sa.Identity(always=True), primary_key=True
        ),
        sa.Column("long_url", sa.String(2048), nullable=False),
        sa.Column("delete_token_hash", sa.CHAR(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("links")
'''

# -------------------------------------------- Dockerfile (replaced, see top)

DOCKERFILE = r"""
FROM python:3.12-slim
WORKDIR /srv

COPY shortener/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ratelimit/ ./ratelimit/
COPY shortener/alembic.ini .
COPY shortener/alembic/ ./alembic/
COPY shortener/app/ ./app/

# 1. Apply any pending migrations.  2. Start the server.
# "exec" makes uvicorn the main process so it receives Docker's stop signal.
# --proxy-headers / --forwarded-allow-ips: see Piece 1 notes. '*' is quoted
# so the shell doesn't expand it into a list of filenames.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*'"]
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # LF line endings even on Windows — CRLF breaks things inside Linux containers.
    path.write_text(content.lstrip("\n"), encoding="utf-8", newline="\n")


def main() -> None:
    root = Path.cwd()
    if not (root / "docker-compose.yml").exists():
        raise SystemExit(
            "docker-compose.yml not found. Run this from inside the project folder."
        )

    for rel_path, content in FILES.items():
        path = root / rel_path
        if path.exists():
            print(f"  skip    {rel_path} (already exists)")
            continue
        write(path, content)
        print(f"  create  {rel_path}")

    dockerfile = root / "shortener" / "Dockerfile"
    if dockerfile.exists():
        shutil.copy(dockerfile, dockerfile.with_suffix(".bak"))
        print("  backup  shortener/Dockerfile -> shortener/Dockerfile.bak")
    write(dockerfile, DOCKERFILE)
    print("  replace shortener/Dockerfile")

    print(
        "\nNext:\n"
        "  docker compose up --build\n"
        '  docker compose exec postgres psql -U shortener -d shortener -c "\\d links"'
    )


if __name__ == "__main__":
    main()