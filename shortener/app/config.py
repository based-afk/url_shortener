from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    limiter_url: str
    limiter_timeout_seconds: float = 0.2
    base_url: str


settings = Settings()
