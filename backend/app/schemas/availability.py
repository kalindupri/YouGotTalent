import uuid
from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AvailabilityWindowCreate(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="0=Monday .. 6=Sunday")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_time_order(self) -> "AvailabilityWindowCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AvailabilityWindowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_id: uuid.UUID
    day_of_week: int
    start_time: time
    end_time: time
    created_at: datetime
