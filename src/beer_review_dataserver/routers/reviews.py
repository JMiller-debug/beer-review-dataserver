from typing import Annotated, Literal

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select

from beer_review_dataserver.dependencies import SessionDep

# The following import is necessary to rebuild the model
# This was the thought to be the best way to avoid circular import issues
from beer_review_dataserver.models.beers import Beers, BeersPublic  # noqa: F401
from beer_review_dataserver.models.reviews import (
    Reviews,
    ReviewsBase,
    ReviewsPublic,
    ReviewsPublicWithBeers,
    ReviewsUpdate,
)

from .common import (
    BEER_NOT_FOUND,
    NO_DELETE_ID,
    NO_PATCH_ID,
    REVIEW_NOT_FOUND,
    fetch_single_record,
    oderby_function,
    patch_record,
)

ReviewsPublicWithBeers.model_rebuild()

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
    responses={
        404: {"Description": "Not Found"},
        403: {"Description": "Not Authorised"},
    },
)


@router.post("/", response_model=ReviewsPublic)
async def create_review(review: ReviewsBase, session: SessionDep):
    # First check to see if the beer exists in the database
    find_beer = (
        select(Beers)
        .where(Beers.name == review.beer_name)
        .options(selectinload(Beers.reviews))
    )
    result = await session.exec(find_beer)
    beer = result.first()
    # Raise a BEER NOT FOUND exception
    if not beer:
        raise BEER_NOT_FOUND

    # Next check to see if the user as already reviewed this beer and prevent
    # them from creating duplicate reviews
    check_duplicate_reviews = (
        select(Reviews)
        .where(
            Reviews.username == review.username, Reviews.beer_name == review.beer_name
        )
        .options(selectinload(Reviews.beer))
    )
    duplicate_review = await session.exec(check_duplicate_reviews)

    if duplicate_review.first() is not None:
        raise HTTPException(
            status_code=403, detail="User is attempting to create multiple reviews"
        )
    num_reviews = len(beer.reviews)
    avg_score = beer.score

    # calculate the new score by updating the average
    new_score = (avg_score * num_reviews + review.score) / (num_reviews + 1)
    review_data = review.model_dump()
    review_data["beer_id"] = beer.id
    review_db = Reviews.model_validate(review_data)
    session.add(review_db)
    await session.commit()
    await session.refresh(review_db)

    await patch_record(
        beer, data=Beers(score=new_score), session=session, exception=BEER_NOT_FOUND
    )
    return review_db


@router.patch("/", response_model=ReviewsPublic)
async def update_review(
    session: SessionDep,
    review: ReviewsUpdate,
    identifier: str | None = None,
):
    review_db = await fetch_single_record(
        session, Reviews, NO_PATCH_ID, identifier=identifier
    )
    result = await patch_record(review_db, review, session, REVIEW_NOT_FOUND)

    # Find the beer if the user changed their score so we can update the average
    # score when the user changes their mind
    if review.score is not None:
        find_beer = (
            select(Beers)
            .where(Beers.name == review.beer_name)
            .options(selectinload(Beers.reviews))
        )
        result = await session.exec(find_beer)
        beer = result.first()
        num_reviews = len(beer.reviews)
        avg_score = beer.score

        # calculate the new score by updating the average
        new_score = (avg_score * num_reviews + review.score) / (num_reviews + 1)
        await patch_record(
            beer, data=Beers(score=new_score), session=session, exception=BEER_NOT_FOUND
        )
    return result


@router.get("/", response_model=list[ReviewsPublicWithBeers])
async def read_reviews(
    session: SessionDep,
    username: str | None = None,
    identifier: str | None = None,
    beer_name: str | None = None,
    beer_id: str | None = None,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    orderby: str | None = None,
    order: Literal["asc", "desc"] = "asc",
):
    stmt = (
        select(Reviews).offset(offset).limit(limit).options(selectinload(Reviews.beer))
    )
    reviews = await session.exec(stmt)
    if username:
        stmt = stmt.where(Reviews.username == username)
    if identifier:
        stmt = stmt.where(Reviews.id == identifier)
    if beer_name:
        stmt = stmt.where(Reviews.beer_name == beer_name)
    if beer_id:
        stmt = stmt.where(Reviews.beer_id == beer_id)

    stmt = oderby_function(stmt, Reviews, orderby, order)
    reviews = await session.exec(stmt)
    return reviews.all()


@router.delete("/")
async def delete_review(
    session: SessionDep,
    identifier: str | None = None,
):
    # Query for the review by the id as a query parameter as the review itself has no name field
    review = await fetch_single_record(
        session, Reviews, NO_DELETE_ID, identifier=identifier
    )

    if not review:
        raise REVIEW_NOT_FOUND

    await session.delete(review)
    await session.commit()
    return {"Ok": True}
