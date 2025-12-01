from typing import Annotated, Literal

from fastapi import APIRouter, Query
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.dependencies import SessionDep

# The following import is necessary to rebuild the model
# This was the thought to be the best way to avoid circular import issues
from app.models.beers import Beers, BeersPublic  # noqa: F401
from app.models.reviews import (
    Reviews,
    ReviewsBase,
    ReviewsPublic,
    ReviewsPublicWithBeers,
    ReviewsUpdate,
)
from fastapi.exceptions import HTTPException
from .common import BEER_NOT_FOUND, REVIEW_NOT_FOUND, oderby_function, patch_record

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
async def create_review(review: ReviewsBase, session: SessionDep) -> ReviewsPublic:
    find_beer = select(Beers).where(Beers.name == review.beer_name)
    result = await session.exec(find_beer)
    beer = result.first()
    if not beer:
        raise BEER_NOT_FOUND
    check_duplicate_reviews = select(Reviews).where(Reviews.username == review.username)
    result = await session.exec(check_duplicate_reviews)
    duplicate_review = result.first()
    if duplicate_review:
        raise HTTPException(
            status_code=403, detail="User is attempting to create multiple reviews"
        )
    review_data = review.model_dump()
    review_data["beer_id"] = beer.id
    review_db = Reviews.model_validate(review_data)
    session.add(review_db)
    await session.commit()
    await session.refresh(review_db)
    return review_db


@router.patch("/by-id/{review_id}", response_model=ReviewsPublic)
async def update_review_by_id(
    review_id: str, review: ReviewsUpdate, session: SessionDep
):
    review_db = await session.get(Reviews, review_id)
    return await patch_record(review_db, review, session, REVIEW_NOT_FOUND)


@router.patch("/by-name/{review_name}", response_model=ReviewsPublic)
async def update_review_by_name(
    review_name: str, review: ReviewsUpdate, session: SessionDep
):
    review_db = (
        await session.exec(select(Reviews).where(Reviews.name == review_name))
    ).first()
    return await patch_record(review_db, review, session, REVIEW_NOT_FOUND)


@router.get("/", response_model=list[ReviewsPublicWithBeers])
async def read_reviews(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    orderby: str | None = None,
    order: Literal["asc", "desc"] = "asc",
):
    stmt = (
        select(Reviews).offset(offset).limit(limit).options(selectinload(Reviews.beer))
    )
    oderby_function(stmt, Reviews, orderby, order)
    reviews = await session.exec(stmt)
    return reviews.all()


@router.get("/by-beer-name/{beer_name}", response_model=list[ReviewsPublicWithBeers])
async def read_review_by_beer_name(beer_name: str, session: SessionDep):
    # Can use first here because the list should only be 1 long as the name is a
    # unique column
    review = await session.exec(select(Reviews).where(Reviews.beer_name == beer_name))
    if not review:
        raise REVIEW_NOT_FOUND
    return review.all()


@router.get("/by-beer-id/{beer_id}", response_model=list[ReviewsPublicWithBeers])
async def read_review_by_beer_id(beer_id: str, session: SessionDep):
    # Can use first here because the list should only be 1 long as the name is a
    # unique column
    review = await session.exec(select(Reviews).where(Reviews.beer_id == beer_id))
    if not review:
        raise REVIEW_NOT_FOUND
    return review.all()


@router.get("/by-id/{review_id}", response_model=ReviewsPublicWithBeers)
async def read_review_by_review_id(review_id: str, session: SessionDep):
    review = await session.get(Reviews, review_id)
    if not review:
        raise REVIEW_NOT_FOUND
    return review


@router.delete("/by-name/{review_name}")
async def delete_review_by_name(review_name: str, session: SessionDep):
    review = (
        await session.exec(select(Reviews).where(Reviews.name == review_name))
    ).first()
    if not review:
        raise REVIEW_NOT_FOUND
    await session.delete(review)
    await session.commit()
    return {"Ok": True}


@router.delete("/by-id/{review_id}")
async def delete_review_by_id(review_id: str, session: SessionDep):
    reviews = await session.get(Reviews, review_id)
    if not reviews:
        raise REVIEW_NOT_FOUND
    await session.delete(reviews)
    await session.commit()
    return {"Ok": True}
