#!/usr/bin/env python3
"""Create an admin user for the closed beta."""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.auth.passwords import hash_password
from app.config import get_settings
from app.db.client import close_mongodb_connection, connect_to_mongodb, get_database
from app.db.repositories.user_repository import UserRepository
from app.models.common import UserRole
from app.models.user import UserCreate


async def create_admin(email: str, password: str, display_name: str) -> None:
    settings = get_settings()
    await connect_to_mongodb(settings)
    db = get_database()
    repo = UserRepository(db)

    existing = await repo.get_by_email(email)
    if existing:
        await db.users.update_one(
            {"email": email.lower()},
            {"$set": {"role": UserRole.ADMIN.value}},
        )
        print(f"Updated existing user to admin: {email}")
    else:
        user = UserCreate(email=email, password=password, display_name=display_name)
        created = await repo.create(user, hash_password(password))
        await db.users.update_one(
            {"_id": created.id},
            {"$set": {"role": UserRole.ADMIN.value}},
        )
        print(f"Created admin user: {email} (beta slot {created.beta_slot})")

    await close_mongodb_connection()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create PROVE admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="Admin")
    args = parser.parse_args()
    asyncio.run(create_admin(args.email, args.password, args.name))


if __name__ == "__main__":
    main()
