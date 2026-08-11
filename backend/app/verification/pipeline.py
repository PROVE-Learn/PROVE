from dataclasses import dataclass
from typing import Any, Literal

from app.models.common import ConfidenceLevel
from app.models.verification import HumanReviewItemCreate, VerificationRecordCreate
from app.verification.policy import VerificationPolicy, get_verification_policy


GateDecision = Literal["PASS", "BLOCK", "DEFER", "REVIEW"]


@dataclass
class VerificationResult:
    passed: bool
    confidence: ConfidenceLevel
    gate_decision: GateDecision
    failure_reason: str | None = None
    computed_result: str | None = None
    declared_result: str | None = None


class VerificationPipeline:
    """Milestone 1 skeleton: logs and records verification attempts."""

    def __init__(
        self,
        verification_repo,
        review_queue_repo,
        policy: VerificationPolicy | None = None,
    ) -> None:
        self._verification_repo = verification_repo
        self._review_queue_repo = review_queue_repo
        self._policy = policy or get_verification_policy()

    async def verify(
        self,
        verification_type: str,
        entity_type: str,
        entity_id: str | None,
        input_snapshot: dict[str, Any],
        *,
        computed_result: str | None = None,
        declared_result: str | None = None,
        passed: bool = True,
        failure_reason: str | None = None,
        confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED,
        queue_for_review: bool = False,
        review_reason: str | None = None,
    ) -> VerificationResult:
        gate_decision: GateDecision
        if passed:
            if confidence in (ConfidenceLevel.VERIFIED, ConfidenceLevel.HIGH_CONFIDENCE):
                gate_decision = "PASS"
            elif confidence == ConfidenceLevel.MEDIUM_CONFIDENCE:
                gate_decision = "PASS"
            elif queue_for_review:
                gate_decision = "REVIEW"
            else:
                gate_decision = "PASS"
        elif queue_for_review:
            gate_decision = "REVIEW"
        else:
            gate_decision = "BLOCK"

        record = VerificationRecordCreate(
            entity_type=entity_type,
            entity_id=entity_id,
            verification_type=verification_type,
            input_snapshot=input_snapshot,
            computed_result=computed_result,
            declared_result=declared_result,
            passed=passed,
            failure_reason=failure_reason,
            confidence=confidence,
        )
        await self._verification_repo.create(record)

        if queue_for_review and review_reason:
            await self._review_queue_repo.create(
                HumanReviewItemCreate(
                    item_type=verification_type,
                    reference_collection=entity_type,
                    reference_id=entity_id,
                    content_snapshot=input_snapshot,
                    reason=review_reason,
                )
            )
            if not passed:
                gate_decision = "REVIEW"

        return VerificationResult(
            passed=passed,
            confidence=confidence,
            gate_decision=gate_decision,
            failure_reason=failure_reason,
            computed_result=computed_result,
            declared_result=declared_result,
        )

    async def pass_through(
        self,
        verification_type: str,
        entity_type: str,
        entity_id: str | None = None,
        input_snapshot: dict | None = None,
    ) -> VerificationResult:
        """M1 placeholder for future domain-specific verifiers."""
        return await self.verify(
            verification_type=verification_type,
            entity_type=entity_type,
            entity_id=entity_id,
            input_snapshot=input_snapshot or {},
            passed=True,
            confidence=ConfidenceLevel.UNVERIFIED,
        )
