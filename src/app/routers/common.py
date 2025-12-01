import datetime

from fastapi.exceptions import HTTPException

REVIEW_NOT_FOUND = HTTPException(status_code=404, detail="Review not found")
BREWERY_NOT_FOUND = HTTPException(status_code=404, detail="Brewery not found")
BEER_NOT_FOUND = HTTPException(status_code=404, detail="Beer not found")


async def patch_record(db, data, session, exception):
    if not db:
        raise exception
    data = data.model_dump(exclude_unset=True)
    data["last_updated"] = datetime.datetime.now(datetime.timezone.utc)
    db.sqlmodel_update(data)
    session.add(db)
    await session.commit()
    await session.refresh(db)
    return db


def oderby_function(stmt, model, orderby, order):
    if orderby is not None:
        # The following is used to get the function attributes from the
        # Model and then query for it
        column = getattr(model, orderby)
        order = getattr(column, order)
        stmt = stmt.order_by(order())
