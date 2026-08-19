import enum


class ContentVisibility(str, enum.Enum):
    """Who can see a piece of portfolio content on a talent's public profile."""

    PUBLIC = "public"
    MEMBERS = "members"
    RECRUITERS = "recruiters"
    # Owner only -- not even admins. For work in progress the talent wants to keep on their
    # own dashboard without publishing it anywhere.
    PRIVATE = "private"
