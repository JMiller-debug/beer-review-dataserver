from typing import Annotated, Literal

from fastapi import APIRouter, Query
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.dependencies import SessionDep
from app.models.beers import (
    Beers,
    BeersBase,
    BeersPublic,
    BeersPublicWithRelations,
    BeersUpdate,
)

# The following import is necessary to rebuild the model
# This was the thought to be the best way to avoid circular import issues
from app.models.breweries import Breweries, BreweriesPublic  # noqa: F401
from app.models.reviews import Reviews, ReviewsPublic  # noqa: F401

from .common import patch_record, BEER_NOT_FOUND, BREWERY_NOT_FOUND, oderby_function

BeersPublicWithRelations.model_rebuild()

router = APIRouter(
    prefix="/beers",
    tags=["beers"],
    responses={404: {"Description": "Not Found"}},
)


@router.post("/", response_model=BeersPublic)
async def create_beer(beer: BeersBase, session: SessionDep) -> BeersPublic:
    stmt = select(Breweries).where(Breweries.name == beer.company)
    result = await session.exec(stmt)
    if not result:
        raise BREWERY_NOT_FOUND
    brewery = result.first()
    beer_data = beer.model_dump()
    beer_data["company_id"] = brewery.id
    beer_db = Beers.model_validate(beer_data)
    session.add(beer_db)
    await session.commit()
    await session.refresh(beer_db)
    return beer_db


@router.patch("/by-id/{beer_id}", response_model=BeersPublic)
async def update_beer_by_id(beer_id: str, beer: BeersUpdate, session: SessionDep):
    beer_db = await session.get(Beers, beer_id)
    return await patch_record(beer_db, beer, session, BEER_NOT_FOUND)


@router.patch("/by-name/{beer_name}", response_model=BeersPublic)
async def update_beer_by_name(beer_name: str, beer: BeersUpdate, session: SessionDep):
    beer_db = (await session.exec(select(Beers).where(Beers.name == beer_name))).first()
    return await patch_record(beer_db, beer, session, BEER_NOT_FOUND)


@router.get("/", response_model=list[BeersPublicWithRelations])
async def read_beers(
    session: SessionDep,
    beer_name: str | None = None,
    beer_id: str | None = None,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    orderby: str | None = None,
    order: Literal["asc", "desc"] = "asc",
):
    stmt = (
        select(Beers)
        .offset(offset)
        .limit(limit)
        .options(selectinload(Beers.brewery))
        .options(selectinload(Beers.reviews))
    )
    if beer_name:
        stmt = stmt.where(Beers.name == beer_name)
    if beer_id:
        stmt = stmt.where(Beers.id == beer_id)
    oderby_function(stmt, Beers, orderby, order)

    beers = await session.exec(stmt)
    return beers.all()


@router.get("/list-beers", response_model=list[str])
async def list_beers(
    session: SessionDep,
    offset: int = 0,
    # limit: Annotated[int, Query(le=100)] = 100,
    orderby: str | None = None,
    order: Literal["asc", "desc"] = "asc",
):
    stmt = select(Beers.name)
    # oderby_function(stmt, Beers, orderby, order)

    beers = (await session.exec(stmt)).all()
    print(beers)
    return beers


@router.get("/by-name/{beer_name}", response_model=BeersPublicWithRelations)
async def read_beer_by_name(beer_name: str, session: SessionDep):
    # Can use first here because the list should only be 1 long as the name is a
    # unique column
    beer = (await session.exec(select(Beers).where(Beers.name == beer_name))).first()
    if not beer:
        raise BEER_NOT_FOUND
    return beer


@router.get("/by-id/{beer_id}", response_model=BeersPublicWithRelations)
async def read_beer_by_id(beer_id: str, session: SessionDep):
    beer = await session.get(Beers, beer_id)
    if not beer:
        raise BEER_NOT_FOUND
    return beer


@router.delete("/by-name/{beer_name}")
async def delete_beer_by_name(beer_name: str, session: SessionDep):
    beer = (await session.exec(select(Beers).where(Beers.name == beer_name))).first()
    if not beer:
        raise BEER_NOT_FOUND
    await session.delete(beer)
    await session.commit()
    return {"Ok": True}


@router.delete("/by-id/{beer_id}")
async def delete_beer_by_id(beer_id: str, session: SessionDep):
    beers = await session.get(Beers, beer_id)
    if not beers:
        raise BEER_NOT_FOUND
    await session.delete(beers)
    await session.commit()
    return {"Ok": True}
