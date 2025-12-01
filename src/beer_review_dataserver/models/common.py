from datetime import datetime, timezone
from functools import partial

from sqlmodel import TIMESTAMP, Column, Field, text

now_func = partial(datetime.now, timezone.utc)


LAST_UPDATED: datetime = Field(
    default_factory=now_func,
    sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    ),
)

DATE_CREATED: datetime = Field(
    default_factory=now_func,
    sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
)
