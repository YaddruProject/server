from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field


class Analytics(BaseModel):
    time: str = Field(
        default_factory=lambda: datetime.now(ZoneInfo("Asia/Kolkata")).strftime(
            "%Y-%m-%d %H:%M:%S",
        ),
        frozen=True,
        init=False,
    )
    value: float
