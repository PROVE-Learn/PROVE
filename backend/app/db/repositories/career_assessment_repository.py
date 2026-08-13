from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.collections import CAREER_ASSESSMENTS
from app.db.repositories.base import serialize_doc, to_object_id
from app.models.career import CareerAssessmentInDB


class CareerAssessmentRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[CAREER_ASSESSMENTS]

    async def ensure_indexes(self) -> None:
        await self._collection.create_index("user_id")
        await self._collection.create_index([("user_id", 1), ("status", 1)])

    async def create(self, user_id: str, question_version: str = "1.0") -> CareerAssessmentInDB:
        now = datetime.now(UTC)
        doc = {
            "user_id": user_id,
            "status": "in_progress",
            "dimensions": {},
            "raw_responses": [],
            "completed_at": None,
            "question_version": question_version,
            "created_at": now,
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return CareerAssessmentInDB.model_validate(serialize_doc(doc))

    async def get_by_id(self, assessment_id: str, user_id: str | None = None) -> CareerAssessmentInDB | None:
        query = {"_id": to_object_id(assessment_id)}
        if user_id is not None:
            query["user_id"] = user_id
        doc = await self._collection.find_one(query)
        serialized = serialize_doc(doc)
        return CareerAssessmentInDB.model_validate(serialized) if serialized else None

    async def get_active_for_user(self, user_id: str) -> CareerAssessmentInDB | None:
        doc = await self._collection.find_one({"user_id": user_id, "status": "in_progress"})
        serialized = serialize_doc(doc)
        return CareerAssessmentInDB.model_validate(serialized) if serialized else None

    async def save_answers(
        self, assessment_id: str, user_id: str, responses: list[dict], dimensions: dict
    ) -> CareerAssessmentInDB | None:
        result = await self._collection.find_one_and_update(
            {"_id": to_object_id(assessment_id), "user_id": user_id, "status": "in_progress"},
            {"$set": {"raw_responses": responses, "dimensions": dimensions}},
            return_document=True,
        )
        serialized = serialize_doc(result)
        return CareerAssessmentInDB.model_validate(serialized) if serialized else None

    async def mark_complete(self, assessment_id: str, user_id: str) -> CareerAssessmentInDB | None:
        now = datetime.now(UTC)
        result = await self._collection.find_one_and_update(
            {"_id": to_object_id(assessment_id), "user_id": user_id, "status": "in_progress"},
            {"$set": {"status": "complete", "completed_at": now}},
            return_document=True,
        )
        serialized = serialize_doc(result)
        return CareerAssessmentInDB.model_validate(serialized) if serialized else None
