from typing import Annotated, Literal

from fastapi import APIRouter, Query
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

BreweriesPublicWithBeers.model_rebuild()

router = APIRouter(
    prefix="/breweries",
    tags=["breweries"],
    responses={404: {"Description": "Not Found"}},
)


@router.patch("/", response_model=BreweriesPublic)
async def update_brewery(
    session: SessionDep,
    brewery: BreweriesUpdate,
    name: str | None = None,
    identifier: str | None = None,
):
    breweries_db = await fetch_single_record(
        session, Breweries, NO_PATCH_ID, name, identifier
    )

    return await patch_record(breweries_db, brewery, session, BREWERY_NOT_FOUND)


@router.post("/", response_model=BreweriesPublic)
async def create_brewery(brewery: BreweriesBase, session: SessionDep):
    brewery_db = Breweries.model_validate(brewery)
    session.add(brewery_db)
    await session.commit()
    await session.refresh(brewery_db)
    return brewery_db


@router.get("/", response_model=list[BreweriesPublicWithBeers])
async def read_breweries(
    session: SessionDep,
    name: str | None = None,
    identifier: str | None = None,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    orderby: str | None = None,
    order: Literal["asc", "desc"] = "asc",
):
    # Note selectinload is used to get the associated content from the other
    # tables. This provides us with a list of associated beers based on the fk
    # relationship
    stmt = (
        select(Breweries)
        .offset(offset)
        .limit(limit)
        .options(selectinload(Breweries.beers))
    )
    if name:
        stmt = stmt.where(Breweries.name == name)
    if identifier:
        stmt = stmt.where(Breweries.id == identifier)

    stmt = oderby_function(stmt, Breweries, orderby, order)

    breweries = await session.exec(stmt)
    return breweries.all()


@router.delete("/")
async def delete_brewery(
    session: SessionDep,
    name: str | None = None,
    identifier: str | None = None,
):
    # Query for the brewery by whether they pass the name or the id as a query parameter
    brewery_db = await fetch_single_record(
        session, Breweries, NO_DELETE_ID, name, identifier
    )

    if not brewery_db:
        raise BREWERY_NOT_FOUND

    await session.delete(brewery_db)
    await session.commit()
    return {"Ok": True}
