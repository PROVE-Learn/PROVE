from dataclasses import dataclass

from app.config import Settings, get_settings


@dataclass
class VerificationPolicy:
    aptitude_max_retries: int
    coding_max_retries: int
    cache_ttl_technical_days: int
    cache_ttl_job_posting_days: int
    cache_ttl_question_reverify_days: int
    beta_company_research_requires_review: bool = True
    beta_rubric_citation_threshold: float = 0.7


def get_verification_policy(settings: Settings | None = None) -> VerificationPolicy:
    settings = settings or get_settings()
    return VerificationPolicy(
        aptitude_max_retries=settings.verification_aptitude_max_retries,
        coding_max_retries=settings.verification_coding_max_retries,
        cache_ttl_technical_days=settings.cache_ttl_technical_days,
        cache_ttl_job_posting_days=settings.cache_ttl_job_posting_days,
        cache_ttl_question_reverify_days=settings.cache_ttl_question_reverify_days,
    )
