from typing import Annotated, Literal

from fastapi import APIRouter, Query
from sqlalchemy.orm import selectinload
from sqlmodel import select

from beer_review_dataserver.dependencies import SessionDep
from beer_review_dataserver.models.beers import (
    Beers,
    BeersBase,
    BeersPublic,
    BeersPublicWithBrewery,
    BeersPublicWithRelations,
    BeersUpdate,
)

# The following import is necessary to rebuild the model
# This was the thought to be the best way to avoid circular import issues
from beer_review_dataserver.models.breweries import (  # noqa: F401
    Breweries,
    BreweriesPublic,
)
from beer_review_dataserver.models.reviews import Reviews, ReviewsPublic  # noqa: F401

from .common import (
    BEER_NOT_FOUND,
    BREWERY_NOT_FOUND,
    NO_DELETE_ID,
    NO_PATCH_ID,
    fetch_single_record,
    oderby_function,
    patch_record,
)

BeersPublicWithRelations.model_rebuild()
BeersPublicWithBrewery.model_rebuild()


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


@router.patch("/", response_model=BeersPublic)
async def update_beer(
    session: SessionDep,
    beer: BeersUpdate,
    name: str | None = None,
    identifier: str | None = None,
):
    beer_db = await fetch_single_record(session, Beers, NO_PATCH_ID, name, identifier)
    return await patch_record(beer_db, beer, session, BEER_NOT_FOUND)


@router.get("/", response_model=list[BeersPublicWithRelations])
async def read_beers(
    session: SessionDep,
    name: str | None = None,
    identifier: str | None = None,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    orderby: str | None = None,
    order: Literal["asc", "desc"] = "asc",
):
    # Note selectinload is used to get the associated content from the other
    # tables. This provides us with a company from just the fk of company name
    # and also a list of reviews associated with our beer
    stmt = (
        select(Beers)
        .offset(offset)
        .limit(limit)
        .options(selectinload(Beers.brewery))
        .options(selectinload(Beers.reviews))
    )
    if name:
        stmt = stmt.where(Beers.name == name)
    if identifier:
        stmt = stmt.where(Beers.id == identifier)
    stmt = oderby_function(stmt, Beers, orderby, order)

    beers = await session.exec(stmt)
    return beers.all()


@router.get("/list-beers", response_model=list[str])
async def list_beers(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    orderby: str | None = None,
    order: Literal["asc", "desc"] = "asc",
):
    stmt = select(Beers.name).offset(offset).limit(limit)
    stmt = oderby_function(stmt, Beers, orderby, order)

    beers = (await session.exec(stmt)).all()
    return beers


@router.delete("/")
async def delete_beer(
    session: SessionDep,
    name: str | None = None,
    identifier: str | None = None,
):
    # Query for the beer by whether they pass the name or the id as a query parameter
    beer_db = await fetch_single_record(session, Beers, NO_DELETE_ID, name, identifier)

    if not beer_db:
        raise BEER_NOT_FOUND

    await session.delete(beer_db)
    await session.commit()
    return {"Ok": True}
