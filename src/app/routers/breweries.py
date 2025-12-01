from typing import Annotated, Literal

from fastapi import APIRouter, Query
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.dependencies import SessionDep

# The following import is necessary to rebuild the model
# This was the thought to be the best way to avoid circular import issues
from app.models.beers import BeersPublic  # noqa: F401
from app.models.breweries import (
    Breweries,
    BreweriesBase,
    BreweriesPublic,
    BreweriesPublicWithBeers,
    BreweriesUpdate,
)

from .common import patch_record, BREWERY_NOT_FOUND, oderby_function

BreweriesPublicWithBeers.model_rebuild()

router = APIRouter(
    prefix="/breweries",
    tags=["breweries"],
    responses={404: {"Description": "Not Found"}},
)


@router.post("/", response_model=BreweriesPublic)
async def create_brewery(brewery: BreweriesBase, session: SessionDep):
    brewery_db = Breweries.model_validate(brewery)
    session.add(brewery_db)
    await session.commit()
    await session.refresh(brewery_db)
    return brewery_db


@router.patch("/by-id/{brewery_id}", response_model=BreweriesPublic)
async def update_brewery_by_id(
    brewery_id: str, brewery: BreweriesUpdate, session: SessionDep
):
    brewery_db = await session.get(Breweries, brewery_id)
    return await patch_record(
        brewery_db,
        brewery,
        session,
        BREWERY_NOT_FOUND,
    )


@router.patch("/by-name/{brewery_name}", response_model=BreweriesPublic)
async def update_brewery_by_name(
    brewery_name: str, brewery: BreweriesUpdate, session: SessionDep
):
    brewery_db = (
        await session.exec(select(Breweries).where(Breweries.name == brewery_name))
    ).first()
    return await patch_record(
        brewery_db,
        brewery,
        session,
        BREWERY_NOT_FOUND,
    )


@router.get("/", response_model=list[BreweriesPublicWithBeers])
async def read_breweries(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    orderby: str | None = None,
    order: Literal["asc", "desc"] = "asc",
):
    stmt = (
        select(Breweries)
        .offset(offset)
        .limit(limit)
        .options(selectinload(Breweries.beers))
    )

    oderby_function(stmt, Breweries, orderby, order)

    breweries = await session.exec(stmt)
    return breweries.all()


@router.get("/by-name/{brewery_name}", response_model=BreweriesPublicWithBeers)
async def read_brewery_by_name(brewery_name: str, session: SessionDep):
    # Can use first here because the list should only be 1 long as the name is a
    # unique column
    brewery = (
        await session.exec(select(Breweries).where(Breweries.name == brewery_name))
    ).first()
    if not brewery:
        raise BREWERY_NOT_FOUND
    return brewery


@router.get("/by-id/{brewery_id}", response_model=BreweriesPublicWithBeers)
async def read_brewery_by_id(brewery_id: str, session: SessionDep):
    brewery = await session.get(Breweries, brewery_id)
    if not brewery:
        raise BREWERY_NOT_FOUND
    return brewery


@router.delete("/by-name/{brewery_name}")
async def delete_brewery_by_name(brewery_name: str, session: SessionDep):
    brewery = (
        await session.exec(select(Breweries).where(Breweries.name == brewery_name))
    ).first()
    if not brewery:
        raise BREWERY_NOT_FOUND
    await session.delete(brewery)
    await session.commit()
    return {"Ok": True}


@router.delete("/by-id/{brewery_id}")
async def delete_brewery_by_id(brewery_id: str, session: SessionDep):
    breweries = await session.get(Breweries, brewery_id)
    if not breweries:
        raise BREWERY_NOT_FOUND
    await session.delete(breweries)
    await session.commit()
    return {"Ok": True}
