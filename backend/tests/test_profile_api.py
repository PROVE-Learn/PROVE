from datetime import UTC, datetime

import httpx
import pytest
import pytest_asyncio

from app.auth.jwt import create_access_token
from app.config import Settings
from app.dependencies import get_settings_dep, get_user_memory_repo, get_user_repo
from app.main import create_app
from app.models.common import UserRole
from app.models.memory import MemoryCreate, MemoryUpdate, UserMemoryInDB
from app.models.user import UserInDB, UserProfileUpdate

USER_A_ID = "64b64c3e5e4f88c9d4000001"
USER_B_ID = "64b64c3e5e4f88c9d4000002"
MEMORY_A_ID = "64b64c3e5e4f88c9d4000011"
MEMORY_B_ID = "64b64c3e5e4f88c9d4000012"


def make_user(user_id: str, email: str) -> UserInDB:
    now = datetime.now(UTC)
    return UserInDB(
        _id=user_id,
        email=email,
        password_hash="private-hash",
        display_name=email.split("@")[0],
        created_at=now,
        updated_at=now,
    )


class FakeUserRepository:
    def __init__(self) -> None:
        self.users = {
            USER_A_ID: make_user(USER_A_ID, "student-a@example.com"),
            USER_B_ID: make_user(USER_B_ID, "student-b@example.com"),
        }

    async def get_by_id(self, user_id: str) -> UserInDB | None:
        return self.users.get(user_id)

    async def get_profile(self, user_id: str) -> UserInDB | None:
        return self.users.get(user_id)

    async def update_profile(self, user_id: str, update: UserProfileUpdate) -> UserInDB | None:
        user = self.users.get(user_id)
        if user is None:
            return None
        values = update.model_dump(exclude_unset=True)
        if "display_name" in values:
            user.display_name = values.pop("display_name")
        if "learning_preferences" in values:
            user.preferences = values.pop("learning_preferences")
        profile_values = user.profile.model_dump()
        profile_values.update(values)
        user.profile = user.profile.model_validate(profile_values)
        return user


class FakeMemoryRepository:
    def __init__(self) -> None:
        self.memories: dict[str, UserMemoryInDB] = {}

    async def create(self, user_id: str, memory: MemoryCreate) -> UserMemoryInDB:
        memory_id = (
            MEMORY_A_ID
            if not self.memories
            else f"64b64c3e5e4f88c9d40000{len(self.memories) + 20:02d}"
        )
        now = datetime.now(UTC)
        result = UserMemoryInDB(
            _id=memory_id,
            user_id=user_id,
            created_at=now,
            updated_at=now,
            **memory.model_dump(),
        )
        self.memories[memory_id] = result
        return result

    async def list_for_user(self, user_id: str) -> list[UserMemoryInDB]:
        return [memory for memory in self.memories.values() if memory.user_id == user_id]

    async def update(
        self, user_id: str, memory_id: str, update: MemoryUpdate
    ) -> UserMemoryInDB | None:
        memory = self.memories.get(memory_id)
        if memory is None or memory.user_id != user_id:
            return None
        values = memory.model_dump()
        values.update(update.model_dump(exclude_unset=True))
        values["updated_at"] = datetime.now(UTC)
        updated = UserMemoryInDB.model_validate(values)
        self.memories[memory_id] = updated
        return updated

    async def delete(self, user_id: str, memory_id: str) -> bool:
        memory = self.memories.get(memory_id)
        if memory is None or memory.user_id != user_id:
            return False
        del self.memories[memory_id]
        return True


@pytest_asyncio.fixture
async def api_client():
    app = create_app()
    users = FakeUserRepository()
    memories = FakeMemoryRepository()
    settings = Settings(jwt_secret="test-secret-key-at-least-32-characters-long")
    app.dependency_overrides[get_user_repo] = lambda: users
    app.dependency_overrides[get_user_memory_repo] = lambda: memories
    app.dependency_overrides[get_settings_dep] = lambda: settings

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client, memories, settings
    app.dependency_overrides.clear()


def auth_headers(user_id: str, email: str, settings: Settings) -> dict[str, str]:
    token = create_access_token(user_id, email, UserRole.STUDENT, settings)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_profile_requires_authentication(api_client):
    client, _, _ = api_client

    response = await client.get("/api/v1/profile")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_returns_current_user_only(api_client):
    client, _, settings = api_client

    response = await client.get(
        "/api/v1/profile", headers=auth_headers(USER_A_ID, "student-a@example.com", settings)
    )

    assert response.status_code == 200
    assert response.json()["email"] == "student-a@example.com"
    assert "password_hash" not in response.json()


@pytest.mark.asyncio
async def test_update_profile_persists_requested_fields(api_client):
    client, _, settings = api_client

    response = await client.patch(
        "/api/v1/profile",
        headers=auth_headers(USER_A_ID, "student-a@example.com", settings),
        json={
            "display_name": "Student A",
            "degree": "B.Tech",
            "specialization": "Computer Science",
            "graduation_year": 2027,
            "experience_level": "student",
            "known_skills": [
                {"name": "Python", "level": "intermediate", "evidence": "Course project"}
            ],
            "learning_preferences": {"learning_style": "hands-on", "learning_goals": ["APIs"]},
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Student A"
    assert response.json()["known_skills"][0]["name"] == "Python"
    assert response.json()["learning_preferences"]["learning_style"] == "hands-on"


@pytest.mark.asyncio
async def test_profile_rejects_invalid_data(api_client):
    client, _, settings = api_client

    response = await client.patch(
        "/api/v1/profile",
        headers=auth_headers(USER_A_ID, "student-a@example.com", settings),
        json={"graduation_year": 1800},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_profile_rejects_blank_list_values_in_updates(api_client):
    client, _, settings = api_client

    blank_interest = await client.patch(
        "/api/v1/profile",
        headers=auth_headers(USER_A_ID, "student-a@example.com", settings),
        json={"interests": ["", "AI"]},
    )
    blank_goal = await client.patch(
        "/api/v1/profile",
        headers=auth_headers(USER_A_ID, "student-a@example.com", settings),
        json={"learning_preferences": {"learning_goals": ["", "APIs"]}},
    )

    assert blank_interest.status_code == 422
    assert blank_goal.status_code == 422


@pytest.mark.asyncio
async def test_memory_create_and_retrieve(api_client):
    client, _, settings = api_client
    headers = auth_headers(USER_A_ID, "student-a@example.com", settings)

    created = await client.post(
        "/api/v1/profile/memory",
        headers=headers,
        json={
            "category": "career_goal",
            "key": "target_role",
            "value": "Backend developer",
            "source": "USER_REPORTED",
            "confidence": 1.0,
        },
    )
    listed = await client.get("/api/v1/profile/memory", headers=headers)

    assert created.status_code == 201
    assert created.json()["user_id"] == USER_A_ID
    assert created.json()["source"] == "USER_REPORTED"
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [created.json()["id"]]


@pytest.mark.asyncio
async def test_memory_update_and_delete(api_client):
    client, _, settings = api_client
    headers = auth_headers(USER_A_ID, "student-a@example.com", settings)
    created = await client.post(
        "/api/v1/profile/memory",
        headers=headers,
        json={"category": "learning_preference", "key": "style", "value": "videos"},
    )

    updated = await client.patch(
        f"/api/v1/profile/memory/{created.json()['id']}",
        headers=headers,
        json={"value": "hands-on exercises", "confidence": 0.9},
    )
    deleted = await client.delete(
        f"/api/v1/profile/memory/{created.json()['id']}", headers=headers
    )
    listed = await client.get("/api/v1/profile/memory", headers=headers)

    assert updated.status_code == 200
    assert updated.json()["value"] == "hands-on exercises"
    assert deleted.status_code == 204
    assert listed.json() == []


@pytest.mark.asyncio
async def test_memory_isolation_prevents_cross_user_update_and_delete(api_client):
    client, memories, settings = api_client
    now = datetime.now(UTC)
    memories.memories[MEMORY_B_ID] = UserMemoryInDB(
        _id=MEMORY_B_ID,
        user_id=USER_B_ID,
        category="career_goal",
        key="role",
        value="Data analyst",
        source="USER_REPORTED",
        created_at=now,
        updated_at=now,
    )
    headers_a = auth_headers(USER_A_ID, "student-a@example.com", settings)

    update = await client.patch(
        f"/api/v1/profile/memory/{MEMORY_B_ID}", headers=headers_a, json={"value": "changed"}
    )
    delete = await client.delete(f"/api/v1/profile/memory/{MEMORY_B_ID}", headers=headers_a)
    listed = await client.get("/api/v1/profile/memory", headers=headers_a)

    assert update.status_code == 404
    assert delete.status_code == 404
    assert listed.json() == []
    assert MEMORY_B_ID in memories.memories


@pytest.mark.asyncio
async def test_memory_rejects_invalid_category_source_and_id(api_client):
    client, _, settings = api_client
    headers = auth_headers(USER_A_ID, "student-a@example.com", settings)

    invalid_category = await client.post(
        "/api/v1/profile/memory",
        headers=headers,
        json={"category": "untrusted", "key": "x", "value": "x"},
    )
    invalid_source = await client.post(
        "/api/v1/profile/memory",
        headers=headers,
        json={"category": "career_goal", "key": "x", "value": "x", "source": "unknown"},
    )
    invalid_id = await client.delete("/api/v1/profile/memory/not-an-object-id", headers=headers)

    assert invalid_category.status_code == 422
    assert invalid_source.status_code == 422
    assert invalid_id.status_code == 422
