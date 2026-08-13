from datetime import UTC, datetime

import pytest
from app.auth.jwt import create_access_token
from app.config import Settings
from app.main import create_app
from app.dependencies import get_settings_dep, get_user_repo, get_company_intelligence_service, get_learning_service, get_weekly_plan_repo, get_current_admin
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

    async def mentor_summary(self, user_id, user=None):
        return {
            "user_id": user_id,
            "target_role": "machine_learning_engineer",
            "weekly_focus": "Focus this week on Python and machine learning foundations.",
            "top_gaps": ["Python", "statistics", "machine learning"],
            "recommended_projects": ["Build an end-to-end ML project."],
            "next_steps": ["Study Python", "Ship a project"],
        }

    async def mentor_week(self, user_id, user=None):
        return {
            "user_id": user_id,
            "target_role": "machine_learning_engineer",
            "weekly_focus": "Focus this week on Python and machine learning foundations.",
            "milestones": [
                {"day": "Day 1", "objective": "Foundation", "task": "Study Python basics", "outcome": "You can explain the concept."},
                {"day": "Day 2", "objective": "Practice", "task": "Solve 2 coding drills", "outcome": "You can code without notes."},
                {"day": "Day 3", "objective": "Project", "task": "Build a mini project", "outcome": "You made a working artifact."},
            ],
        }

    async def adaptive_roadmap(self, user_id, user=None):
        return {
            "user_id": user_id,
            "target_role": "machine_learning_engineer",
            "focus": "Prioritize Python and data preparation.",
            "adjustments": ["Increase project time for Python and ML foundations."],
            "next_milestone": "Finish a small preprocessing + model training project.",
        }

    async def next_activity(self, user_id, user=None):
        return {
            "activity_id": "intro-python",
            "title": "Build skill: Python",
            "description": "A curated starting activity for Python; completion is not mastery.",
            "skill_id": "python",
            "activity_type": "exercise",
            "difficulty": 2,
            "estimated_effort_hours": 2,
            "prerequisites": ["programming_fundamentals"],
            "source": "PROVE curated foundation",
            "state": "NOT_STARTED",
            "evidence_required": False,
        }

    async def save_weekly_plan(self, user_id, user=None):
        return {"user_id": user_id, "status": "saved", "created_at": "now"}

    async def complete_weekly_milestone(self, user_id, day, user=None):
        return {"user_id": user_id, "completed": day}

    async def get_weekly_plan(self, user_id, user=None):
        return {
            "user_id": user_id,
            "target_role": "machine_learning_engineer",
            "weekly_focus": "Focus this week on Python and machine learning foundations.",
            "milestones": [
                {"day": "Day 1", "objective": "Foundation", "task": "Study Python basics", "outcome": "You can explain the concept."}
            ],
        }

    async def delete_weekly_plan(self, user_id, user=None):
        # emulate deletion success
        return True


class WeeklyPlanRepoStub:
    def __init__(self):
        self.plans = [{"user_id": "a", "target_role": "machine_learning_engineer"}]

    async def list_all(self, limit: int = 100):
        return self.plans

    async def delete_for_user(self, user_id: str):
        self.plans = [p for p in self.plans if p.get("user_id") != user_id]
        return True


async def client_for_admin(admin_user):
    settings = Settings(app_env="test", jwt_secret="test-secret-key-at-least-32-characters-long")
    app = create_app()
    app.dependency_overrides[get_settings_dep] = lambda: settings
    app.dependency_overrides[get_user_repo] = lambda: Users([admin_user])
    app.dependency_overrides[get_weekly_plan_repo] = lambda: WeeklyPlanRepoStub()
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    headers = {admin_user.id: {"Authorization": "Bearer " + create_access_token(admin_user.id, admin_user.email, admin_user.role, settings)}}
    return app, headers


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


@pytest.mark.asyncio
async def test_mentor_summary_endpoint_returns_personalized_guidance():
    a = make_user("a")
    app, headers = await client_for(a)
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/learning/mentor-summary", headers=headers["a"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_role"] == "machine_learning_engineer"
        assert "focus" in data["weekly_focus"].lower()
        assert len(data["recommended_projects"]) >= 1


@pytest.mark.asyncio
async def test_weekly_mentor_loop_returns_daily_milestones():
    a = make_user("a")
    app, headers = await client_for(a)
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/learning/mentor-week", headers=headers["a"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_role"] == "machine_learning_engineer"
        assert len(data["milestones"]) >= 3
        assert any(item["day"] for item in data["milestones"])


@pytest.mark.asyncio
async def test_adaptive_roadmap_reflects_user_progress():
    a = make_user("a")
    app, headers = await client_for(a)
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/learning/adaptive-roadmap", headers=headers["a"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_role"] == "machine_learning_engineer"
        assert "focus" in data
        assert len(data["adjustments"]) >= 1
        assert data["next_milestone"]


@pytest.mark.asyncio
async def test_next_activity_endpoint_returns_a_concrete_learning_task():
    a = make_user("a")
    app, headers = await client_for(a)
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/learning/activities/next", headers=headers["a"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["skill_id"]
        assert data["title"]
        assert data["activity_id"].startswith("intro-")


@pytest.mark.asyncio
async def test_save_weekly_plan_endpoint_persists_plan():
    a = make_user("a")
    app, headers = await client_for(a)
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/learning/plan/weekly", headers=headers["a"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] == "a"
        assert data.get("status") == "saved"


@pytest.mark.asyncio
async def test_complete_weekly_milestone_endpoint_marks_completion():
    a = make_user("a")
    app, headers = await client_for(a)
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/learning/plan/weekly/milestones/Day%201/complete", headers=headers["a"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "a"
        assert data["completed"] == "Day 1"


@pytest.mark.asyncio
async def test_get_weekly_plan_endpoint_returns_saved_plan():
    a = make_user("a")
    app, headers = await client_for(a)
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/learning/plan/weekly", headers=headers["a"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "a"
        assert "milestones" in data


@pytest.mark.asyncio
async def test_delete_weekly_plan_endpoint_removes_saved_plan():
    a = make_user("a")
    app, headers = await client_for(a)
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.delete("/api/v1/learning/plan/weekly", headers=headers["a"])
        assert resp.status_code == 204


@pytest.mark.asyncio
async def test_admin_list_and_delete_weekly_plans():
    admin = make_user("admin")
    admin.role = UserRole.ADMIN
    app, headers = await client_for_admin(admin)
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/admin/learning/plans", headers=headers["admin"])
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

        # delete a user's plan
        resp = await client.delete("/api/v1/admin/learning/plan/a", headers=headers["admin"])
        assert resp.status_code == 204