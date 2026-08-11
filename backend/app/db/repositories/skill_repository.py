from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.collections import SKILLS
from app.db.repositories.base import serialize_doc, to_object_id
from app.models.skill import SkillCreate, SkillInDB


class SkillRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[SKILLS]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("skill_id", unique=True)
        await self._collection.create_index("category")
        await self._collection.create_index("parent_skill_id")

    async def get_by_skill_id(self, skill_id: str) -> SkillInDB | None:
        doc = await self._collection.find_one({"skill_id": skill_id})
        serialized = serialize_doc(doc)
        return SkillInDB.model_validate(serialized) if serialized else None

    async def list_all(self) -> list[SkillInDB]:
        cursor = self._collection.find({}).sort("skill_id", 1)
        skills = []
        async for doc in cursor:
            serialized = serialize_doc(doc)
            if serialized:
                skills.append(SkillInDB.model_validate(serialized))
        return skills

    async def upsert(self, skill: SkillCreate) -> SkillInDB:
        now = datetime.now(UTC)
        existing = await self._collection.find_one({"skill_id": skill.skill_id})
        if existing:
            await self._collection.update_one(
                {"skill_id": skill.skill_id},
                {
                    "$set": {
                        "name": skill.name,
                        "category": skill.category,
                        "parent_skill_id": skill.parent_skill_id,
                        "prerequisites": skill.prerequisites,
                        "description": skill.description,
                        "verification_sources": skill.verification_sources,
                    }
                },
            )
            doc = await self._collection.find_one({"skill_id": skill.skill_id})
        else:
            doc = {
                "skill_id": skill.skill_id,
                "name": skill.name,
                "category": skill.category,
                "parent_skill_id": skill.parent_skill_id,
                "prerequisites": skill.prerequisites,
                "description": skill.description,
                "verification_sources": skill.verification_sources,
                "created_at": now,
            }
            result = await self._collection.insert_one(doc)
            doc["_id"] = result.inserted_id

        return SkillInDB.model_validate(serialize_doc(doc))

    async def delete_by_skill_id(self, skill_id: str) -> bool:
        result = await self._collection.delete_one({"skill_id": skill_id})
        return result.deleted_count > 0

    async def count(self) -> int:
        return await self._collection.count_documents({})
