import datetime

from fastapi.exceptions import HTTPException
from sqlmodel import select

from beer_review_dataserver.dependencies import SessionDep

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


async def patch_record(db, data, session, exception):
    """
    Docstring for patch_record

    :param db: The record from the database that we are trying to update
    :param data: The data we are trying to update the database with
    :param session: default connection into the database
    :param exception: The exception to raise if we can't find the record we are trying to udpate

    Generic function for trying to update a single record in the database
    """
    if not db:
        raise exception
    data = data.model_dump(exclude_unset=True)
    data["last_updated"] = datetime.datetime.now(datetime.timezone.utc)
    db.sqlmodel_update(data)
    session.add(db)
    await session.commit()
    await session.refresh(db)
    return db


# Generic function for ordering/sorting results in ascending/descending order
# based on a give column name
def oderby_function(stmt, model, orderby, order):
    """
    Docstring for oderby_function

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
        order = getattr(column, order, None)
        if order is None:
            raise NO_VALID_ORDER
        stmt = stmt.order_by(order())
    return stmt


async def fetch_single_record(
    session: SessionDep,
    model,
    exception: HTTPException,
    name: str | None = None,
    identifier: str | None = None,
):
    if name:
        data_db = (await session.exec(select(model).where(model.name == name))).first()
    elif identifier:
        data_db = await session.get(model, identifier)
    else:
        raise exception
    return data_db
