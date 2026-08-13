from app.learning.catalog import SKILLS_BY_ID, role_requirements
from app.models.common import MasteryState, MemoryCategory
from app.models.company_intelligence import VerificationStatus
from app.models.readiness import (
    CompanyEvidenceReview,
    LearningEvidenceReview,
    ReadinessProvenance,
    ReadinessReview,
)
from app.models.user import UserInDB


class ReadinessReviewService:
    """Applies deterministic evidence-quality checks to a user's readiness data."""

    def __init__(self, selections, progress, companies, claims, memories) -> None:
        self._selections = selections
        self._progress = progress
        self._companies = companies
        self._claims = claims
        self._memories = memories

    async def review(self, user: UserInDB) -> ReadinessReview:
        selection = await self._selections.get_for_user(user.id)
        memories = await self._memories.list_for_user(user.id)
        completed_skills = self._completed_skills(memories)
        completed_activity_count = sum(
            memory.category == MemoryCategory.COMPLETED_ACTIVITY for memory in memories
        )
        if selection is None:
            return ReadinessReview(
                review_status="BLOCKED",
                completed_activity_count=completed_activity_count,
                provenance=self._provenance(None, 0, 0, memories),
            )

        progress = {item.skill_id: item for item in await self._progress.list_for_user(user.id)}
        demonstrated, missing = self._learning_reviews(
            selection.role.role_id, progress, completed_skills
        )
        company_evidence = await self._company_reviews(user, selection.role.role_id)
        return ReadinessReview(
            review_status=self._status(missing, company_evidence),
            target_role_id=selection.role.role_id,
            demonstrated_learning=demonstrated,
            missing_learning=missing,
            company_evidence=company_evidence,
            completed_activity_count=completed_activity_count,
            provenance=self._provenance(selection, len(progress), len(company_evidence), memories),
        )

    @staticmethod
    def _completed_skills(memories) -> set[str]:
        return {
            memory.value["skill_id"]
            for memory in memories
            if memory.category == MemoryCategory.COMPLETED_ACTIVITY
            and isinstance(memory.value, dict)
            and isinstance(memory.value.get("skill_id"), str)
        }

    @staticmethod
    def _learning_reviews(role_id, progress, completed_skills):
        demonstrated, missing = [], []
        for skill_id, required_level in role_requirements(role_id).items():
            item = progress.get(skill_id)
            current_level = item.current_level if item else 0
            evidence_count = len(item.evidence) + len(item.evidence_records) if item else 0
            demonstrated_skill = (
                item is not None
                and item.status in {MasteryState.DEMONSTRATED, MasteryState.MASTERED}
                and current_level >= required_level
                and (evidence_count > 0 or skill_id in completed_skills)
            )
            review = LearningEvidenceReview(
                skill_id=skill_id,
                skill_name=SKILLS_BY_ID[skill_id].name,
                current_level=current_level,
                required_level=required_level,
                evidence_status="DEMONSTRATED" if demonstrated_skill else "MISSING",
                evidence_count=evidence_count,
            )
            (demonstrated if demonstrated_skill else missing).append(review)
        return demonstrated, missing

    async def _company_reviews(self, user: UserInDB, role_id: str):
        reviews = []
        for company_id in user.profile.target_companies:
            company = await self._companies.get(company_id)
            if company is None:
                continue
            claims = await self._claims.list_for_company(company_id, role_id)
            reviews.append(
                CompanyEvidenceReview(
                    company_id=company.company_id,
                    company_name=company.name,
                    trusted_evidence_count=sum(
                        claim.verification_status
                        in {VerificationStatus.VERIFIED, VerificationStatus.HIGH_CONFIDENCE}
                        for claim in claims
                    ),
                    unverified_evidence_count=sum(
                        claim.verification_status
                        in {
                            VerificationStatus.UNVERIFIED,
                            VerificationStatus.LOW_CONFIDENCE,
                            VerificationStatus.MEDIUM_CONFIDENCE,
                        }
                        for claim in claims
                    ),
                    conflicting_evidence_count=sum(
                        claim.verification_status == VerificationStatus.CONFLICTING
                        for claim in claims
                    ),
                )
            )
        return reviews

    @staticmethod
    def _status(missing_learning, company_evidence) -> str:
        if any(item.conflicting_evidence_count for item in company_evidence):
            return "REVIEW_REQUIRED"
        if missing_learning or not any(item.trusted_evidence_count for item in company_evidence):
            return "NEEDS_EVIDENCE"
        return "READY_FOR_NEXT_STEP"

    @staticmethod
    def _provenance(selection, progress_count, company_count, memories):
        return [
            ReadinessProvenance(
                component="career_discovery",
                source="selected_target_role",
                record_count=int(selection is not None),
            ),
            ReadinessProvenance(
                component="learning",
                source="user_skill_progress_and_activity_memory",
                record_count=progress_count,
            ),
            ReadinessProvenance(
                component="company_intelligence",
                source="role_evidence_claims",
                record_count=company_count,
            ),
            ReadinessProvenance(
                component="structured_memory",
                source="completed_activity",
                record_count=len(memories),
            ),
        ]
