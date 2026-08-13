from datetime import UTC, datetime
import pytest
from app.learning.catalog import ROLE_SKILL_REQUIREMENTS, SKILLS_BY_ID
from app.models.common import MasteryState, MemorySource, SkillSource
from app.models.learning import ActivityState
from app.models.user import UserInDB
from app.db.repositories.user_skill_progress_repository import UserSkillProgressRepository
from app.services.learning_service import calculate_skill_gaps, order_learning_stages, LearningService
from tests.fake_mongo import FakeDatabase

def test_catalog_is_small_extensible_and_contains_graph_metadata():
    assert 10 < len(SKILLS_BY_ID) < 30
    assert SKILLS_BY_ID["apis"].prerequisites == ["http", "programming_fundamentals"]
    assert SKILLS_BY_ID["apis"].active and SKILLS_BY_ID["apis"].version == "1.0"

def test_role_skill_mapping_has_expected_proficiency():
    assert ROLE_SKILL_REQUIREMENTS["backend_developer"]["apis"] == 3
    assert ROLE_SKILL_REQUIREMENTS["frontend_developer"]["html"] == 3

@pytest.mark.asyncio
async def test_user_skill_creation_has_safe_unverified_defaults():
    item = await UserSkillProgressRepository(FakeDatabase()).create_or_get("u1", "python")
    assert item.current_level == 0 and item.source == SkillSource.USER_REPORTED
    assert item.status == MasteryState.NOT_STARTED and item.confidence == 0

def test_gap_calculation_and_priority_are_deterministic():
    gaps = calculate_skill_gaps("backend_developer", {})
    assert gaps[0].priority >= gaps[-1].priority
    assert gaps[0].gap_size == gaps[0].required_level
    assert calculate_skill_gaps("backend_developer", {}) == gaps

def test_prerequisites_are_topologically_ordered():
    gaps = calculate_skill_gaps("backend_developer", {})
    positions = {stage.skill_id: index for index, stage in enumerate(order_learning_stages(gaps))}
    for stage in order_learning_stages(gaps):
        for prerequisite in stage.prerequisites:
            if prerequisite in positions: assert positions[prerequisite] < positions[stage.skill_id]

class _Roles:
    async def get_for_user(self, _):
        role = type("Role", (), {"role": type("Selected", (), {"role_id": "backend_developer"})()})()
        return role
class _Progress:
    async def list_for_user(self, _): return []
class _Plans:
    async def save(self, plan): return plan.model_copy(update={"id": "plan-1"})

@pytest.mark.asyncio
async def test_learning_plan_is_personalized_to_selected_role_and_dependencies():
    service = LearningService(None, _Progress(), _Roles(), _Plans(), None, None)
    plan = await service.plan("u1")
    assert plan.target_role == "backend_developer"
    assert plan.stages and plan.estimated_effort_hours > 0

@pytest.mark.asyncio
async def test_ai_inferred_source_is_distinct_from_verified_state():
    repo = UserSkillProgressRepository(FakeDatabase()); await repo.create_or_get("u1", "python")
    updated = await repo.update_details("u1", "python", {"source": SkillSource.AI_INFERRED.value, "status": MasteryState.LEARNING.value})
    assert updated.source == SkillSource.AI_INFERRED and updated.status != MasteryState.MASTERED
