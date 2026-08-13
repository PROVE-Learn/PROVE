from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.collections import CAREER_ROLE_SELECTIONS
from app.db.repositories.base import serialize_doc
from app.models.career_discovery import CareerRole, TargetRoleSelection


class CareerRoleSelectionRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[CAREER_ROLE_SELECTIONS]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("user_id", unique=True)

    async def get_for_user(self, user_id: str) -> TargetRoleSelection | None:
        doc = await self._collection.find_one({"user_id": user_id})
        serialized = serialize_doc(doc)
        return TargetRoleSelection.model_validate(serialized) if serialized else None

    async def select(
        self, user_id: str, role: CareerRole, assessment_id: str, evidence: list[str]
    ) -> TargetRoleSelection:
        now = datetime.now(UTC)
        doc = {
            "user_id": user_id,
            "role": role.model_dump(),
            "assessment_id": assessment_id,
            "recommendation_evidence": evidence,
            "selected_at": now,
        }
        result = await self._collection.find_one_and_update(
            {"user_id": user_id}, {"$set": doc}, upsert=True, return_document=True
        )
        if result is None:
            doc["_id"] = (await self._collection.find_one({"user_id": user_id}))["_id"]
            result = doc
        return TargetRoleSelection.model_validate(serialize_doc(result))
