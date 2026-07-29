"""Create an admin account. Admin accounts are never created via the public API/UI —
this CLI script is the only way, so this file lives outside the app package.

Usage:
    python scripts/create_admin.py <email> <password> <full_name>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: python scripts/create_admin.py <email> <password> <full_name>")
        sys.exit(1)

    email, password, full_name = sys.argv[1], sys.argv[2], sys.argv[3]
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            print(f"A user with email {email} already exists.")
            sys.exit(1)

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        print(f"Created admin account: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
