from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def main():
    email = input("Admin email: ").strip().lower()
    password = getpass("Admin password (minimum 8 characters): ")

    if len(password) < 8 or len(password) > 128:
        print("Password must be between 8 and 128 characters.")
        return

    db = SessionLocal()

    try:
        user = db.scalar(select(User).where(User.email == email))

        if user:
            user.role = "Admin"
            user.is_active = True
            user.hashed_password = hash_password(password)
            print("Existing account will be promoted to Admin.")
        else:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                role="Admin",
                is_active=True,
            )
            db.add(user)

        db.commit()
        print("Admin account created or updated successfully.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()