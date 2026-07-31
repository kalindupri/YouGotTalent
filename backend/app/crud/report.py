import uuid

from sqlalchemy.orm import Session

from app.models.report import Report, ReportCategory, ReportStatus
from app.schemas.report import ReportCreate, ReportStatusUpdate


def create_report(db: Session, reporter_user_id: uuid.UUID, report_in: ReportCreate) -> Report:
    report = Report(reporter_user_id=reporter_user_id, **report_in.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: uuid.UUID) -> Report | None:
    return db.query(Report).filter(Report.id == report_id).first()


def list_reports(
    db: Session,
    status_filter: ReportStatus | None = None,
    category_filter: ReportCategory | None = None,
) -> list[Report]:
    query = db.query(Report)
    if status_filter is not None:
        query = query.filter(Report.status == status_filter)
    if category_filter is not None:
        query = query.filter(Report.category == category_filter)
    return query.order_by(Report.created_at.desc()).all()


def update_report_status(db: Session, report: Report, update: ReportStatusUpdate) -> Report:
    report.status = update.status
    if update.admin_notes is not None:
        report.admin_notes = update.admin_notes
    db.commit()
    db.refresh(report)
    return report
