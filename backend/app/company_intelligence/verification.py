from datetime import timedelta

from app.models.company_intelligence import EvidenceClaim, SourceType, VerificationStatus


def verify_claim(claim: EvidenceClaim, review_days: int) -> EvidenceClaim:
    """Conservative deterministic verification; never elevates generated or community claims."""
    claim.next_review_at = claim.collected_at + timedelta(days=review_days)
    if claim.source_type in {SourceType.OFFICIAL_COMPANY, SourceType.OFFICIAL_JOB_POSTING, SourceType.OFFICIAL_DOCUMENTATION}:
        claim.verification_status = VerificationStatus.HIGH_CONFIDENCE
        claim.confidence = max(claim.confidence, 0.8)
    elif claim.source_type == SourceType.REPUTABLE_SOURCE:
        claim.verification_status = VerificationStatus.MEDIUM_CONFIDENCE
        claim.confidence = max(claim.confidence, 0.6)
    else:
        claim.verification_status = VerificationStatus.UNVERIFIED
        claim.confidence = min(claim.confidence, 0.4)
    return claim


def mark_conflicts(claims: list[EvidenceClaim]) -> list[EvidenceClaim]:
    groups: dict[tuple[str, str | None, str], list[EvidenceClaim]] = {}
    for claim in claims:
        groups.setdefault((claim.company_id, claim.role_id, claim.claim_key), []).append(claim)
    for group in groups.values():
        if len({claim.claim_text.strip().lower() for claim in group}) > 1:
            for claim in group:
                claim.verification_status = VerificationStatus.CONFLICTING
    return claims
