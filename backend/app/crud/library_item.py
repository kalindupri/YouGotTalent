import uuid

from sqlalchemy.orm import Session

from app.models.library_item import LibraryItem
from app.schemas.library_item import LibraryItemCreate


def create_library_item(db: Session, talent_id: uuid.UUID, item_in: LibraryItemCreate) -> LibraryItem:
    item = LibraryItem(
        talent_id=talent_id,
        title=item_in.title,
        description=item_in.description,
        media_type=item_in.media_type,
        url=item_in.url,
        visibility=item_in.visibility,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_library_item(db: Session, item_id: uuid.UUID) -> LibraryItem | None:
    return db.query(LibraryItem).filter(LibraryItem.id == item_id).first()


def list_library_items(db: Session, talent_id: uuid.UUID) -> list[LibraryItem]:
    return (
        db.query(LibraryItem)
        .filter(LibraryItem.talent_id == talent_id)
        .order_by(LibraryItem.created_at.desc())
        .all()
    )


def delete_library_item(db: Session, item: LibraryItem) -> None:
    db.delete(item)
    db.commit()
