from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.collections import HUMAN_REVIEW_QUEUE
from app.db.repositories.base import serialize_doc, to_object_id
from app.models.common import ReviewStatus
from app.models.verification import HumanReviewItemCreate, HumanReviewItemInDB


class HumanReviewQueueRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[HUMAN_REVIEW_QUEUE]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("status")
        await self._collection.create_index("item_type")
        await self._collection.create_index("created_at")

    async def create(self, item: HumanReviewItemCreate) -> HumanReviewItemInDB:
        now = datetime.now(UTC)
        doc = {
            **item.model_dump(),
            "status": ReviewStatus.PENDING_REVIEW.value,
            "reviewed_by": None,
            "reviewed_at": None,
            "created_at": now,
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return HumanReviewItemInDB.model_validate(serialize_doc(doc))

    async def get_by_id(self, item_id: str) -> HumanReviewItemInDB | None:
        doc = await self._collection.find_one({"_id": to_object_id(item_id)})
        serialized = serialize_doc(doc)
        return HumanReviewItemInDB.model_validate(serialized) if serialized else None

    async def list_pending(self, limit: int = 50) -> list[HumanReviewItemInDB]:
        cursor = (
            self._collection.find({"status": ReviewStatus.PENDING_REVIEW.value})
            .sort("created_at", 1)
            .limit(limit)
        )
        items = []
        async for doc in cursor:
            serialized = serialize_doc(doc)
            if serialized:
                items.append(HumanReviewItemInDB.model_validate(serialized))
        return items

    async def update_status(
        self,
        item_id: str,
        status: ReviewStatus,
        reviewed_by: str | None = None,
    ) -> HumanReviewItemInDB | None:
        now = datetime.now(UTC)
        update: dict = {"status": status.value, "reviewed_at": now}
        if reviewed_by:
            update["reviewed_by"] = reviewed_by

        result = await self._collection.find_one_and_update(
            {"_id": to_object_id(item_id)},
            {"$set": update},
            return_document=True,
        )
        serialized = serialize_doc(result)
        return HumanReviewItemInDB.model_validate(serialized) if serialized else None
