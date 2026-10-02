import argparse

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Create or update a local ReadySafe administrator account.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    email = args.email.strip().lower()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(name=args.name.strip(), email=email, password_hash=hash_password(args.password), is_admin=True)
            db.add(user)
        else:
            user.name = args.name.strip()
            user.password_hash = hash_password(args.password)
            user.is_admin = True
            user.is_active = True
        db.commit()
    print(f"Administrator ready: {email}")


if __name__ == "__main__":
    main()
