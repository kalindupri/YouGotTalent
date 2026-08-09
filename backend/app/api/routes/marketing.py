from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.marketing_post import check_approvals, generate_and_post_draft
from app.db.session import get_db
from app.schemas.marketing_post import CheckApprovalsResult, GenerateDraftResult

router = APIRouter(prefix="/admin/marketing", tags=["marketing"])


def require_cron_secret(x_cron_secret: str | None = Header(default=None)) -> None:
    """Separate from admin JWT auth deliberately — this is hit by an unattended external
    scheduler (same pattern as /admin/billing/run-dunning-sweep, since this app has no
    cron/queue of its own), and a JWT would expire long before a long-running cron's next call.
    """
    if not settings.MARKETING_CRON_SECRET or x_cron_secret != settings.MARKETING_CRON_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing cron secret")


@router.post("/generate-draft", response_model=GenerateDraftResult, dependencies=[Depends(require_cron_secret)])
def trigger_generate_draft(db: Session = Depends(get_db)):
    """Meant to be polled periodically (e.g. every 15-30 min). Advances the marketing pipeline
    one step: asks what today's post should be about in Discord, turns a human's reply into a
    branded draft with ✅/❌ reactions once they respond (or auto-generates a topic if nobody
    replies within the timeout), or no-ops if a draft is already pending approval.
    """
    created, reason, post = generate_and_post_draft(db)
    return GenerateDraftResult(created=created, reason=reason, post=post)


@router.post("/check-approvals", response_model=CheckApprovalsResult, dependencies=[Depends(require_cron_secret)])
def trigger_check_approvals(db: Session = Depends(get_db)):
    """Meant to run every 15-30 minutes. Discord reactions are read via REST polling here —
    there's no push notification telling this app when someone reacts.
    """
    result = check_approvals(db)
    return CheckApprovalsResult(**result)
