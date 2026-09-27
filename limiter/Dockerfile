FROM python:3.12-slim
WORKDIR /srv

COPY limiter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ratelimit/ ./ratelimit/
COPY limiter/app/ ./app/

# No --proxy-headers: the limiter never looks at who is calling it.
# The client identity always arrives in the request body as client_id.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
