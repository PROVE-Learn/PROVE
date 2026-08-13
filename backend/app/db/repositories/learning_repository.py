from datetime import UTC, datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.collections import LEARNING_ACTIVITIES, LEARNING_PLANS
from app.db.repositories.base import serialize_doc, to_object_id
from app.models.learning import LearningActivity, LearningPlan

class LearningActivityRepository:
    def __init__(self, db: AsyncIOMotorDatabase): self._collection = db[LEARNING_ACTIVITIES]
    async def ensure_indexes(self): await self._collection.create_index("activity_id", unique=True)
    async def upsert(self, activity: LearningActivity):
        values = activity.model_dump(by_alias=False, exclude={"id"})
        await self._collection.update_one({"activity_id": activity.activity_id}, {"$set": values}, upsert=True)
        return LearningActivity.model_validate(serialize_doc(await self._collection.find_one({"activity_id": activity.activity_id})))
    async def get(self, activity_id):
        doc = await self._collection.find_one({"activity_id": activity_id})
        return LearningActivity.model_validate(serialize_doc(doc)) if doc else None

class LearningPlanRepository:
    def __init__(self, db: AsyncIOMotorDatabase): self._collection = db[LEARNING_PLANS]
    async def ensure_indexes(self): await self._collection.create_index("user_id", unique=True)
    async def get_for_user(self, user_id):
        doc = await self._collection.find_one({"user_id": user_id})
        return LearningPlan.model_validate(serialize_doc(doc)) if doc else None
    async def save(self, plan: LearningPlan):
        values = plan.model_dump(by_alias=False, exclude={"id"})
        existing = await self._collection.find_one({"user_id": plan.user_id})
        if existing:
            await self._collection.update_one({"user_id": plan.user_id}, {"$set": values})
            values["_id"] = existing["_id"]
        else:
            result = await self._collection.insert_one(values); values["_id"] = result.inserted_id
        return LearningPlan.model_validate(serialize_doc(values))

class ActivityProgressRepository:
    """User-scoped activity state; kept separate from the global activity catalog."""
    def __init__(self, db: AsyncIOMotorDatabase): self._collection = db["learning_activity_progress"]
    async def ensure_indexes(self): await self._collection.create_index([("user_id", 1), ("activity_id", 1)], unique=True)
    async def get(self, user_id, activity_id): return await self._collection.find_one({"user_id": user_id, "activity_id": activity_id})
    async def save(self, user_id, activity_id, state, evidence=None):
        now = datetime.now(UTC); values = {"user_id": user_id, "activity_id": activity_id, "state": state, "evidence": evidence or [], "updated_at": now}
        existing = await self.get(user_id, activity_id)
        if existing: await self._collection.update_one({"user_id": user_id, "activity_id": activity_id}, {"$set": values}); values["_id"] = existing["_id"]
        else: values["_id"] = (await self._collection.insert_one(values)).inserted_id
        return serialize_doc(values)
