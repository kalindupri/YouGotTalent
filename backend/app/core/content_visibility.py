from app.models.user import UserRole


def is_visible_to(visibility: str, viewer_role: UserRole | None) -> bool:
    if viewer_role == UserRole.ADMIN:
        return True
    if visibility == "public":
        return True
    if visibility == "members":
        return viewer_role is not None
    if visibility == "recruiters":
        return viewer_role == UserRole.RECRUITER
    return True
