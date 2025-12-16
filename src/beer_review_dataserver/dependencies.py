"""FastAPI Dataserver dependencies."""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from beer_review_dataserver.models.beers import Beers
from beer_review_dataserver.models.breweries import Breweries
from beer_review_dataserver.models.reviews import Reviews

from .config import get_settings

settings = get_settings()

engine = create_async_engine(settings.postgres_uri)

async_engine = create_async_engine(settings.postgres_uri, echo=True, future=True)

async_session = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def create_db_and_tables() -> None:
    """Create the tables in the database if they don't already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Beers.metadata.create_all)
        await conn.run_sync(Breweries.metadata.create_all)
        await conn.run_sync(Reviews.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Return the session into the database when we access certain endpoints."""
    async with async_session() as session:
        yield session


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create the db and tables if you dont use alembic."""
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
    yield


SessionDep = Annotated[AsyncSession, Depends(get_session)]
