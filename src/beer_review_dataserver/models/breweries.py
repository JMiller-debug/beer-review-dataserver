"""Breweries database models."""

# ruff: noqa: UP045
import uuid
from copy import deepcopy
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .common import DATE_CREATED, LAST_UPDATED

if TYPE_CHECKING:
    from .beers import Beers, BeersPublic


class BreweriesBase(SQLModel):
    """Base object for the breweries model."""

    name: str = Field(index=True, unique=True)


class Breweries(BreweriesBase, table=True):
    """Breweries object with columns that get generated."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    last_updated: datetime = deepcopy(LAST_UPDATED)
    date_created: datetime = deepcopy(DATE_CREATED)
    beers: Optional[list["Beers"]] = Relationship(
        back_populates="brewery",
        sa_relationship_kwargs={"foreign_keys": "Beers.company_id"},
    )


class BreweriesPublic(BreweriesBase):
    """Public return object for breweries model."""

    id: uuid.UUID
    last_updated: datetime
    date_created: datetime


class BreweriesUpdate(SQLModel):
    """Update model for the breweries object."""

    name: str | None = None


class BreweriesPublicWithBeers(BreweriesPublic):
    """Public Retrun for breweries object with Beers Relationship."""

    beers: Optional[list["BeersPublic"]] = []
