"""Reviews database models."""

import uuid
from copy import deepcopy
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

from .common import DATE_CREATED, LAST_UPDATED

if TYPE_CHECKING:
    from .beers import Beers, BeersPublic


class ReviewsBase(SQLModel):
    """Base object for the Reviews model."""

    username: str = Field(index=True, unique=False)
    score: float = Field(index=True)
    comment: str | None = Field(index=True, default=None)
    beer_name: str = Field(index=True, foreign_key="beers.name")
    __table_args__ = (
        CheckConstraint("score  > 0 AND score <=10", name="check_score_range"),
    )


class Reviews(ReviewsBase, table=True):
    """Reveiws object with columns that get generated."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    last_updated: datetime = deepcopy(LAST_UPDATED)
    date_created: datetime = deepcopy(DATE_CREATED)

    beer: "Beers" = Relationship(
        back_populates="reviews",
        sa_relationship_kwargs={"foreign_keys": "Reviews.beer_id"},
    )
    beer_id: uuid.UUID = Field(foreign_key="beers.id", nullable=False)


class ReviewsPublic(ReviewsBase):
    """Public return object for Reviews."""

    id: uuid.UUID
    last_updated: datetime
    date_created: datetime
    beer_id: uuid.UUID


class ReviewsPublicWithBeers(ReviewsPublic):
    """Public return object for reviews with beers relation."""

    beer: "BeersPublic"


class ReviewsUpdate(SQLModel):
    """Update model for the reviews object."""

    score: float | None = None
    comment: str | None = None
