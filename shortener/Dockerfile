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
