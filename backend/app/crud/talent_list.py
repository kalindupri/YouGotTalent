import uuid

from sqlalchemy.orm import Session

from app.models.talent_list import TalentList, TalentListMember
from app.schemas.talent_list import TalentListCreate, TalentListMemberCreate


def _attach_display_names(talent_list: TalentList) -> TalentList:
    for member in talent_list.members:
        member.talent_display_name = member.talent.display_name
    return talent_list


def create_talent_list(db: Session, recruiter_id: uuid.UUID, list_in: TalentListCreate) -> TalentList:
    talent_list = TalentList(recruiter_id=recruiter_id, name=list_in.name)
    db.add(talent_list)
    db.commit()
    db.refresh(talent_list)
    return _attach_display_names(talent_list)


def get_talent_list(db: Session, list_id: uuid.UUID) -> TalentList | None:
    return db.query(TalentList).filter(TalentList.id == list_id).first()


def list_talent_lists(db: Session, recruiter_id: uuid.UUID) -> list[TalentList]:
    lists = (
        db.query(TalentList)
        .filter(TalentList.recruiter_id == recruiter_id)
        .order_by(TalentList.created_at.desc())
        .all()
    )
    return [_attach_display_names(l) for l in lists]


def delete_talent_list(db: Session, talent_list: TalentList) -> None:
    db.delete(talent_list)
    db.commit()


def add_member(db: Session, list_id: uuid.UUID, member_in: TalentListMemberCreate) -> TalentListMember:
    member = TalentListMember(list_id=list_id, talent_id=member_in.talent_id, notes=member_in.notes)
    db.add(member)
    db.commit()
    db.refresh(member)
    member.talent_display_name = member.talent.display_name
    return member


def get_member(db: Session, member_id: uuid.UUID) -> TalentListMember | None:
    return db.query(TalentListMember).filter(TalentListMember.id == member_id).first()


def update_member_notes(db: Session, member: TalentListMember, notes: str | None) -> TalentListMember:
    member.notes = notes
    db.commit()
    db.refresh(member)
    member.talent_display_name = member.talent.display_name
    return member


def remove_member(db: Session, member: TalentListMember) -> None:
    db.delete(member)
    db.commit()
