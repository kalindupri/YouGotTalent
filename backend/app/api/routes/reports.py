from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.discord import send_discord_message
from app.crud.report import create_report
from app.db.session import get_db
from app.models.report import ReportCategory
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead

router = APIRouter(prefix="/reports", tags=["reports"])

_CATEGORY_LABELS = {
    ReportCategory.BUG: "🐛 Bug report",
    ReportCategory.SPAM: "🚫 Spam",
    ReportCategory.HARASSMENT: "⚠️ Harassment",
    ReportCategory.FAKE_PROFILE: "🎭 Fake profile",
    ReportCategory.INAPPROPRIATE_CONTENT: "🔞 Inappropriate content",
    ReportCategory.OTHER: "❓ Other",
}


@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def submit_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report = create_report(db, user.id, report_in)

    lines = [
        f"**{_CATEGORY_LABELS.get(report.category, report.category.value)}** from {user.email}",
        f"**Subject:** {report.subject}",
        report.description,
    ]
    if report.target_type and report.target_id:
        lines.append(f"**Target:** {report.target_type.value} `{report.target_id}`")
    if report.page_url:
        lines.append(f"**Page:** {report.page_url}")
    send_discord_message("\n".join(lines))

    return report
