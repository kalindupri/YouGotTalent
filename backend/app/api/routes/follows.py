import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_talent_profile
from app.crud.follow import follow_recruiter, list_followed_recruiters, unfollow_recruiter
from app.crud.recruiter_profile import get_recruiter_profile
from app.db.session import get_db
from app.models.talent_profile import TalentProfile
from app.schemas.follow import FollowRead

router = APIRouter(tags=["follows"])


@router.post("/recruiters/{recruiter_id}/follow", response_model=FollowRead, status_code=status.HTTP_201_CREATED)
def follow(
    recruiter_id: uuid.UUID,
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    recruiter = get_recruiter_profile(db, recruiter_id)
    if recruiter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter profile not found")
    try:
        return follow_recruiter(db, talent.id, recruiter_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You're already following this recruiter")


@router.delete("/recruiters/{recruiter_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow(
    recruiter_id: uuid.UUID,
    db: Session = Depends(get_db),
    talent: TalentProfile = Depends(get_current_talent_profile),
):
    unfollow_recruiter(db, talent.id, recruiter_id)


@router.get("/talents/me/following", response_model=list[FollowRead])
def read_my_following(db: Session = Depends(get_db), talent: TalentProfile = Depends(get_current_talent_profile)):
    return list_followed_recruiters(db, talent.id)
