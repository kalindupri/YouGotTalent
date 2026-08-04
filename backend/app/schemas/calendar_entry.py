import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, model_validator


class CalendarEntryCreate(BaseModel):
    title: str
    start_date: date
    end_date: date
    notes: str | None = None
    is_public: bool = True

    @model_validator(mode="after")
    def check_date_order(self) -> "CalendarEntryCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class CalendarEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_id: uuid.UUID
    title: str
    start_date: date
    end_date: date
    notes: str | None
    is_public: bool
    created_at: datetime


class CalendarEvent(BaseModel):
    """A unified item in the merged talent calendar feed — either a platform Booking or a
    manually-entered CalendarEntry, normalized to the same shape for the frontend."""

    id: uuid.UUID
    kind: str  # "booking" | "entry"
    title: str
    start_at: datetime
    end_at: datetime
    status: str


class BusyRange(BaseModel):
    start_date: date
    end_date: date
    title: str | None = None
