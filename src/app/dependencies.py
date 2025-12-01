from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.beers import Beers

postgres_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/beer_review"
engine = create_async_engine(postgres_url)

async_engine = create_async_engine(postgres_url, echo=True, future=True)

async_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Beers.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
    yield


SessionDep = Annotated[Session, Depends(get_session)]
