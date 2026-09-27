FROM python:3.12-slim
WORKDIR /srv

COPY shortener/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ratelimit/ ./ratelimit/
COPY shortener/app/ ./app/

# --proxy-headers: read the real client IP from X-Forwarded-For.
# --forwarded-allow-ips "*": trust whoever sends that header. Safe on
# Render/Railway only because their proxy is the only thing that can reach
# the app. Locally (no proxy) anyone can spoof it — fine for dev only.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
