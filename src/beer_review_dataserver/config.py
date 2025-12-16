"""Beer Dataserver config."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Enviornemnt settings class."""

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000
    log_level: str = "info"
    postgres_uri: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/beer_review"
    )
    image_dir: str = ""


@lru_cache
def get_settings() -> Settings:
    """
    Return environment variables.

    Cached so it saves the result the first time
    its called.
    """
    return Settings()
