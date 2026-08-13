import enum


class ContentVisibility(str, enum.Enum):
    """Who can see a piece of portfolio content on a talent's public profile."""

    PUBLIC = "public"
    MEMBERS = "members"
    RECRUITERS = "recruiters"
