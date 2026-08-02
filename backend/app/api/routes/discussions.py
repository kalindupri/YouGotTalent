import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import discussion as discussion_crud
from app.db.session import get_db
from app.models.discussion import DiscussionCategory
from app.models.user import User
from app.schemas.discussion import ReplyCreate, ReplyRead, ReplyUpdate, ThreadCreate, ThreadRead, ThreadUpdate

router = APIRouter(prefix="/discussions", tags=["discussions"])


@router.get("", response_model=list[ThreadRead])
def read_threads(
    category: DiscussionCategory | None = None,
    title_id: uuid.UUID | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    return discussion_crud.list_threads(db, category, title_id, q)


@router.post("", response_model=ThreadRead, status_code=status.HTTP_201_CREATED)
def create_thread(payload: ThreadCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return discussion_crud.create_thread(db, user.id, payload)


@router.get("/{thread_id}", response_model=ThreadRead)
def read_thread(thread_id: uuid.UUID, db: Session = Depends(get_db)):
    thread = discussion_crud.get_thread_dict(db, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found")
    return thread


@router.patch("/{thread_id}", response_model=ThreadRead)
def update_thread(
    thread_id: uuid.UUID,
    payload: ThreadUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    thread = discussion_crud.get_thread(db, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found")
    if thread.author_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You didn't start this discussion")
    return discussion_crud.update_thread(db, thread, payload)


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(thread_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    thread = discussion_crud.get_thread(db, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found")
    if thread.author_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You didn't start this discussion")
    discussion_crud.delete_thread(db, thread)


@router.get("/{thread_id}/replies", response_model=list[ReplyRead])
def read_replies(thread_id: uuid.UUID, db: Session = Depends(get_db)):
    if discussion_crud.get_thread(db, thread_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found")
    return discussion_crud.list_replies(db, thread_id)


@router.post("/{thread_id}/replies", response_model=ReplyRead, status_code=status.HTTP_201_CREATED)
def create_reply(
    thread_id: uuid.UUID,
    payload: ReplyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if discussion_crud.get_thread(db, thread_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found")
    return discussion_crud.create_reply(db, thread_id, user.id, payload)


def _get_own_reply(db: Session, thread_id: uuid.UUID, reply_id: uuid.UUID, user: User):
    reply = discussion_crud.get_reply(db, reply_id)
    if reply is None or reply.thread_id != thread_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found")
    if reply.author_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You didn't post this reply")
    return reply


@router.patch("/{thread_id}/replies/{reply_id}", response_model=ReplyRead)
def update_reply(
    thread_id: uuid.UUID,
    reply_id: uuid.UUID,
    payload: ReplyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reply = _get_own_reply(db, thread_id, reply_id, user)
    return discussion_crud.update_reply(db, reply, payload)


@router.delete("/{thread_id}/replies/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reply(
    thread_id: uuid.UUID,
    reply_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reply = _get_own_reply(db, thread_id, reply_id, user)
    discussion_crud.delete_reply(db, reply)
