import uuid
from copy import deepcopy
from datetime import datetime, timezone
from functools import partial
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from .common import DATE_CREATED, LAST_UPDATED

now_func = partial(datetime.now, timezone.utc)

if TYPE_CHECKING:
    from .beers import Beers, BeersPublic  # noqa: F401


class BreweriesBase(SQLModel):
    name: str = Field(index=True, unique=True)


class Breweries(BreweriesBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    last_updated: datetime = deepcopy(LAST_UPDATED)
    date_created: datetime = deepcopy(DATE_CREATED)
    beers: Optional[list["Beers"]] = Relationship(
        back_populates="brewery",
        sa_relationship_kwargs={"foreign_keys": "Beers.company_id"},
    )


class BreweriesPublic(BreweriesBase):
    id: uuid.UUID
    last_updated: datetime
    date_created: datetime


class BreweriesUpdate(BreweriesBase):
    name: str | None = None


class BreweriesPublicWithBeers(BreweriesPublic):
    beers: Optional[list["BeersPublic"]] = []
