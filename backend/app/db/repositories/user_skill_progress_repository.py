from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.collections import USER_SKILL_PROGRESS
from app.db.repositories.base import serialize_doc, to_object_id
from app.models.common import MasteryLevel
from app.models.skill import UserSkillProgressInDB


class UserSkillProgressRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[USER_SKILL_PROGRESS]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("user_id", 1), ("skill_id", 1)],
            unique=True,
        )
        await self._collection.create_index("user_id")

    async def get(self, user_id: str, skill_id: str) -> UserSkillProgressInDB | None:
        doc = await self._collection.find_one({"user_id": user_id, "skill_id": skill_id})
        serialized = serialize_doc(doc)
        return UserSkillProgressInDB.model_validate(serialized) if serialized else None

    async def list_for_user(self, user_id: str) -> list[UserSkillProgressInDB]:
        cursor = self._collection.find({"user_id": user_id}).sort("skill_id", 1)
        results = []
        async for doc in cursor:
            serialized = serialize_doc(doc)
            if serialized:
                results.append(UserSkillProgressInDB.model_validate(serialized))
        return results

    async def create_or_get(self, user_id: str, skill_id: str) -> UserSkillProgressInDB:
        existing = await self.get(user_id, skill_id)
        if existing:
            return existing

        now = datetime.now(UTC)
        doc = {
            "user_id": user_id,
            "skill_id": skill_id,
            "mastery_level": MasteryLevel.UNKNOWN.value,
            "signals": {
                "knowledge": {"score": 0.0, "last_updated": None, "evidence_count": 0},
                "performance": {"score": 0.0, "last_updated": None, "evidence_count": 0},
                "consistency": {"score": 0.0, "last_updated": None, "evidence_count": 0},
                "independence": {"score": 0.0, "last_updated": None, "evidence_count": 0},
                "confidence": {"score": 0.0, "last_updated": None, "evidence_count": 0},
            },
            "weaknesses": [],
            "evidence_records": [],
            "next_retest_at": None,
            "updated_at": now,
            "current_level": 0,
            "target_level": 3,
            "evidence": [],
            "source": "USER_REPORTED",
            "confidence": 0.0,
            "last_assessed": None,
            "progress": 0.0,
            "status": "NOT_STARTED",
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return UserSkillProgressInDB.model_validate(serialize_doc(doc))

    async def update_mastery_level(
        self, user_id: str, skill_id: str, mastery_level: MasteryLevel
    ) -> UserSkillProgressInDB | None:
        now = datetime.now(UTC)
        result = await self._collection.find_one_and_update(
            {"user_id": user_id, "skill_id": skill_id},
            {"$set": {"mastery_level": mastery_level.value, "updated_at": now}},
            return_document=True,
        )
        serialized = serialize_doc(result)
        return UserSkillProgressInDB.model_validate(serialized) if serialized else None

    async def update_details(self, user_id: str, skill_id: str, values: dict) -> UserSkillProgressInDB | None:
        values = {**values, "updated_at": datetime.now(UTC)}
        result = await self._collection.find_one_and_update(
            {"user_id": user_id, "skill_id": skill_id}, {"$set": values}, return_document=True
        )
        serialized = serialize_doc(result)
        return UserSkillProgressInDB.model_validate(serialized) if serialized else None
