import uuid
from copy import deepcopy
from datetime import datetime, timezone
from functools import partial
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

from .common import DATE_CREATED, LAST_UPDATED

if TYPE_CHECKING:
    from .breweries import Breweries, BreweriesPublic
    from .reviews import Reviews, ReviewsPublic


now_func = partial(datetime.now, timezone.utc)


class BeersBase(SQLModel):
    name: str = Field(index=True, unique=True)
    score: int | None = Field(default=None, index=True)
    company: str = Field(index=True, foreign_key="breweries.name")


class Beers(BeersBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    last_updated: datetime = deepcopy(LAST_UPDATED)
    date_created: datetime = deepcopy(DATE_CREATED)

    # A good example of resolving foreign key ambiguity
    # https://github.com/fastapi/sqlmodel/discussions/1038
    #
    # Essentially, you link to the foreign_key relationship from the table that
    # has the relationship So Beers has the company_id relationship for
    # breweries and reviews has the beer_id fk for reviews.

    brewery: "Breweries" = Relationship(
        back_populates="beers",
        sa_relationship_kwargs={"foreign_keys": "Beers.company_id"},
    )
    reviews: Optional[list["Reviews"]] = Relationship(
        back_populates="beer",
        sa_relationship_kwargs={"foreign_keys": "Reviews.beer_id"},
    )
    company_id: uuid.UUID = Field(foreign_key="breweries.id", nullable=False)


class BeersPublic(BeersBase):
    id: uuid.UUID
    last_updated: datetime
    date_created: datetime
    company_id: uuid.UUID


class BeersPublicWithBrewery(BeersPublic):
    brewery: "BreweriesPublic"


class BeersPublicWithRelations(BeersPublic):
    brewery: "BreweriesPublic"
    reviews: Optional[list["ReviewsPublic"]]


class BeersUpdate(BeersBase):
    name: str | None = None
    company: str | None = None
    score: int | None = None
