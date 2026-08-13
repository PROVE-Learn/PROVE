from app.learning.catalog import role_requirements
from app.models.common import MemoryCategory
from app.models.readiness import (
    CareerReadiness,
    ReadinessAction,
    ReadinessProvenance,
    TargetCompanyReadiness,
)
from app.models.user import UserInDB
from app.services.learning_service import calculate_skill_gaps


class ReadinessService:
    """Builds a user-scoped read model from existing career, learning, and company records."""

    def __init__(self, selections, progress, companies, claims, memories) -> None:
        self._selections = selections
        self._progress = progress
        self._companies = companies
        self._claims = claims
        self._memories = memories

    async def get(self, user: UserInDB) -> CareerReadiness:
        selection = await self._selections.get_for_user(user.id)
        memories = await self._memories.list_for_user(user.id)
        completed_activity_count = sum(
            memory.category == MemoryCategory.COMPLETED_ACTIVITY for memory in memories
        )
        gaps = []
        if selection:
            progress = {item.skill_id: item for item in await self._progress.list_for_user(user.id)}
            gaps = calculate_skill_gaps(selection.role.role_id, progress)

        target_companies = []
        for company_id in user.profile.target_companies:
            company = await self._companies.get(company_id)
            if company is None:
                continue
            claims = await self._claims.list_for_company(
                company_id, selection.role.role_id if selection else None
            )
            target_companies.append(
                TargetCompanyReadiness(
                    company_id=company.company_id,
                    name=company.name,
                    role_evidence_count=len(claims),
                )
            )

        score = self._score(selection, gaps, target_companies)
        return CareerReadiness(
            target_role_id=selection.role.role_id if selection else None,
            target_role_name=selection.role.name if selection else None,
            readiness_score=score,
            skill_gaps=gaps,
            completed_activity_count=completed_activity_count,
            target_companies=target_companies,
            next_actions=self._next_actions(selection, gaps, target_companies),
            provenance=self._provenance(selection, gaps, target_companies, memories),
        )

    @staticmethod
    def _score(selection, gaps, target_companies) -> int:
        if selection is None:
            return 0
        requirements = role_requirements(selection.role.role_id)
        required_levels = sum(requirements.values())
        remaining_levels = sum(gap.gap_size for gap in gaps)
        learning_score = round(70 * (required_levels - remaining_levels) / required_levels)
        company_score = min(10, len(target_companies) * 10)
        evidence_score = (
            10 if any(company.role_evidence_count for company in target_companies) else 0
        )
        return min(100, 10 + learning_score + company_score + evidence_score)

    @staticmethod
    def _next_actions(selection, gaps, target_companies) -> list[ReadinessAction]:
        if selection is None:
            return [
                ReadinessAction(
                    action="Select a target role",
                    detail=(
                        "Complete career discovery and select a role to generate "
                        "a readiness plan."
                    ),
                )
            ]

        actions = [
            ReadinessAction(
                action=f"Improve {gap.skill_name}",
                detail=f"Close the {gap.gap_size}-level gap required for {selection.role.name}.",
            )
            for gap in gaps[:2]
        ]
        if not target_companies:
            actions.append(
                ReadinessAction(
                    action="Add a target company",
                    detail="Track a company to connect role preparation with company evidence.",
                )
            )
        elif not any(company.role_evidence_count for company in target_companies):
            actions.append(
                ReadinessAction(
                    action="Review company evidence",
                    detail=(
                        "No saved evidence currently matches your selected role "
                        "at target companies."
                    ),
                )
            )
        return actions[:3] or [
            ReadinessAction(
                action="Maintain demonstrated skills",
                detail="Your selected role currently has no catalog skill gaps.",
            )
        ]

    @staticmethod
    def _provenance(selection, gaps, target_companies, memories) -> list[ReadinessProvenance]:
        return [
            ReadinessProvenance(
                component="career_discovery",
                source="selected_target_role",
                record_count=int(selection is not None),
            ),
            ReadinessProvenance(
                component="learning", source="user_skill_progress", record_count=len(gaps)
            ),
            ReadinessProvenance(
                component="company_intelligence",
                source="target_companies",
                record_count=len(target_companies),
            ),
            ReadinessProvenance(
                component="structured_memory", source="user_memories", record_count=len(memories)
            ),
        ]
