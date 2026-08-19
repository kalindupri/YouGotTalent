from app.models.user import UserRole


def is_visible_to(visibility: str, viewer_role: UserRole | None, *, is_owner: bool = False) -> bool:
    """Whether a piece of portfolio content should be shown to this viewer.

    `private` is checked before the admin short-circuit on purpose. Labelling something
    "Only me" and then showing it to staff would be a false promise, and there is nothing to
    moderate in content nobody else can reach -- the same reasoning that already makes
    writing-sample drafts owner-only regardless of their visibility setting.
    """
    if visibility == "private":
        return is_owner
    if is_owner:
        return True
    if viewer_role == UserRole.ADMIN:
        return True
    if visibility == "public":
        return True
    if visibility == "members":
        return viewer_role is not None
    if visibility == "recruiters":
        return viewer_role == UserRole.RECRUITER
    return True
