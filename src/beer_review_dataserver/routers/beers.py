"""Beers dataserver routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import selectinload
from sqlmodel import select

from beer_review_dataserver.dependencies import SessionDep  # noqa: TC001
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
from .types import CommonOptions, DeleteResponse, QueryOptions

BeersPublicWithRelations.model_rebuild()
BeersPublicWithBrewery.model_rebuild()


router = APIRouter(
    prefix="/beers",
    tags=["beers"],
    responses={404: {"Description": "Not Found"}},
)


@router.post("/")
async def create_beer(beer: BeersBase, session: SessionDep) -> BeersPublic:
    """Create a beer from user input and insert into the database."""
    stmt = select(Breweries).where(Breweries.name == beer.company)
    result = await session.exec(stmt)
    if not result:
        raise BREWERY_NOT_FOUND
    brewery = result.first()
    beer_data = beer.model_dump()
    brewery_id = getattr(brewery, "id", None)
    if brewery_id is None:
        raise BREWERY_NOT_FOUND
    beer_data["company_id"] = brewery_id
    beer_db = Beers.model_validate(beer_data)
    session.add(beer_db)
    await session.commit()
    await session.refresh(beer_db)
    return BeersPublic.model_validate(beer_db)


@router.patch("/")
async def update_beer(
    session: SessionDep,
    beer: BeersUpdate,
    options: Annotated[CommonOptions, Depends()],
) -> BeersPublic:
    """Patch a beer from user input and update the database."""
    beer_db = await fetch_single_record(session, Beers, NO_PATCH_ID, options)
    return await patch_record(beer_db, beer, session, BEER_NOT_FOUND)


@router.get(
    "/",
)
async def read_beers(
    session: SessionDep,
    options: Annotated[CommonOptions, Depends()],
    query: Annotated[QueryOptions, Depends()],
) -> list[BeersPublicWithRelations]:
    """Return beers matching query parameters."""
    # Note selectinload is used to get the associated content from the other
    # tables. This provides us with a company from just the fk of company name
    # and also a list of reviews associated with our beer
    stmt = (
        select(Beers)
        .offset(query.offset)
        .limit(query.limit)
        .options(selectinload(Beers.brewery))  # ty: ignore[invalid-argument-type]
        .options(selectinload(Beers.reviews))  # ty: ignore[invalid-argument-type]
    )
    if options.name:
        stmt = stmt.where(Beers.name == options.name)
    if options.identifier:
        stmt = stmt.where(Beers.id == options.identifier)
    stmt = oderby_function(stmt, Beers, query.orderby, query.order)

    beers = await session.exec(stmt)
    return beers.all()  # ty: ignore[invalid-return-type]


@router.get("/list-beers")
async def list_beers(
    session: SessionDep,
    query: Annotated[QueryOptions, Query()],
) -> list[str]:
    """Return a list of beer names from the database."""
    stmt = select(Beers.name).offset(query.offset).limit(query.limit)
    stmt = oderby_function(stmt, Beers, query.orderby, query.order)

    return (await session.exec(stmt)).all()  # ty: ignore[invalid-return-type]


@router.delete("/")
async def delete_beer(
    session: SessionDep,
    options: Annotated[CommonOptions, Query()],
) -> DeleteResponse:
    """Delete a beer from the database."""
    # Query for the beer by whether they pass the name or the id as a query parameter
    beer_db = await fetch_single_record(session, Beers, NO_DELETE_ID, options)

    if not beer_db:
        raise BEER_NOT_FOUND

    await session.delete(beer_db)
    await session.commit()
    return DeleteResponse(ok=True)
