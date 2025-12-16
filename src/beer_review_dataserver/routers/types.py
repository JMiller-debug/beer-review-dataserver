"""Dataclasses to define for arguments into routes."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, ConfigDict


class CommonOptions(BaseModel):
    """Common Search based options for routes."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    identifier: str | None = None


class QueryOptions(BaseModel):
    """
    Common Query based Options for routes.

    i.e. Limit, offset, order, orderby
    """

    model_config = ConfigDict(extra="forbid")

    offset: int = 0
    limit: Annotated[int, Query(le=100)] = 100
    orderby: str | None = None
    order: Literal["asc", "desc"] = "asc"


class DeleteResponse(BaseModel):
    """Return type for delete action."""

    ok: bool


class CreateFileResponse(BaseModel):
    """Return type for delete action."""

    filename: str
