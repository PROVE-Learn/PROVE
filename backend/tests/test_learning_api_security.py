from datetime import UTC, datetime
import httpx
import pytest
from app.auth.jwt import create_access_token
from app.config import Settings
from app.dependencies import get_learning_service, get_settings_dep, get_user_repo
from app.main import create_app
from app.models.user import UserInDB
from app.models.common import UserRole

def make_user(user_id):
    now = datetime.now(UTC)
    return UserInDB(_id=user_id, email=f"{user_id}@example.com", password_hash="x", display_name=user_id, created_at=now, updated_at=now)

class Users:
    def __init__(self, users): self.users = {u.id: u for u in users}
    async def get_by_id(self, user_id): return self.users.get(user_id)

class Service:
    def __init__(self):
        self.started_activities = set()

    async def list_skills(self): return []
    async def get_skill(self, skill_id):
        from fastapi import HTTPException
        if skill_id != "python": raise HTTPException(status_code=404, detail="Skill not found")
        return {"skill_id": "python", "name": "Python", "category": "programming", "description": "", "prerequisites": [], "related_skills": [], "difficulty": 2, "version": "1.0", "active": True}
    async def gaps(self, user_id): return [{"skill_id": user_id, "skill_name": user_id, "current_level": 0, "required_level": 1, "gap_size": 1, "priority": 1, "prerequisites": [], "reason": "test"}]
    async def plan(self, user_id): return {"user_id": user_id, "target_role": "backend_developer", "gaps": [], "stages": [], "estimated_effort_hours": 0, "status": "ACTIVE"}
    async def start(self, user_id, activity_id):
        from fastapi import HTTPException
        if activity_id != "intro-python": raise HTTPException(status_code=404, detail="Activity not found")
        self.started_activities.add((user_id, activity_id))
        return {"activity_id": activity_id, "title": "Python", "description": "", "skill_id": "python", "activity_type": "exercise", "difficulty": 1, "estimated_effort_hours": 1, "prerequisites": [], "state": "STARTED"}
    async def complete(self, user_id, activity_id, evidence):
        from fastapi import HTTPException
        if activity_id != "intro-python": raise HTTPException(status_code=404, detail="Activity not found")
        if (user_id, activity_id) not in self.started_activities: raise HTTPException(status_code=409, detail="Activity must be started first")
        if not evidence: raise HTTPException(status_code=422, detail="Evidence is required")
        return {"activity_id": activity_id, "title": "Python", "description": "", "skill_id": "python", "activity_type": "exercise", "difficulty": 1, "estimated_effort_hours": 1, "prerequisites": [], "state": "COMPLETED"}
    async def progress_view(self, user_id): return []

async def client_for(*users):
    settings = Settings(app_env="test", jwt_secret="test-secret-key-at-least-32-characters-long")
    app = create_app(); app.dependency_overrides[get_settings_dep] = lambda: settings; app.dependency_overrides[get_user_repo] = lambda: Users(users); service = Service(); app.dependency_overrides[get_learning_service] = lambda: service
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    headers = {u.id: {"Authorization": "Bearer " + create_access_token(u.id, u.email, u.role, settings)} for u in users}
    return client, headers

@pytest.mark.asyncio
async def test_learning_apis_require_authentication():
    client, _ = await client_for(make_user("a"))
    async with client:
        assert (await client.get("/api/v1/skills")).status_code == 401
        assert (await client.get("/api/v1/learning/progress")).status_code == 401

@pytest.mark.asyncio
async def test_invalid_skill_and_activity_ids_are_rejected():
    client, headers = await client_for(make_user("a"))
    async with client:
        assert (await client.get("/api/v1/skills/nope", headers=headers["a"])).status_code == 404
        assert (await client.post("/api/v1/learning/activities/nope/start", headers=headers["a"])).status_code == 404

@pytest.mark.asyncio
async def test_progress_requests_are_scoped_to_authenticated_user():
    a, b = make_user("a"), make_user("b"); client, headers = await client_for(a, b)
    async with client:
        first = (await client.get("/api/v1/learning/skill-gaps", headers=headers["a"])).json()
        second = (await client.get("/api/v1/learning/skill-gaps", headers=headers["b"])).json()
    assert first[0]["skill_id"] == "a" and second[0]["skill_id"] == "b"

@pytest.mark.asyncio
async def test_activity_completion_requires_evidence_and_start():
    client, headers = await client_for(make_user("a"))
    async with client:
        assert (await client.post("/api/v1/learning/activities/intro-python/complete", headers=headers["a"], json={"evidence": ["x"]})).status_code == 409
        assert (await client.post("/api/v1/learning/activities/intro-python/start", headers=headers["a"])).status_code == 200
        assert (await client.post("/api/v1/learning/activities/intro-python/complete", headers=headers["a"], json={"evidence": []})).status_code == 422

