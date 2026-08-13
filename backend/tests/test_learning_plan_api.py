from datetime import UTC, datetime

import pytest
from app.auth.jwt import create_access_token
from app.config import Settings
from app.main import create_app
from app.dependencies import get_settings_dep, get_user_repo, get_company_intelligence_service, get_learning_service
from app.models.user import UserInDB
from app.models.common import UserRole


def make_user(user_id):
    now = datetime.now(UTC)
    return UserInDB(_id=user_id, email=f"{user_id}@example.com", password_hash="x", display_name=user_id, created_at=now, updated_at=now)


class Users:
    def __init__(self, users):
        self.users = {u.id: u for u in users}

    async def get_by_id(self, user_id):
        return self.users.get(user_id)


class CompanyService:
    async def extract_role_skills(self, company_id, role_id):
        return ["python", "machine_learning", "sql"]


class LearningServiceStub:
    async def plan_for_company_role(self, user_id, company_id, role_id, company_intel_service):
        return {
            "user_id": user_id,
            "target_role": role_id,
            "gaps": [],
            "stages": [],
            "estimated_effort_hours": 0,
            "status": "ACTIVE",
        }


async def client_for(*users):
    settings = Settings(app_env="test", jwt_secret="test-secret-key-at-least-32-characters-long")
    app = create_app()
    app.dependency_overrides[get_settings_dep] = lambda: settings
    app.dependency_overrides[get_user_repo] = lambda: Users(users)
    app.dependency_overrides[get_company_intelligence_service] = lambda: CompanyService()
    app.dependency_overrides[get_learning_service] = lambda: LearningServiceStub()
    headers = {u.id: {"Authorization": "Bearer " + create_access_token(u.id, u.email, u.role, settings)} for u in users}
    return app, headers


@pytest.mark.asyncio
async def test_plan_for_company_role_endpoint_returns_plan():
    a = make_user("a")
    app, headers = await client_for(a)
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/learning/plan/company/example_co/role/machine_learning_engineer", headers=headers["a"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "a"
        assert data["target_role"] == "machine_learning_engineer"
