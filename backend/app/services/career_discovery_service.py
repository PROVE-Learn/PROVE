from bson import ObjectId
from fastapi import HTTPException, status

from app.career_discovery.catalog import QUESTION_BY_ID, QUESTION_VERSION, QUESTIONS, ROLE_BY_ID, ROLES
from app.db.repositories.career_assessment_repository import CareerAssessmentRepository
from app.db.repositories.career_role_selection_repository import CareerRoleSelectionRepository
from app.db.repositories.user_memory_repository import UserMemoryRepository
from app.models.career import CareerAssessmentInDB, DimensionResult
from app.models.career_discovery import (
    AssessmentAnswerSubmission, AssessmentResult, CareerRecommendation, PublicDiscoveryQuestion,
    TargetRoleSelection, TargetRoleSelectionRequest,
)
from app.models.common import ConfidenceLevel, MemoryCategory, MemorySource
from app.models.memory import MemoryCreate
from app.models.user import UserInDB


class CareerDiscoveryService:
    def __init__(
        self,
        assessment_repo: CareerAssessmentRepository,
        selection_repo: CareerRoleSelectionRepository,
        memory_repo: UserMemoryRepository,
    ) -> None:
        self._assessment_repo = assessment_repo
        self._selection_repo = selection_repo
        self._memory_repo = memory_repo

    async def start(self, user_id: str) -> CareerAssessmentInDB:
        active = await self._assessment_repo.get_active_for_user(user_id)
        return active or await self._assessment_repo.create(user_id, QUESTION_VERSION)

    def questions(self) -> list[PublicDiscoveryQuestion]:
        return [
            PublicDiscoveryQuestion(
                id=q.id, category=q.category, text=q.text,
                options=[(option.id, option.text) for option in q.options], version=q.version, active=q.active,
            )
            for q in QUESTIONS
        ]

    async def get_assessment(self, user_id: str, assessment_id: str) -> CareerAssessmentInDB:
        assessment = await self._owned_assessment(user_id, assessment_id)
        return assessment

    async def submit_answers(
        self, user_id: str, assessment_id: str, submission: AssessmentAnswerSubmission
    ) -> CareerAssessmentInDB:
        assessment = await self._owned_assessment(user_id, assessment_id)
        if assessment.status != "in_progress":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assessment is complete")
        if len({answer.question_id for answer in submission.answers}) != len(submission.answers):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Duplicate answers")
        responses = {response["question_id"]: response for response in assessment.raw_responses}
        for answer in submission.answers:
            question = QUESTION_BY_ID.get(answer.question_id)
            if question is None or not any(option.id == answer.option_id for option in question.options):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid answer")
            responses[answer.question_id] = answer.model_dump()
        dimensions = self._dimensions(list(responses.values()))
        saved = await self._assessment_repo.save_answers(
            assessment_id, user_id, list(responses.values()), dimensions
        )
        if saved is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return saved

    async def complete(self, user_id: str, assessment_id: str) -> AssessmentResult:
        assessment = await self._owned_assessment(user_id, assessment_id)
        if assessment.status == "complete":
            return self._result(assessment)
        answered = {response["question_id"] for response in assessment.raw_responses}
        missing = sorted(set(QUESTION_BY_ID) - answered)
        if missing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All questions must be answered")
        completed = await self._assessment_repo.mark_complete(assessment_id, user_id)
        if completed is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        await self._memory_repo.create(user_id, MemoryCreate(
            category=MemoryCategory.ASSESSMENT_RESULT,
            key="career_discovery_completed",
            value={"assessment_id": completed.id, "dimensions": self._scores(completed)},
            source=MemorySource.ASSESSMENT_DERIVED,
            confidence=0.8,
        ))
        return self._result(completed)

    async def recommendations(self, user: UserInDB, assessment_id: str) -> list[CareerRecommendation]:
        assessment = await self._owned_assessment(user.id, assessment_id)
        if assessment.status != "complete":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complete assessment first")
        scores = self._scores(assessment)
        profile_terms = {term.lower() for term in user.profile.interests + user.profile.preferred_domains}
        profile_terms.update(skill.name.lower() for skill in user.profile.known_skills)
        recommendations = []
        for role in ROLES:
            role_dimensions = role.relevant_interests
            dimension_score = sum(scores.get(key, 0) for key in role_dimensions) / len(role_dimensions)
            matches = [term for term in profile_terms if term in {item.lower() for item in role_dimensions}]
            score = round(min(100, dimension_score * 0.8 + min(20, len(matches) * 10)), 2)
            evidence = [f"Assessment signal: {key} ({scores.get(key, 0):.0f}/100)" for key in role_dimensions if scores.get(key, 0) >= 50]
            evidence.extend(f"Profile evidence: {item}" for item in matches)
            missing = [skill for skill in role.core_skills if skill.lower() not in profile_terms]
            recommendations.append(CareerRecommendation(
                role=role, score=score, supporting_evidence=evidence or ["Limited supporting evidence so far"],
                missing_evidence=missing, confidence=ConfidenceLevel.HIGH_CONFIDENCE,
                recommended_next_experiment=f"Build a small {role.name} practice project.",
                explanation="Based on the available evidence, this is a starting point to explore, not a guarantee of fit.",
            ))
        return sorted(recommendations, key=lambda item: (-item.score, item.role.role_id))[:3]

    async def select_role(self, user: UserInDB, request: TargetRoleSelectionRequest) -> TargetRoleSelection:
        assessment = await self._owned_assessment(user.id, request.assessment_id)
        if assessment.status != "complete":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complete assessment first")
        role = ROLE_BY_ID.get(request.role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown role")
        recommendation = next(
            (item for item in await self.recommendations(user, request.assessment_id) if item.role.role_id == role.role_id), None
        )
        evidence = recommendation.supporting_evidence if recommendation else ["User selected this catalog role"]
        selection = await self._selection_repo.select(user.id, role, assessment.id, evidence)
        await self._memory_repo.create(user.id, MemoryCreate(
            category=MemoryCategory.CAREER_GOAL, key="selected_target_role", value=role.name,
            source=MemorySource.USER_REPORTED, confidence=1.0,
        ))
        return selection

    async def current_role(self, user_id: str) -> TargetRoleSelection | None:
        return await self._selection_repo.get_for_user(user_id)

    async def _owned_assessment(self, user_id: str, assessment_id: str) -> CareerAssessmentInDB:
        if not ObjectId.is_valid(assessment_id):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid assessment id")
        assessment = await self._assessment_repo.get_by_id(assessment_id, user_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return assessment

    @staticmethod
    def _dimensions(responses: list[dict]) -> dict[str, dict]:
        totals: dict[str, int] = {}
        counts: dict[str, int] = {}
        for response in responses:
            option = next(option for option in QUESTION_BY_ID[response["question_id"]].options if option.id == response["option_id"])
            for dimension, value in option.scores.items():
                totals[dimension] = totals.get(dimension, 0) + value
                counts[dimension] = counts.get(dimension, 0) + 1
        return {key: DimensionResult(score=totals[key] / (counts[key] * 2) * 100).model_dump() for key in totals}

    @staticmethod
    def _scores(assessment: CareerAssessmentInDB) -> dict[str, float]:
        return {key: result.score for key, result in assessment.dimensions.items()}

    def _result(self, assessment: CareerAssessmentInDB) -> AssessmentResult:
        return AssessmentResult(assessment_id=assessment.id, status=assessment.status, dimension_scores=self._scores(assessment), completed_at=assessment.completed_at)
