from datetime import UTC, datetime

import httpx
import pytest

from app.auth.jwt import create_access_token
from app.career_discovery.catalog import ROLE_BY_ID
from app.config import Settings
from app.dependencies import get_readiness_service, get_settings_dep, get_user_repo
from app.main import create_app
from app.models.common import MemoryCategory, UserRole
from app.models.company_intelligence import Company
from app.models.readiness import CareerReadiness
from app.models.user import UserInDB, UserProfile
from app.services.readiness_service import ReadinessService


def user(user_id: str, targets: list[str] | None = None) -> UserInDB:
    now = datetime.now(UTC)
    return UserInDB(
        _id=user_id,
        email=f"{user_id}@example.com",
        password_hash="private",
        display_name=user_id,
        profile=UserProfile(target_companies=targets or []),
        created_at=now,
        updated_at=now,
    )


class Selections:
    def __init__(self, items):
        self.items = items

    async def get_for_user(self, user_id):
        return self.items.get(user_id)


class Progress:
    def __init__(self, items):
        self.items, self.calls = items, []

    async def list_for_user(self, user_id):
        self.calls.append(user_id)
        return self.items.get(user_id, [])


class Companies:
    def __init__(self, items):
        self.items = items

    async def get(self, company_id):
        return self.items.get(company_id)


class Claims:
    def __init__(self, items):
        self.items = items

    async def list_for_company(self, company_id, role_id=None):
        return self.items.get((company_id, role_id), [])


class Memories:
    def __init__(self, items):
        self.items, self.calls = items, []

    async def list_for_user(self, user_id):
        self.calls.append(user_id)
        return self.items.get(user_id, [])


def selection(user_id: str, role_id="backend_developer"):
    return type("Selection", (), {"user_id": user_id, "role": ROLE_BY_ID[role_id]})()


@pytest.mark.asyncio
async def test_readiness_composes_selected_role_learning_company_and_memory_with_provenance():
    current_user = user("student", ["acme"])
    progress = Progress(
        {"student": [type("ProgressItem", (), {"skill_id": "python", "current_level": 3})()]}
    )
    memories = Memories(
        {"student": [type("Memory", (), {"category": MemoryCategory.COMPLETED_ACTIVITY})()]}
    )
    service = ReadinessService(
        Selections({"student": selection("student")}),
        progress,
        Companies({"acme": Company(company_id="acme", name="Acme")}),
        Claims({("acme", "backend_developer"): [object()]}),
        memories,
    )

    snapshot = await service.get(current_user)

    assert snapshot.target_role_id == "backend_developer"
    assert snapshot.completed_activity_count == 1
    assert snapshot.target_companies[0].role_evidence_count == 1
    assert snapshot.readiness_score > 20
    assert {item.component for item in snapshot.provenance} == {
        "career_discovery",
        "learning",
        "company_intelligence",
        "structured_memory",
    }
    assert progress.calls == ["student"] and memories.calls == ["student"]


@pytest.mark.asyncio
async def test_readiness_requires_a_user_selected_role_before_generating_learning_gaps():
    progress, memories = Progress({}), Memories({"student": []})
    service = ReadinessService(Selections({}), progress, Companies({}), Claims({}), memories)

    snapshot = await service.get(user("student"))

    assert snapshot.readiness_score == 0
    assert snapshot.skill_gaps == []
    assert snapshot.next_actions[0].action == "Select a target role"
    assert progress.calls == []


class Users:
    def __init__(self, *items):
        self.items = {item.id: item for item in items}

    async def get_by_id(self, user_id):
        return self.items.get(user_id)


class ApiReadinessService:
    def __init__(self):
        self.user_ids = []

    async def get(self, current_user):
        self.user_ids.append(current_user.id)
        return CareerReadiness(readiness_score=0, next_actions=[])


@pytest.mark.asyncio
async def test_readiness_api_requires_authentication_and_uses_authenticated_user():
    first, second = user("first"), user("second")
    settings = Settings(app_env="test", jwt_secret="test-secret-key-at-least-32-characters-long")
    service = ApiReadinessService()
    app = create_app()
    app.dependency_overrides[get_settings_dep] = lambda: settings
    app.dependency_overrides[get_user_repo] = lambda: Users(first, second)
    app.dependency_overrides[get_readiness_service] = lambda: service
    headers = {
        item.id: {
            "Authorization": "Bearer "
            + create_access_token(item.id, item.email, UserRole.STUDENT, settings)
        }
        for item in (first, second)
    }

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        assert (await client.get("/api/v1/readiness")).status_code == 401
        assert (await client.get("/api/v1/readiness", headers=headers[first.id])).status_code == 200
        assert (
            await client.get("/api/v1/readiness", headers=headers[second.id])
        ).status_code == 200

    assert service.user_ids == ["first", "second"]
