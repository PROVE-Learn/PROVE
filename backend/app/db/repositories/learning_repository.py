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


class WeeklyPlanRepository:
    """Persist WeeklyMentorPlan objects per user in LEARNING_SESSIONS."""
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db["learning_sessions"]

    async def ensure_indexes(self):
        await self._collection.create_index([("user_id", 1)], unique=True)

    async def get_for_user(self, user_id: str):
        doc = await self._collection.find_one({"user_id": user_id})
        return serialize_doc(doc) if doc else None

    async def save_weekly(self, plan: dict):
        # plan is a serializable dict representing WeeklyMentorPlan
        values = dict(plan)
        now = datetime.now(UTC)
        # normalize milestones: add created_at, progress, completed_at
        milestones = []
        for m in values.get("milestones", []):
            mm = dict(m)
            mm.setdefault("created_at", now)
            mm.setdefault("completed_at", None)
            mm.setdefault("progress", 0)
            milestones.append(mm)
        values["milestones"] = milestones
        existing = await self._collection.find_one({"user_id": plan.get("user_id")})
        if existing:
            # archive previous version to history collection
            history = dict(existing)
            history.setdefault("archived_at", now)
            history.setdefault("version", existing.get("version", 1))
            await self._collection.database["learning_sessions_history"].insert_one(history)
            # increment version
            values["version"] = existing.get("version", 1) + 1
            values["updated_at"] = now
            await self._collection.update_one({"user_id": plan.get("user_id")}, {"$set": values})
            values["_id"] = existing["_id"]
        else:
            values["created_at"] = now
            values["updated_at"] = now
            values["version"] = 1
            result = await self._collection.insert_one(values)
            values["_id"] = result.inserted_id
        return serialize_doc(values)

    async def mark_milestone_complete(self, user_id: str, day: str):
        doc = await self._collection.find_one({"user_id": user_id})
        if not doc:
            return None
        now = datetime.now(UTC)
        updated = False
        milestones = doc.get("milestones", [])
        for m in milestones:
            if m.get("day") == day:
                m["completed_at"] = now
                m["progress"] = 100
                updated = True
                break
        if updated:
            await self._collection.update_one({"user_id": user_id}, {"$set": {"milestones": milestones, "updated_at": now}})
            doc = await self._collection.find_one({"user_id": user_id})
            return serialize_doc(doc)
        return None

    async def delete_for_user(self, user_id: str):
        doc = await self._collection.find_one_and_delete({"user_id": user_id})
        return serialize_doc(doc) if doc else None

    async def list_all(self, limit: int = 100):
        cursor = self._collection.find({}).sort("updated_at", -1).limit(limit)
        results = []
        async for doc in cursor:
            results.append(serialize_doc(doc))
        return results
