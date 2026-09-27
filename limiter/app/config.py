from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str


settings = Settings()
