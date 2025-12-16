"""Common utilities for the routers moudle."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from fastapi.exceptions import HTTPException
from sqlmodel import select

if TYPE_CHECKING:
    from sqlmodel.sql._expression_select_cls import SelectOfScalar

    from beer_review_dataserver.dependencies import SessionDep

    from .beers import Beers, BeersPublicWithRelations, BeersUpdate
    from .breweries import Breweries, BreweriesPublicWithBeers, BreweriesUpdate
    from .reviews import Reviews, ReviewsPublicWithBeers, ReviewsUpdate
    from .types import CommonOptions

    type Models = Beers | Breweries | Reviews
    type ReturnModels = (
        BeersPublicWithRelations | BreweriesPublicWithBeers | ReviewsPublicWithBeers
    )
    type UpdateModels = BeersUpdate | BreweriesUpdate | ReviewsUpdate

REVIEW_NOT_FOUND = HTTPException(status_code=404, detail="Review not found")
BREWERY_NOT_FOUND = HTTPException(status_code=404, detail="Brewery not found")
BEER_NOT_FOUND = HTTPException(status_code=404, detail="Beer not found")
NO_VALID_ORDER = HTTPException(
    status_code=400, detail="Invalid Order: Options include 'asc' and 'desc'"
)
NO_VALID_ORDERBY = HTTPException(
    status_code=400,
    detail="Invalid Orderby: The column you are sorting by does not exist",
)
NO_DELETE_ID = HTTPException(
    status_code=400,
    detail="Invalid Delete: Not enough information to process delete request",
)
NO_PATCH_ID = HTTPException(
    status_code=400,
    detail="Invalid Patch: Not enough information to process patch request",
)
NO_VALID_FILE = HTTPException(
    status_code=400,
    detail="Invalid File: No filename found",
)


async def patch_record(
    db: type[Models],
    data: UpdateModels,
    session: SessionDep,
    exception: HTTPException,
) -> type[ReturnModels]:
    """
    Docstring for patch_record.

    :param db: The record from the database that we are trying to update
    :param data: The data we are trying to update the database with
    :param session: default connection into the database
    :param exception: The exception to raise if we can't find the record we are
        trying to udpate

    Generic function for trying to update a single record in the database
    """
    if not db:
        raise exception
    data_dict = data.model_dump(exclude_unset=True)
    data_dict["last_updated"] = datetime.datetime.now(datetime.UTC)
    db.sqlmodel_update(data_dict)
    session.add(db)
    await session.commit()
    await session.refresh(db)
    return db


# Generic function for ordering/sorting results in ascending/descending order
# based on a give column name
def oderby_function(
    stmt: SelectOfScalar, model: type[Models], orderby: str | None, order: str | None
) -> SelectOfScalar:
    """
    Docstring for oderby_function.

    :param stmt: The select statement that we will be modifying
    :param model: The sql model that we are using to get the column name from
    :param orderby: The column to sort the data by
    :param order: Whether ascending or descending

    Generic function for ordering/sorting results in ascending/descending order
    based on a give column name

    returns the modified stmt
    """
    if orderby is not None:
        # The following is used to get the function attributes from the
        # Model and then query for it
        column = getattr(model, orderby, None)
        if column is None:
            raise NO_VALID_ORDERBY
        if order is not None:
            order_func = getattr(column, order, None)
            if order_func is None:
                raise NO_VALID_ORDER
            stmt = stmt.order_by(order_func())
    return stmt


async def fetch_single_record(
    session: SessionDep,
    model: type[Models],
    exception: HTTPException,
    options: CommonOptions,
) -> Models | None:
    """Fetch a single record from the database by name or id."""
    if options.name:
        data_db = (
            await session.exec(select(model).where(model.options.name == options.name))
        ).first()
    elif options.identifier:
        data_db = await session.get(model, options.identifier)
    else:
        raise exception
    validate_func = getattr(Models, "model_validate", None)
    if validate_func is not None:
        return validate_func(data_db)
    return None
