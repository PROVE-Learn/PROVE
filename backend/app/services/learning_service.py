from datetime import UTC, datetime
from fastapi import HTTPException, status
from app.learning.catalog import SKILLS_BY_ID, role_requirements, ROLE_SKILL_REQUIREMENTS
from app.models.common import MasteryState, MemoryCategory, MemorySource, SkillSource
from app.models.learning import ActivityState, LearningActivity, LearningPlan, LearningStage, ProgressItem, SkillGap
from app.models.memory import MemoryCreate

def calculate_skill_gaps(role_id, progress):
    gaps = []
    requirements = role_requirements(role_id)
    for skill_id, required in requirements.items():
        skill = SKILLS_BY_ID[skill_id]; item = progress.get(skill_id)
        current = item.current_level if item else 0; size = max(0, required - current)
        if size:
            gaps.append(SkillGap(skill_id=skill_id, skill_name=skill.name, current_level=current, required_level=required, gap_size=size, priority=size * required, prerequisites=skill.prerequisites, reason=f"{skill.name} is required for the selected {role_id} role and is {size} level(s) below target."))
    return sorted(gaps, key=lambda gap: (-gap.priority, gap.skill_id))

def order_learning_stages(gaps):
    wanted = {gap.skill_id for gap in gaps}; ordered = []; visiting = set(); visited = set()
    def visit(skill_id):
        if skill_id in visited: return
        if skill_id in visiting: raise ValueError("Cyclic skill prerequisites")
        visiting.add(skill_id)
        for prerequisite in SKILLS_BY_ID[skill_id].prerequisites:
            if prerequisite in wanted: visit(prerequisite)
        visiting.remove(skill_id); visited.add(skill_id)
        ordered.append(LearningStage(skill_id=skill_id, title=SKILLS_BY_ID[skill_id].name, prerequisites=SKILLS_BY_ID[skill_id].prerequisites, estimated_effort_hours=max(1, SKILLS_BY_ID[skill_id].difficulty * 2)))
    for gap in gaps: visit(gap.skill_id)
    return ordered

class LearningService:
    def __init__(self, skill_repo, progress_repo, role_repo, plan_repo, activity_progress_repo, memory_repo):
        self.skills, self.progress, self.roles, self.plans, self.activity_progress, self.memory = skill_repo, progress_repo, role_repo, plan_repo, activity_progress_repo, memory_repo
    async def list_skills(self): return [skill for skill in SKILLS_BY_ID.values() if skill.active]
    async def get_skill(self, skill_id):
        skill = SKILLS_BY_ID.get(skill_id)
        if not skill or not skill.active: raise HTTPException(status_code=404, detail="Skill not found")
        return skill
    async def gaps(self, user_id):
        role = await self.roles.get_for_user(user_id)
        if not role: return []
        progress = {item.skill_id: item for item in await self.progress.list_for_user(user_id)}
        return calculate_skill_gaps(role.role.role_id, progress)
    async def plan(self, user_id):
        role = await self.roles.get_for_user(user_id)
        if not role: raise HTTPException(status_code=400, detail="Select a target role first")
        gaps = await self.gaps(user_id); stages = order_learning_stages(gaps)
        plan = LearningPlan(user_id=user_id, target_role=role.role.role_id, gaps=gaps, stages=stages, estimated_effort_hours=sum(stage.estimated_effort_hours for stage in stages))
        return await self.plans.save(plan)

    async def plan_for_company_role(self, user_id: str, company_id: str, role_id: str, company_intel_service) -> LearningPlan:
        # Use company intelligence to extract role-specific skill signals
        skills = await company_intel_service.extract_role_skills(company_id, role_id)
        progress = {item.skill_id: item for item in await self.progress.list_for_user(user_id)}
        gaps: list[SkillGap] = []
        for skill_id in skills:
            if skill_id not in SKILLS_BY_ID:
                continue
            skill = SKILLS_BY_ID[skill_id]
            item = progress.get(skill_id)
            current = item.current_level if item else 0
            required = ROLE_SKILL_REQUIREMENTS.get(role_id, {}).get(skill_id, 3)
            size = max(0, required - current)
            if size:
                gaps.append(
                    SkillGap(
                        skill_id=skill_id,
                        skill_name=skill.name,
                        current_level=current,
                        required_level=required,
                        gap_size=size,
                        priority=size * required,
                        prerequisites=skill.prerequisites,
                        reason=f"{skill.name} was inferred from company evidence for {role_id} and is {size} level(s) below target.",
                    )
                )
        stages = order_learning_stages(gaps) if gaps else []
        plan = LearningPlan(user_id=user_id, target_role=role_id, gaps=gaps, stages=stages, estimated_effort_hours=sum(stage.estimated_effort_hours for stage in stages))
        return await self.plans.save(plan)
    def activity(self, activity_id):
        skill_id = activity_id.removeprefix("intro-")
        skill = SKILLS_BY_ID.get(skill_id)
        if not skill or not activity_id.startswith("intro-"): raise HTTPException(status_code=404, detail="Activity not found")
        return LearningActivity(activity_id=activity_id, title=f"Build skill: {skill.name}", description=f"A curated starting activity for {skill.name}; completion is not mastery.", skill_id=skill_id, activity_type="exercise", difficulty=skill.difficulty, estimated_effort_hours=max(1, skill.difficulty), prerequisites=skill.prerequisites, source="PROVE curated foundation")
    async def start(self, user_id, activity_id):
        activity = self.activity(activity_id); prior = await self.activity_progress.get(user_id, activity_id)
        if prior and prior.get("state") == ActivityState.COMPLETED: return activity.model_copy(update={"state": ActivityState.COMPLETED})
        await self.activity_progress.save(user_id, activity_id, ActivityState.STARTED)
        await self.memory.create(user_id, MemoryCreate(category=MemoryCategory.LEARNING_PREFERENCE, key="learning_activity_started", value={"activity_id": activity_id}, source=MemorySource.SYSTEM_OBSERVED, confidence=1.0))
        return activity.model_copy(update={"state": ActivityState.STARTED})
    async def complete(self, user_id, activity_id, evidence):
        activity = self.activity(activity_id); prior = await self.activity_progress.get(user_id, activity_id)
        if not prior or prior.get("state") != ActivityState.STARTED: raise HTTPException(status_code=409, detail="Activity must be started first")
        if not evidence: raise HTTPException(status_code=422, detail="Evidence is required to complete an activity")
        await self.activity_progress.save(user_id, activity_id, ActivityState.COMPLETED, evidence)
        item = await self.progress.create_or_get(user_id, activity.skill_id)
        await self.progress.update_details(user_id, activity.skill_id, {"current_level": max(item.current_level, min(item.target_level, item.current_level + 1)), "evidence": item.evidence + evidence, "source": SkillSource.SYSTEM_OBSERVED.value, "confidence": max(item.confidence, .6), "status": MasteryState.DEMONSTRATED.value})
        await self.memory.create(user_id, MemoryCreate(category=MemoryCategory.COMPLETED_ACTIVITY, key="learning_activity_completed", value={"activity_id": activity_id, "skill_id": activity.skill_id, "evidence": evidence}, source=MemorySource.SYSTEM_OBSERVED, confidence=.8))
        return activity.model_copy(update={"state": ActivityState.COMPLETED})
    async def progress_view(self, user_id):
        return [ProgressItem(skill_id=item.skill_id, current_level=item.current_level, target_level=item.target_level, progress=item.current_level / item.target_level if item.target_level else 1, status=item.status, evidence=item.evidence) for item in await self.progress.list_for_user(user_id)]
