from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.collections import VERIFICATION_RECORDS
from app.db.repositories.base import serialize_doc, to_object_id
from app.models.verification import VerificationRecordCreate, VerificationRecordInDB


class VerificationRecordRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[VERIFICATION_RECORDS]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("entity_type")
        await self._collection.create_index("entity_id")
        await self._collection.create_index("verification_type")
        await self._collection.create_index("created_at")

    async def create(self, record: VerificationRecordCreate) -> VerificationRecordInDB:
        now = datetime.now(UTC)
        doc = {
            **record.model_dump(),
            "created_at": now,
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return VerificationRecordInDB.model_validate(serialize_doc(doc))

    async def get_by_id(self, record_id: str) -> VerificationRecordInDB | None:
        doc = await self._collection.find_one({"_id": to_object_id(record_id)})
        serialized = serialize_doc(doc)
        return VerificationRecordInDB.model_validate(serialized) if serialized else None

    async def list_for_entity(self, entity_type: str, entity_id: str) -> list[VerificationRecordInDB]:
        cursor = self._collection.find(
            {"entity_type": entity_type, "entity_id": entity_id}
        ).sort("created_at", -1)
        records = []
        async for doc in cursor:
            serialized = serialize_doc(doc)
            if serialized:
                records.append(VerificationRecordInDB.model_validate(serialized))
        return records
