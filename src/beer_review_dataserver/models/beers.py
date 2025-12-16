"""Beers Database models."""

# ruff: noqa:  UP045
import uuid
from copy import deepcopy
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .common import DATE_CREATED, LAST_UPDATED

# Required for type checking when developing but doesn't break
# when running due to circular imports.
if TYPE_CHECKING:
    from .breweries import Breweries, BreweriesPublic
    from .reviews import Reviews, ReviewsPublic


class BeersBase(SQLModel):
    """Base object for the beers model."""

    name: str = Field(index=True, unique=True)
    company: str = Field(index=True, foreign_key="breweries.name")


class Beers(BeersBase, table=True):
    """Beers object with columns that get generated."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    last_updated: datetime = deepcopy(LAST_UPDATED)
    date_created: datetime = deepcopy(DATE_CREATED)
    score: float = Field(default=0, index=True)

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
    """Public return object for beers."""

    id: uuid.UUID
    score: float
    last_updated: datetime
    date_created: datetime
    company_id: uuid.UUID


class BeersPublicWithBrewery(BeersPublic):
    """Public return object for beers with brewery relation."""

    brewery: "BreweriesPublic"


class BeersPublicWithRelations(BeersPublic):
    """Public return object for beers with brewery and review relation."""

    brewery: "BreweriesPublic"
    reviews: Optional[list["ReviewsPublic"]]


class BeersUpdate(SQLModel):
    """Update model for the beers object."""

    name: str | None = None
    company: str | None = None
