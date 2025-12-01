from typing import TYPE_CHECKING

from copy import deepcopy
import uuid
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship
from functools import partial
from sqlalchemy import CheckConstraint

from .common import LAST_UPDATED, DATE_CREATED

if TYPE_CHECKING:
    from .beers import Beers, BeersPublic

now_func = partial(datetime.now, timezone.utc)


class ReviewsBase(SQLModel):
    username: str = Field(index=True, unique=True)
    score: int = Field(index=True)
    comment: str | None = Field(index=True, default=None)
    beer_name: str = Field(index=True, foreign_key="beers.name")
    __table_args__ = (
        CheckConstraint("score  > 0 AND score <=10", name="check_score_range"),
    )


class Reviews(ReviewsBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    last_updated: datetime = deepcopy(LAST_UPDATED)
    date_created: datetime = deepcopy(DATE_CREATED)

    beer: "Beers" = Relationship(
        back_populates="reviews",
        sa_relationship_kwargs={"foreign_keys": "Reviews.beer_id"},
    )
    beer_id: uuid.UUID = Field(foreign_key="beers.id", nullable=False)


class ReviewsPublic(ReviewsBase):
    id: uuid.UUID
    last_updated: datetime
    date_created: datetime
    beer_id: uuid.UUID


class ReviewsUpdate(ReviewsBase):
    score: int | None = None
    comment: str = Field(index=True)


class ReviewsPublicWithBeers(ReviewsPublic):
    beers: "BeersPublic"
