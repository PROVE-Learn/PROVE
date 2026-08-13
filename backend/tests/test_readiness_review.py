from datetime import UTC, datetime

import httpx
import pytest

from app.auth.jwt import create_access_token
from app.career_discovery.catalog import ROLE_BY_ID
from app.config import Settings
from app.dependencies import get_readiness_review_service, get_settings_dep, get_user_repo
from app.main import create_app
from app.models.common import MasteryState, MemoryCategory, UserRole
from app.models.company_intelligence import Company, VerificationStatus
from app.models.readiness import ReadinessReview
from app.models.user import UserInDB, UserProfile
from app.services.readiness_review_service import ReadinessReviewService


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
        self.items = items
        self.calls = []

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

    async def list_for_company(self, company_id, role_id):
        return self.items.get((company_id, role_id), [])


class Memories:
    def __init__(self, items):
        self.items = items
        self.calls = []

    async def list_for_user(self, user_id):
        self.calls.append(user_id)
        return self.items.get(user_id, [])


def selection(user_id: str):
    return type("Selection", (), {"user_id": user_id, "role": ROLE_BY_ID["backend_developer"]})()


def progress(skill_id, level, status, evidence=None):
    return type(
        "ProgressItem",
        (),
        {
            "skill_id": skill_id,
            "current_level": level,
            "status": status,
            "evidence": evidence or [],
            "evidence_records": [],
        },
    )()


def memory(skill_id):
    return type(
        "Memory",
        (),
        {
            "category": MemoryCategory.COMPLETED_ACTIVITY,
            "value": {"skill_id": skill_id},
        },
    )()


def claim(status):
    return type("Claim", (), {"verification_status": status})()


@pytest.mark.asyncio
async def test_review_distinguishes_demonstrated_learning_and_unverified_company_evidence():
    current_user = user("student", ["acme"])
    progress_repo = Progress(
        {
            "student": [
                progress("python", 3, MasteryState.DEMONSTRATED, ["exercise evidence"]),
                progress("apis", 2, MasteryState.LEARNING),
            ]
        }
    )
    memories = Memories({"student": [memory("python")]})
    service = ReadinessReviewService(
        Selections({"student": selection("student")}),
        progress_repo,
        Companies({"acme": Company(company_id="acme", name="Acme")} ),
        Claims(
            {
                ("acme", "backend_developer"): [
                    claim(VerificationStatus.HIGH_CONFIDENCE),
                    claim(VerificationStatus.UNVERIFIED),
                ]
            }
        ),
        memories,
    )

    review = await service.review(current_user)

    assert review.review_status == "NEEDS_EVIDENCE"
    assert [item.skill_id for item in review.demonstrated_learning] == ["python"]
    assert "apis" in {item.skill_id for item in review.missing_learning}
    assert review.company_evidence[0].trusted_evidence_count == 1
    assert review.company_evidence[0].unverified_evidence_count == 1
    assert review.completed_activity_count == 1
    assert progress_repo.calls == ["student"] and memories.calls == ["student"]


@pytest.mark.asyncio
async def test_review_marks_conflicting_company_evidence_for_review():
    service = ReadinessReviewService(
        Selections({"student": selection("student")} ),
        Progress({"student": []}),
        Companies({"acme": Company(company_id="acme", name="Acme")} ),
        Claims({("acme", "backend_developer"): [claim(VerificationStatus.CONFLICTING)]}),
        Memories({"student": []}),
    )

    review = await service.review(user("student", ["acme"]))

    assert review.review_status == "REVIEW_REQUIRED"
    assert review.company_evidence[0].conflicting_evidence_count == 1


class Users:
    def __init__(self, *items):
        self.items = {item.id: item for item in items}

    async def get_by_id(self, user_id):
        return self.items.get(user_id)


class ApiReviewService:
    def __init__(self):
        self.user_ids = []

    async def review(self, current_user):
        self.user_ids.append(current_user.id)
        return ReadinessReview(review_status="BLOCKED")


@pytest.mark.asyncio
async def test_readiness_review_api_requires_authentication_and_scopes_the_review_to_user():
    first, second = user("first"), user("second")
    settings = Settings(app_env="test", jwt_secret="test-secret-key-at-least-32-characters-long")
    review_service = ApiReviewService()
    app = create_app()
    app.dependency_overrides[get_settings_dep] = lambda: settings
    app.dependency_overrides[get_user_repo] = lambda: Users(first, second)
    app.dependency_overrides[get_readiness_review_service] = lambda: review_service
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
        assert (await client.get("/api/v1/readiness/review")).status_code == 401
        assert (
            await client.get("/api/v1/readiness/review", headers=headers[first.id])
        ).status_code == 200
        assert (
            await client.get("/api/v1/readiness/review", headers=headers[second.id])
        ).status_code == 200

    assert review_service.user_ids == ["first", "second"]
