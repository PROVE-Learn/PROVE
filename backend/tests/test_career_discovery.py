from datetime import UTC, datetime

import httpx
import pytest

from app.api.routes.career_discovery import router
from app.auth.jwt import create_access_token
from app.career_discovery.catalog import QUESTIONS
from app.config import Settings
from app.db.repositories.career_assessment_repository import CareerAssessmentRepository
from app.dependencies import get_settings_dep, get_user_repo
from app.main import create_app
from app.models.career import CareerAssessmentInDB, DimensionResult
from app.models.common import MemorySource, UserRole
from app.models.memory import MemoryCreate
from app.models.user import ProfileSkill, UserInDB
from app.services.career_discovery_service import CareerDiscoveryService

USER_A = "64b64c3e5e4f88c9d4000101"
USER_B = "64b64c3e5e4f88c9d4000102"
ASSESSMENT_A = "64b64c3e5e4f88c9d4000111"


def user(user_id: str) -> UserInDB:
    now = datetime.now(UTC)
    return UserInDB(_id=user_id, email=f"{user_id}@example.com", password_hash="private", display_name="Student", created_at=now, updated_at=now, profile={"interests": ["backend"], "known_skills": [ProfileSkill(name="Python", level="intermediate")]})


class FakeAssessments:
    def __init__(self): self.items = {}
    async def get_active_for_user(self, user_id): return next((x for x in self.items.values() if x.user_id == user_id and x.status == "in_progress"), None)
    async def create(self, user_id, question_version):
        item = CareerAssessmentInDB(_id=ASSESSMENT_A, user_id=user_id, question_version=question_version, created_at=datetime.now(UTC)); self.items[item.id] = item; return item
    async def get_by_id(self, assessment_id, user_id=None):
        item = self.items.get(assessment_id); return item if item and (user_id is None or item.user_id == user_id) else None
    async def save_answers(self, assessment_id, user_id, responses, dimensions):
        item = await self.get_by_id(assessment_id, user_id)
        if not item or item.status != "in_progress": return None
        item.raw_responses = responses; item.dimensions = {k: DimensionResult.model_validate(v) for k, v in dimensions.items()}; return item
    async def mark_complete(self, assessment_id, user_id):
        item = await self.get_by_id(assessment_id, user_id)
        if not item or item.status != "in_progress": return None
        item.status = "complete"; item.completed_at = datetime.now(UTC); return item


class FakeSelections:
    def __init__(self): self.items = {}
    async def get_for_user(self, user_id): return self.items.get(user_id)
    async def select(self, user_id, role, assessment_id, evidence):
        from app.models.career_discovery import TargetRoleSelection
        item = TargetRoleSelection(_id="64b64c3e5e4f88c9d4000121", user_id=user_id, role=role, assessment_id=assessment_id, recommendation_evidence=evidence, selected_at=datetime.now(UTC)); self.items[user_id] = item; return item


class FakeMemories:
    def __init__(self): self.created = []
    async def create(self, user_id, memory: MemoryCreate): self.created.append((user_id, memory)); return memory


@pytest.fixture
def service():
    return CareerDiscoveryService(FakeAssessments(), FakeSelections(), FakeMemories())


def all_answers():
    return {"answers": [{"question_id": question.id, "option_id": question.options[0].id} for question in QUESTIONS]}


@pytest.mark.asyncio
async def test_assessment_creation_questions_and_scoring_metadata_boundary(service):
    assessment = await service.start(USER_A)
    questions = service.questions()

    assert assessment.status == "in_progress"
    assert len(questions) == 8
    assert {question.category for question in questions} >= {"interests", "strengths", "technical_orientation", "problem_solving"}
    assert not hasattr(questions[0].options[0], "scores")


@pytest.mark.asyncio
async def test_answer_submission_rejects_invalid_answers_and_scores_deterministically(service):
    assessment = await service.start(USER_A)
    from app.models.career_discovery import AssessmentAnswerSubmission
    invalid = AssessmentAnswerSubmission(answers=[{"question_id": "unknown", "option_id": "no"}])
    with pytest.raises(Exception) as exc: await service.submit_answers(USER_A, assessment.id, invalid)
    assert exc.value.status_code == 422
    submission = AssessmentAnswerSubmission(**all_answers())
    first = await service.submit_answers(USER_A, assessment.id, submission)
    second = await service.submit_answers(USER_A, assessment.id, submission)
    assert first.dimensions == second.dimensions
    assert first.dimensions["web"].score == pytest.approx(66.66666666666666)


@pytest.mark.asyncio
async def test_completion_results_and_assessment_derived_memory(service):
    assessment = await service.start(USER_A)
    from app.models.career_discovery import AssessmentAnswerSubmission
    with pytest.raises(Exception) as exc: await service.complete(USER_A, assessment.id)
    assert exc.value.status_code == 400
    await service.submit_answers(USER_A, assessment.id, AssessmentAnswerSubmission(**all_answers()))
    result = await service.complete(USER_A, assessment.id)
    memories = service._memory_repo.created
    assert result.status == "complete"
    assert result.dimension_scores["web"] == pytest.approx(66.66666666666666)
    assert memories[0][1].source == MemorySource.ASSESSMENT_DERIVED


@pytest.mark.asyncio
async def test_recommendations_are_multiple_and_deterministic(service):
    assessment = await service.start(USER_A)
    from app.models.career_discovery import AssessmentAnswerSubmission
    await service.submit_answers(USER_A, assessment.id, AssessmentAnswerSubmission(**all_answers()))
    await service.complete(USER_A, assessment.id)
    first = await service.recommendations(user(USER_A), assessment.id)
    second = await service.recommendations(user(USER_A), assessment.id)
    assert len(first) == 3
    assert [item.role.role_id for item in first] == [item.role.role_id for item in second]
    assert all("not a guarantee" in item.explanation for item in first)


@pytest.mark.asyncio
async def test_user_selection_overrides_recommendation_and_is_recorded_as_user_reported(service):
    assessment = await service.start(USER_A)
    from app.models.career_discovery import AssessmentAnswerSubmission, TargetRoleSelectionRequest
    await service.submit_answers(USER_A, assessment.id, AssessmentAnswerSubmission(**all_answers()))
    await service.complete(USER_A, assessment.id)
    selection = await service.select_role(user(USER_A), TargetRoleSelectionRequest(role_id="java_developer", assessment_id=assessment.id))
    assert selection.role.role_id == "java_developer"
    assert service._memory_repo.created[-1][1].source == MemorySource.USER_REPORTED


@pytest.mark.asyncio
async def test_assessment_user_isolation(service):
    assessment = await service.start(USER_A)
    from app.models.career_discovery import AssessmentAnswerSubmission, TargetRoleSelectionRequest
    with pytest.raises(Exception) as read: await service.get_assessment(USER_B, assessment.id)
    with pytest.raises(Exception) as update: await service.submit_answers(USER_B, assessment.id, AssessmentAnswerSubmission(**all_answers()))
    with pytest.raises(Exception) as selection:
        await service.select_role(
            user(USER_B),
            TargetRoleSelectionRequest(role_id="backend_developer", assessment_id=assessment.id),
        )
    assert read.value.status_code == 404
    assert update.value.status_code == 404
    assert selection.value.status_code == 404


class FakeUsers:
    async def get_by_id(self, user_id): return user(user_id)


@pytest.mark.asyncio
async def test_career_discovery_api_requires_authentication():
    app = create_app()
    app.dependency_overrides[get_user_repo] = lambda: FakeUsers()
    app.dependency_overrides[get_settings_dep] = lambda: Settings(jwt_secret="test-secret-key-at-least-32-characters-long")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/career-discovery/questions")
    assert response.status_code == 401
