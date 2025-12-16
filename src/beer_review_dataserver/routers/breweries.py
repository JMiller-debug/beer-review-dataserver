"""Breweries dataserver routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import selectinload
from sqlmodel import select

from beer_review_dataserver.dependencies import SessionDep

# The following import is necessary to rebuild the model
# This was the thought to be the best way to avoid circular import issues
from beer_review_dataserver.models.beers import BeersPublic  # noqa: F401
from beer_review_dataserver.models.breweries import (
    Breweries,
    BreweriesBase,
    BreweriesPublic,
    BreweriesPublicWithBeers,
    BreweriesUpdate,
)

from .common import (
    BREWERY_NOT_FOUND,
    NO_DELETE_ID,
    NO_PATCH_ID,
    fetch_single_record,
    oderby_function,
    patch_record,
)
from .types import CommonOptions, DeleteResponse, QueryOptions

BreweriesPublicWithBeers.model_rebuild()

router = APIRouter(
    prefix="/breweries",
    tags=["breweries"],
    responses={404: {"Description": "Not Found"}},
)


@router.post("/")
async def create_brewery(
    brewery: BreweriesBase, session: SessionDep
) -> BreweriesPublic:
    """Create a brewery from user input and insert into the database."""
    brewery_db = Breweries.model_validate(brewery)
    session.add(brewery_db)
    await session.commit()
    await session.refresh(brewery_db)
    return BreweriesPublic.model_validate(brewery_db)


@router.patch("/")
async def update_brewery(
    session: SessionDep,
    brewery: BreweriesUpdate,
    options: Annotated[CommonOptions, Depends()],
) -> BreweriesPublic:
    """Patch a brewery from user input and update teh database."""
    breweries_db = await fetch_single_record(session, Breweries, NO_PATCH_ID, options)

    return await patch_record(breweries_db, brewery, session, BREWERY_NOT_FOUND)


@router.get("/")
async def read_breweries(
    session: SessionDep,
    options: Annotated[CommonOptions, Depends()],
    query: Annotated[QueryOptions, Depends()],
) -> list[BreweriesPublicWithBeers]:
    """Return breweries matching query parameters."""
    # Note selectinload is used to get the associated content from the other
    # tables. This provides us with a list of associated beers based on the fk
    # relationship
    stmt = (
        select(Breweries)
        .offset(query.offset)
        .limit(query.limit)
        .options(selectinload(Breweries.beers))  # ty: ignore[invalid-argument-type]
    )
    if options.name:
        stmt = stmt.where(Breweries.name == options.name)
    if options.identifier:
        stmt = stmt.where(Breweries.id == options.identifier)

    stmt = oderby_function(stmt, Breweries, query.orderby, query.order)

    breweries = await session.exec(stmt)
    return breweries.all()  # ty: ignore[invalid-return-type]


@router.delete("/")
async def delete_brewery(
    session: SessionDep,
    options: Annotated[CommonOptions, Query()],
) -> DeleteResponse:
    """Delete a brewery matching query parameters."""
    # Query for the brewery by whether they pass the name or the id as a query parameter
    brewery_db = await fetch_single_record(session, Breweries, NO_DELETE_ID, options)

    if not brewery_db:
        raise BREWERY_NOT_FOUND

    await session.delete(brewery_db)
    await session.commit()

    return DeleteResponse(ok=True)
