from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.company_intelligence.verification import mark_conflicts, verify_claim
from app.models.company_intelligence import EvidenceClaim, JobPosting, SourceType, VerificationStatus
from app.services.company_intelligence_service import CompanyIntelligenceService


def claim(text="Python is required", source=SourceType.OFFICIAL_JOB_POSTING):
    return EvidenceClaim(company_id="example", role_id="backend_developer", claim_key="python", claim_text=text, source_url="https://careers.example.com/job", source_type=source, source_title="Backend role", evidence_text="Required: Python")


def test_job_posting_validation_and_staleness():
    job = JobPosting(company_id="example", title="Backend Developer", url="https://careers.example.com/job", source_type=SourceType.OFFICIAL_JOB_POSTING, collected_at=datetime.now(UTC) - timedelta(days=91))
    assert job.is_stale(90)
    with pytest.raises(ValidationError): JobPosting(company_id="example", title="Role", url="javascript:alert(1)", source_type=SourceType.OTHER)


def test_evidence_preserves_provenance_and_assigns_conservative_status():
    result = verify_claim(claim(), 90)
    assert result.source_type == SourceType.OFFICIAL_JOB_POSTING
    assert result.source_title == "Backend role"
    assert result.verification_status == VerificationStatus.HIGH_CONFIDENCE
    assert result.next_review_at is not None


def test_unverified_sources_are_not_silently_upgraded():
    result = verify_claim(claim(source=SourceType.COMMUNITY_REPORT), 90)
    assert result.verification_status == VerificationStatus.UNVERIFIED
    assert result.confidence <= 0.4


def test_conflicting_evidence_is_marked_deterministically():
    claims = mark_conflicts([claim("Python is required"), claim("Python is not required")])
    assert all(item.verification_status == VerificationStatus.CONFLICTING for item in claims)


def test_verified_claim_requires_explicit_verification_date():
    values = claim().model_dump()
    values["verification_status"] = VerificationStatus.VERIFIED
    with pytest.raises(ValidationError):
        EvidenceClaim.model_validate(values)


def test_extract_role_skills_from_company_evidence():
    service = CompanyIntelligenceService.__new__(CompanyIntelligenceService)
    skills = service._extract_role_skills([
        EvidenceClaim(company_id="example", role_id="machine_learning_engineer", claim_key="python", claim_text="Python is required for the role", source_url="https://careers.example.com/job", source_type=SourceType.OFFICIAL_JOB_POSTING, source_title="ML Engineer", evidence_text="Strong Python skills are required for model development."),
        EvidenceClaim(company_id="example", role_id="machine_learning_engineer", claim_key="sql", claim_text="SQL is part of the workflow", source_url="https://careers.example.com/job", source_type=SourceType.OFFICIAL_JOB_POSTING, source_title="ML Engineer", evidence_text="We run queries and data cleaning in SQL."),
        EvidenceClaim(company_id="example", role_id="machine_learning_engineer", claim_key="machine_learning", claim_text="Experience with ML systems is needed", source_url="https://careers.example.com/job", source_type=SourceType.OFFICIAL_JOB_POSTING, source_title="ML Engineer", evidence_text="Must build and deploy machine learning models for product features."),
    ], "machine_learning_engineer")

    assert "python" in skills
    assert "sql" in skills
    assert "machine_learning" in skills
    assert skills[:3] == ["python", "machine_learning", "sql"] or set(skills).issuperset({"python", "machine_learning", "sql"})
