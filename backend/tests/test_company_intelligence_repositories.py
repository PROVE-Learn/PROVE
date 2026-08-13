from app.db.collections import COMPANIES, EVIDENCE_CLAIMS, JOB_POSTINGS, USERS
from app.db.repositories.company_intelligence_repository import (
    CompanyRepository,
    EvidenceClaimRepository,
    JobPostingRepository,
)
from app.db.repositories.user_repository import UserRepository
from app.models.company_intelligence import Company, EvidenceClaim, JobPosting, SourceType
from app.models.user import UserCreate
from tests.fake_mongo import FakeDatabase


async def test_company_repository_upserts_gets_and_looks_up_case_insensitively():
    db = FakeDatabase()
    repository = CompanyRepository(db)
    await repository.ensure_indexes()
    await repository.upsert(Company(company_id="acme", name="Acme Corporation", aliases=["AC"] ))
    saved = await repository.upsert(Company(company_id="acme", name="Acme Labs", aliases=["Acme"]))

    assert saved.name == "Acme Labs"
    assert (await repository.get("acme")).aliases == ["Acme"]
    assert [company.company_id for company in await repository.lookup("LABS")] == ["acme"]
    assert db[COMPANIES].indexes == [("company_id", {"unique": True})]


async def test_job_posting_repository_persists_ids_and_returns_only_active_company_jobs():
    db = FakeDatabase()
    repository = JobPostingRepository(db)
    await repository.ensure_indexes()
    active = await repository.create(JobPosting(company_id="acme", title="Backend", url="https://acme.example/backend", source_type=SourceType.OFFICIAL_JOB_POSTING))
    await repository.create(JobPosting(company_id="acme", title="Old", url="https://acme.example/old", source_type=SourceType.OFFICIAL_JOB_POSTING, active=False))
    await repository.create(JobPosting(company_id="other", title="Other", url="https://other.example/job", source_type=SourceType.OFFICIAL_JOB_POSTING))

    assert active.id is not None
    assert [job.title for job in await repository.list_for_company("acme")] == ["Backend"]
    assert (await repository.get(active.id)).title == "Backend"
    assert (await repository.get("64b64c3e5e4f88c9d4000999")) is None
    assert db[JOB_POSTINGS].indexes


async def test_evidence_claim_repository_filters_by_company_and_optional_role():
    db = FakeDatabase()
    repository = EvidenceClaimRepository(db)
    await repository.ensure_indexes()
    first = await repository.create(EvidenceClaim(company_id="acme", role_id="backend", claim_key="python", claim_text="Python required", source_url="https://acme.example/job", source_type=SourceType.OFFICIAL_JOB_POSTING, evidence_text="Python"))
    await repository.create(EvidenceClaim(company_id="acme", role_id="data", claim_key="sql", claim_text="SQL required", source_url="https://acme.example/data", source_type=SourceType.OFFICIAL_JOB_POSTING, evidence_text="SQL"))
    await repository.create(EvidenceClaim(company_id="other", role_id="backend", claim_key="go", claim_text="Go required", source_url="https://other.example/job", source_type=SourceType.OFFICIAL_JOB_POSTING, evidence_text="Go"))

    assert first.id is not None
    assert [claim.claim_key for claim in await repository.list_for_company("acme", "backend")] == ["python"]
    assert {claim.claim_key for claim in await repository.list_for_company("acme")} == {"python", "sql"}
    assert db[EVIDENCE_CLAIMS].indexes


async def test_user_repository_persists_target_companies_for_the_selected_user(monkeypatch):
    db = FakeDatabase()
    monkeypatch.setattr("app.db.repositories.user_repository.get_settings", lambda: type("Settings", (), {"max_beta_users": 10})())
    repository = UserRepository(db)
    first = await repository.create(UserCreate(email="first@example.com", password="password1", display_name="First"), "hash")
    second = await repository.create(UserCreate(email="second@example.com", password="password1", display_name="Second"), "hash")

    updated = await repository.set_target_companies(first.id, ["acme", "globex"])

    assert updated.profile.target_companies == ["acme", "globex"]
    assert (await repository.get_by_id(first.id)).profile.target_companies == ["acme", "globex"]
    assert (await repository.get_by_id(second.id)).profile.target_companies == []
    assert db[USERS].indexes == []
