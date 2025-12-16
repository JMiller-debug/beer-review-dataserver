"""Common utilities for the database models."""

import datetime
from functools import partial

from sqlmodel import TIMESTAMP, Column, Field, text

now_func = partial(datetime.datetime.now, datetime.UTC)


LAST_UPDATED: datetime.datetime = Field(
    default_factory=now_func,
    sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    ),
)

DATE_CREATED: datetime.datetime = Field(
    default_factory=now_func,
    sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
)
