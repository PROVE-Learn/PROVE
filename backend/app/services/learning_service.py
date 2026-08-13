from datetime import UTC, datetime
from fastapi import HTTPException, status
from app.learning.catalog import SKILLS_BY_ID, role_requirements, ROLE_SKILL_REQUIREMENTS
from app.models.common import MasteryState, MemoryCategory, MemorySource, SkillSource
from app.models.learning import ActivityState, AdaptiveRoadmap, LearningActivity, LearningPlan, LearningStage, MentorSummary, ProgressItem, SkillGap, WeeklyMentorPlan, WeeklyMilestone
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

    @staticmethod
    def _context_from_user(user=None) -> tuple[str, str, str, list[str]]:
        if user is None:
            return "", "", "", []
        preferences = getattr(user, "preferences", None)
        if preferences is None:
            return "", "", "", []
        learning_style = (preferences.learning_style or "").strip().lower()
        available_study_time = (preferences.available_study_time or "").strip().lower()
        preferred_difficulty = (preferences.preferred_difficulty or "").strip().lower()
        learning_goals = [goal.strip() for goal in (preferences.learning_goals or []) if goal and goal.strip()]
        return learning_style, available_study_time, preferred_difficulty, learning_goals

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

    async def next_activity(self, user_id: str) -> LearningActivity:
        role = await self.roles.get_for_user(user_id)
        role_id = role.role.role_id if role else "machine_learning_engineer"
        gaps = await self.gaps(user_id) if role else calculate_skill_gaps(role_id, {})
        skill_id = gaps[0].skill_id if gaps else "python"
        activity_id = f"intro-{skill_id}"
        activity = self.activity(activity_id)
        prior = await self.activity_progress.get(user_id, activity_id)
        if prior:
            activity = activity.model_copy(update={"state": prior.get("state", ActivityState.NOT_STARTED)})
        return activity

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

    async def mentor_summary(self, user_id: str, user=None) -> MentorSummary:
        role = await self.roles.get_for_user(user_id)
        role_id = role.role.role_id if role else "machine_learning_engineer"
        gaps = await self.gaps(user_id) if role else calculate_skill_gaps(role_id, {})
        top_gaps = [gap.skill_name for gap in gaps[:3]] or ["Python", "statistics", "machine learning"]
        learning_style, available_study_time, preferred_difficulty, learning_goals = self._context_from_user(user)

        style_hint = ""
        if learning_style:
            style_hint = f"Keep the rhythm {learning_style} so you stay engaged; "
        if available_study_time:
            style_hint += f"work in {available_study_time} blocks. "
        elif preferred_difficulty:
            style_hint += f"start at a {preferred_difficulty} pace. "

        if learning_goals:
            normalized = {gap.lower() for gap in top_gaps}
            matched = [goal for goal in learning_goals if goal.lower() in normalized][:3]
            if matched:
                top_gaps = matched

        project_map = {
            "machine_learning_engineer": [
                "Build an end-to-end churn prediction project with preprocessing, feature engineering, model training, evaluation, and deployment API.",
                "Create a recommendation system project with offline metrics, ranking evaluation, and a simple serving layer.",
                "Ship a real-time fraud or demand forecasting model with dashboarding and deployment notes."
            ],
            "data_analyst": [
                "Build a KPI dashboard from raw sales or product data.",
                "Create a SQL + Python data cleaning workflow with business reporting.",
                "Implement hypothesis testing on real data and present findings clearly."
            ],
            "backend_developer": [
                "Build a small API service with auth, database storage, and tests.",
                "Create a production-ready task service with validation and deployment notes.",
                "Ship a background job pipeline with monitoring and observability."
            ],
        }

        project_recommendations = project_map.get(role_id, [
            "Build a small full-stack product that solves one real user problem.",
            "Package your work in a portfolio-ready repository with docs and a demo."
        ])

        focus = (
            f"{style_hint}Focus this week on {', '.join(top_gaps[:2])} while building one end-to-end project to turn theory into proof."
            if top_gaps
            else f"{style_hint}Focus this week on fundamentals and one small portfolio project."
        )

        next_steps = [
            f"Study the highest-priority gap: {top_gaps[0]}.",
            "Complete one small project milestone every 3–4 days.",
            "Document outputs and review what is weak before moving to the next topic."
        ]
        if learning_goals:
            next_steps.insert(0, f"Keep your personal goal in view: {', '.join(learning_goals[:2])}.")

        return MentorSummary(
            user_id=user_id,
            target_role=role_id,
            weekly_focus=focus,
            top_gaps=top_gaps,
            recommended_projects=project_recommendations,
            next_steps=next_steps,
        )

    async def mentor_week(self, user_id: str, user=None) -> WeeklyMentorPlan:
        summary = await self.mentor_summary(user_id, user)
        milestone_tasks = [
            ("Day 1", "Foundation", f"Review {summary.top_gaps[0]} and complete a focused study block.", "You can explain the core idea and map one real use case."),
            ("Day 2", "Practice", f"Solve 2–3 small exercises on {summary.top_gaps[0]} and {summary.top_gaps[1] if len(summary.top_gaps) > 1 else summary.top_gaps[0]}.", "You can correctly implement the concept without notes."),
            ("Day 3", "Project", summary.recommended_projects[0], "A small working artifact is ready to show in your portfolio."),
            ("Day 4", "Review", f"Check your weak points in {summary.top_gaps[0]} and revise the mistakes.", "You can explain the errors and avoid them next time."),
            ("Day 5", "Delivery", "Write a short progress update and prepare the next milestone for the following week.", "You have a visible record of measurable output and learning."),
        ]
        return WeeklyMentorPlan(
            user_id=user_id,
            target_role=summary.target_role,
            weekly_focus=summary.weekly_focus,
            milestones=[WeeklyMilestone(day=day, objective=objective, task=task, outcome=outcome) for day, objective, task, outcome in milestone_tasks],
        )

    async def save_weekly_plan(self, user_id: str, user=None):
        """Generate the weekly plan and persist it when a weekly plan repository is available."""
        plan = await self.mentor_week(user_id, user)
        serialized = plan.model_dump(by_alias=False)
        # include metadata container for completed milestones
        serialized.setdefault("completed_milestones", [])
        # prefer an injected weekly plan repo if present
        weekly_repo = getattr(self, "weekly_plans", None)
        if weekly_repo is None and hasattr(self.plans, "save_weekly"):
            weekly_repo = self.plans
        if weekly_repo and hasattr(weekly_repo, "save_weekly"):
            return await weekly_repo.save_weekly(serialized)
        # fallback: return the generated plan without persistence
        return serialized

    async def get_weekly_plan(self, user_id: str, user=None):
        weekly_repo = getattr(self, "weekly_plans", None)
        if weekly_repo is None and hasattr(self.plans, "get_for_user"):
            weekly_repo = self.plans
        if weekly_repo and hasattr(weekly_repo, "get_for_user"):
            return await weekly_repo.get_for_user(user_id)
        # no persistence configured
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No weekly plan found for user")

    async def delete_weekly_plan(self, user_id: str):
        weekly_repo = getattr(self, "weekly_plans", None)
        if weekly_repo is None and hasattr(self.plans, "delete_for_user"):
            weekly_repo = self.plans
        if weekly_repo and hasattr(weekly_repo, "delete_for_user"):
            result = await weekly_repo.delete_for_user(user_id)
            if result:
                return True
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weekly plan not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Weekly plan persistence not configured")

    async def complete_weekly_milestone(self, user_id: str, day: str):
        weekly_repo = getattr(self, "weekly_plans", None)
        if weekly_repo is None and hasattr(self.plans, "mark_milestone_complete"):
            weekly_repo = self.plans
        if weekly_repo and hasattr(weekly_repo, "mark_milestone_complete"):
            return await weekly_repo.mark_milestone_complete(user_id, day)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Weekly plan persistence not configured")

    async def adaptive_roadmap(self, user_id: str, user=None) -> AdaptiveRoadmap:
        role = await self.roles.get_for_user(user_id)
        role_id = role.role.role_id if role else "machine_learning_engineer"
        gaps = await self.gaps(user_id) if role else calculate_skill_gaps(role_id, {})
        top_gap_names = [gap.skill_name for gap in gaps[:3]] or ["Python", "statistics", "machine learning"]
        learning_style, available_study_time, preferred_difficulty, learning_goals = self._context_from_user(user)

        adjustments = [
            f"Increase project time for {top_gap_names[0]} and its application in real work.",
            "Keep one project milestone every 3–4 days instead of spreading study across too many topics.",
        ]
        if learning_style:
            adjustments.insert(0, f"Match your {learning_style} learning style by building a small hands-on example before theory review.")
        if available_study_time:
            adjustments.append(f"Keep each session within {available_study_time} so the plan stays realistic and sustainable.")
        if learning_goals:
            adjustments.append(f"Tie each milestone back to your personal learning goals: {', '.join(learning_goals[:2])}.")

        if role_id == "machine_learning_engineer":
            focus = "Prioritize Python, data preparation, and model-building fundamentals before deeper optimization."
            next_milestone = "Finish one end-to-end preprocessing + model training project with evaluation and a short write-up."
        elif role_id == "backend_developer":
            focus = "Prioritize APIs, database design, and deployment reliability."
            next_milestone = "Build and deploy a small service with reliable auth, database storage, and tests."
        else:
            focus = f"Focus on {', '.join(top_gap_names[:2])} and devote the next cycle to one portfolio artifact."
            next_milestone = f"Complete a small portfolio project that demonstrates {top_gap_names[0]} in practice."

        return AdaptiveRoadmap(
            user_id=user_id,
            target_role=role_id,
            focus=focus,
            adjustments=adjustments,
            next_milestone=next_milestone,
        )
