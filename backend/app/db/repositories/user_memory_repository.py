from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.collections import USER_MEMORIES
from app.db.repositories.base import serialize_doc, to_object_id
from app.models.memory import MemoryCreate, MemoryUpdate, UserMemoryInDB


class UserMemoryRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[USER_MEMORIES]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index([("user_id", 1), ("updated_at", -1)])

    async def create(self, user_id: str, memory: MemoryCreate) -> UserMemoryInDB:
        now = datetime.now(UTC)
        doc = {"user_id": user_id, **memory.model_dump(), "created_at": now, "updated_at": now}
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return UserMemoryInDB.model_validate(serialize_doc(doc))

    async def list_for_user(self, user_id: str) -> list[UserMemoryInDB]:
        cursor = self._collection.find({"user_id": user_id}).sort("updated_at", -1)
        memories = []
        async for doc in cursor:
            serialized = serialize_doc(doc)
            if serialized:
                memories.append(UserMemoryInDB.model_validate(serialized))
        return memories

    async def update(
        self, user_id: str, memory_id: str, update: MemoryUpdate
    ) -> UserMemoryInDB | None:
        values = update.model_dump(exclude_unset=True)
        values["updated_at"] = datetime.now(UTC)
        result = await self._collection.find_one_and_update(
            {"_id": to_object_id(memory_id), "user_id": user_id},
            {"$set": values},
            return_document=True,
        )
        serialized = serialize_doc(result)
        return UserMemoryInDB.model_validate(serialized) if serialized else None

    async def delete(self, user_id: str, memory_id: str) -> bool:
        result = await self._collection.delete_one(
            {"_id": to_object_id(memory_id), "user_id": user_id}
        )
        return result.deleted_count == 1
