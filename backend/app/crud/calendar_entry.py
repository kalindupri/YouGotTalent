import calendar as _calendar
import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy.orm import Session

from app.crud.booking import list_bookings_for_talent
from app.models.booking import Booking
from app.models.calendar_entry import CalendarEntry
from app.schemas.calendar_entry import BusyRange, CalendarEntryCreate, CalendarEvent


def create_calendar_entry(db: Session, talent_id: uuid.UUID, entry_in: CalendarEntryCreate) -> CalendarEntry:
    entry = CalendarEntry(
        talent_id=talent_id,
        title=entry_in.title,
        start_date=entry_in.start_date,
        end_date=entry_in.end_date,
        notes=entry_in.notes,
        is_public=entry_in.is_public,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_calendar_entry(db: Session, entry_id: uuid.UUID) -> CalendarEntry | None:
    return db.query(CalendarEntry).filter(CalendarEntry.id == entry_id).first()


def list_calendar_entries(db: Session, talent_id: uuid.UUID) -> list[CalendarEntry]:
    return (
        db.query(CalendarEntry)
        .filter(CalendarEntry.talent_id == talent_id)
        .order_by(CalendarEntry.start_date.asc())
        .all()
    )


def delete_calendar_entry(db: Session, entry: CalendarEntry) -> None:
    db.delete(entry)
    db.commit()


def _month_bounds(month: str) -> tuple[date, date]:
    year, month_num = (int(part) for part in month.split("-"))
    last_day = _calendar.monthrange(year, month_num)[1]
    return date(year, month_num, 1), date(year, month_num, last_day)


def get_monthly_calendar(db: Session, talent_id: uuid.UUID, month: str) -> list[CalendarEvent]:
    month_start, month_end = _month_bounds(month)

    bookings = [
        b
        for b in list_bookings_for_talent(db, talent_id)
        if b.status in ("pending", "accepted") and b.start_at.date() <= month_end and b.end_at.date() >= month_start
    ]
    entries = [
        e
        for e in list_calendar_entries(db, talent_id)
        if e.start_date <= month_end and e.end_date >= month_start
    ]

    events = [
        CalendarEvent(
            id=b.id,
            kind="booking",
            title=b.casting_call_title or f"Booking with {b.recruiter_company_name}",
            start_at=b.start_at,
            end_at=b.end_at,
            status=b.status,
        )
        for b in bookings
    ]
    events += [
        CalendarEvent(
            id=e.id,
            kind="entry",
            title=e.title,
            start_at=_to_datetime(e.start_date),
            end_at=_to_datetime(e.end_date),
            status="confirmed",
        )
        for e in entries
    ]
    return sorted(events, key=lambda e: e.start_at)


def _to_datetime(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def get_busy_dates(db: Session, talent_id: uuid.UUID) -> list[BusyRange]:
    bookings = (
        db.query(Booking)
        .filter(Booking.talent_id == talent_id, Booking.status == "accepted")
        .all()
    )
    entries = list_calendar_entries(db, talent_id)

    ranges = [BusyRange(start_date=b.start_at.date(), end_date=b.end_at.date(), title=None) for b in bookings]
    ranges += [
        BusyRange(start_date=e.start_date, end_date=e.end_date, title=e.title if e.is_public else None)
        for e in entries
    ]
    return sorted(ranges, key=lambda r: r.start_date)
