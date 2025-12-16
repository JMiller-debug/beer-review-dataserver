"""Reviews dataserver routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import selectinload
from sqlmodel import select

from beer_review_dataserver.dependencies import SessionDep  # noqa: TC001

# The following import is necessary to rebuild the model
# This was the thought to be the best way to avoid circular import issues
from beer_review_dataserver.models.beers import (  # noqa: F401
    Beers,
    BeersPublic,
    BeersUpdate,
)
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
from .types import CommonOptions, DeleteResponse, QueryOptions

ReviewsPublicWithBeers.model_rebuild()


class ReviewOptions(BaseModel):
    """Review specific search options."""

    model_config = ConfigDict(extra="forbid")

    username: str | None = None
    identifier: str | None = None
    beer_name: str | None = None
    beer_id: str | None = None


router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
    responses={
        404: {"Description": "Not Found"},
        403: {"Description": "Not Authorised"},
    },
)


@router.post("/")
async def create_review(review: ReviewsBase, session: SessionDep) -> ReviewsPublic:
    """Create a review from user input and insert into the database."""
    # First check to see if the beer exists in the database
    find_beer = (
        select(Beers)
        .where(Beers.name == review.beer_name)
        .options(selectinload(Beers.reviews))  # ty: ignore[invalid-argument-type]
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
        .options(selectinload(Reviews.beer))  # ty: ignore[invalid-argument-type]
    )
    duplicate_review = await session.exec(check_duplicate_reviews)

    if duplicate_review.first() is not None:
        raise HTTPException(
            status_code=403, detail="User is attempting to create multiple reviews"
        )
    if beer.reviews:
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
            beer,
            data=BeersUpdate(score=new_score),
            session=session,
            exception=BEER_NOT_FOUND,
        )
    return ReviewsPublic.model_validate(review_db)


@router.patch("/")
async def update_review(
    session: SessionDep,
    review: ReviewsUpdate,
    identifier: str | None = None,
) -> ReviewsPublic:
    """Patch a review from user input and update the database."""
    review_db = await fetch_single_record(
        session, Reviews, NO_PATCH_ID, options=CommonOptions(identifier=identifier)
    )
    result = await patch_record(review_db, review, session, REVIEW_NOT_FOUND)

    # Find the beer if the user changed their score so we can update the average
    # score when the user changes their mind
    score = getattr(review, "score", None)
    beer_name = getattr(review_db, "beer_name", None)

    if review.score is not None:
        find_beer = (
            select(Beers)
            .where(Beers.name == beer_name)
            .options(selectinload(Beers.reviews))  # ty: ignore[invalid-argument-type]
        )
        result = await session.exec(find_beer)
        beer = result.first()
        reviews = getattr(beer, "reviews", None)
        score = getattr(beer, "score", 0)
        if reviews is not None and score:
            num_reviews = len(reviews)
            avg_score = score

            # calculate the new score by updating the average
            new_score = (avg_score * num_reviews + review.score) / (num_reviews + 1)
            await patch_record(
                beer,
                data=BeersUpdate(score=new_score),
                session=session,
                exception=BEER_NOT_FOUND,
            )
    return ReviewsPublic.model_validate(result)


@router.get("/")
async def read_reviews(
    session: SessionDep,
    options: Annotated[ReviewOptions, Depends()],
    query: Annotated[QueryOptions, Depends()],
) -> list[ReviewsPublicWithBeers]:
    """Return reviews matching query parameters."""
    stmt = (
        select(Reviews)
        .offset(query.offset)
        .limit(query.limit)
        .options(selectinload(Reviews.beer))  # ty: ignore[invalid-argument-type]
    )
    reviews = await session.exec(stmt)
    if options.username:
        stmt = stmt.where(Reviews.username == options.username)
    if options.identifier:
        stmt = stmt.where(Reviews.id == options.identifier)
    if options.beer_name:
        stmt = stmt.where(Reviews.beer_name == options.beer_name)
    if options.beer_id:
        stmt = stmt.where(Reviews.beer_id == options.beer_id)

    stmt = oderby_function(stmt, Reviews, query.orderby, query.order)
    reviews = await session.exec(stmt)
    return reviews.all()  # ty: ignore[invalid-return-type]


@router.delete("/")
async def delete_review(
    session: SessionDep,
    identifier: str | None = None,
) -> DeleteResponse:
    """Delete a review matching the id of the review."""
    # Query for the review by the id as a query parameter as the review itself
    # has no name field
    review = await fetch_single_record(
        session, Reviews, NO_DELETE_ID, options=CommonOptions(identifier=identifier)
    )

    if not review:
        raise REVIEW_NOT_FOUND

    await session.delete(review)
    await session.commit()
    return DeleteResponse(ok=True)
