from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.db.collections import USERS
from app.db.repositories.base import serialize_doc
from app.models.common import UserPhase, UserRole
from app.models.user import UserCreate, UserInDB


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[USERS]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("email", unique=True)
        await self._collection.create_index("beta_slot", unique=True, sparse=True)

    async def count_active_users(self) -> int:
        return await self._collection.count_documents({"is_active": True})

    async def get_by_email(self, email: str) -> UserInDB | None:
        doc = await self._collection.find_one({"email": email.lower()})
        serialized = serialize_doc(doc)
        return UserInDB.model_validate(serialized) if serialized else None

    async def get_by_id(self, user_id: str) -> UserInDB | None:
        from app.db.repositories.base import to_object_id

        doc = await self._collection.find_one({"_id": to_object_id(user_id)})
        serialized = serialize_doc(doc)
        return UserInDB.model_validate(serialized) if serialized else None

    async def create(self, user: UserCreate, password_hash: str) -> UserInDB:
        settings = get_settings()
        active_count = await self.count_active_users()
        if active_count >= settings.max_beta_users:
            raise BetaCapacityError(
                f"Beta is full. Maximum {settings.max_beta_users} users allowed."
            )

        now = datetime.now(UTC)
        beta_slot = active_count + 1
        doc = {
            "email": user.email.lower(),
            "password_hash": password_hash,
            "display_name": user.display_name,
            "role": UserRole.STUDENT.value,
            "beta_slot": beta_slot,
            "current_phase": UserPhase.ONBOARDING.value,
            "phase_metadata": {},
            "target_role_id": None,
            "target_company_id": None,
            "preferences": {},
            "created_at": now,
            "updated_at": now,
            "is_active": True,
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return UserInDB.model_validate(serialize_doc(doc))


class BetaCapacityError(Exception):
    pass
