import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_talent_profile
from app.crud.calendar_entry import (
    create_calendar_entry,
    delete_calendar_entry,
    get_busy_dates,
    get_calendar_entry,
    get_monthly_calendar,
    list_calendar_entries,
)
from app.crud.talent_profile import get_talent_profile
from app.db.session import get_db
from app.models.talent_profile import TalentProfile
from app.schemas.calendar_entry import BusyRange, CalendarEntryCreate, CalendarEntryRead, CalendarEvent

router = APIRouter(tags=["calendar"])

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@router.get("/talents/me/calendar", response_model=list[CalendarEvent])
def read_my_calendar(
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    if not _MONTH_RE.match(month):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="month must be in YYYY-MM format")
    return get_monthly_calendar(db, talent.id, month)


@router.get("/talents/{talent_id}/calendar/busy-dates", response_model=list[BusyRange])
def read_talent_busy_dates(talent_id: uuid.UUID, db: Session = Depends(get_db)):
    talent = get_talent_profile(db, talent_id)
    if talent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent profile not found")
    return get_busy_dates(db, talent_id)


@router.get("/talents/me/calendar-entries", response_model=list[CalendarEntryRead])
def read_my_calendar_entries(
    db: Session = Depends(get_db), talent: TalentProfile = Depends(get_current_talent_profile)
):
    return list_calendar_entries(db, talent.id)


@router.post("/talents/me/calendar-entries", response_model=CalendarEntryRead, status_code=status.HTTP_201_CREATED)
def add_my_calendar_entry(
    entry_in: CalendarEntryCreate,
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    return create_calendar_entry(db, talent.id, entry_in)


@router.delete("/talents/me/calendar-entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_my_calendar_entry(
    entry_id: uuid.UUID,
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    entry = get_calendar_entry(db, entry_id)
    if entry is None or entry.talent_id != talent.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar entry not found")
    delete_calendar_entry(db, entry)
