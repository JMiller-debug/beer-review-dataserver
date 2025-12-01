from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    postgres_uri: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/beer_review"
    )


@lru_cache
def get_settings():
    return Settings()
