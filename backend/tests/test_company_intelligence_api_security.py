from datetime import UTC, datetime

import httpx
import pytest

from app.auth.jwt import create_access_token
from app.company_intelligence.research import CompanyResearchProvider
from app.config import Settings
from app.db.repositories.company_intelligence_repository import (
    CompanyRepository,
    EvidenceClaimRepository,
    JobPostingRepository,
)
from app.dependencies import (
    get_company_intelligence_service,
    get_company_research_provider,
    get_settings_dep,
    get_user_repo,
)
from app.main import create_app
from app.models.common import UserRole
from app.models.company_intelligence import Company, EvidenceClaim, SourceType
from app.models.user import UserInDB, UserProfile
from app.services.company_intelligence_service import CompanyIntelligenceService
from tests.fake_mongo import FakeDatabase


def user(user_id, role=UserRole.STUDENT, targets=None):
    now = datetime.now(UTC)
    return UserInDB(
        _id=user_id,
        email=f"{user_id}@example.com",
        password_hash="private",
        display_name=user_id,
        role=role,
        profile=UserProfile(target_companies=targets or []),
        created_at=now,
        updated_at=now,
    )


class Users:
    def __init__(self, *items):
        self.items = {item.id: item for item in items}

    async def get_by_id(self, user_id):
        return self.items.get(user_id)

    async def set_target_companies(self, user_id, company_ids):
        item = self.items[user_id]
        updated = item.model_copy(update={"profile": item.profile.model_copy(update={"target_companies": company_ids})})
        self.items[user_id] = updated
        return updated


class Provider(CompanyResearchProvider):
    def __init__(self, claims):
        self.claims = claims
        self.calls = []

    async def research(self, company_id, role_id=None):
        self.calls.append((company_id, role_id))
        return self.claims


async def setup_api(*users, provider=None):
    settings = Settings(app_env="test", jwt_secret="test-secret-key-at-least-32-characters-long")
    db = FakeDatabase()
    companies = CompanyRepository(db)
    await companies.upsert(Company(company_id="acme", name="Acme"))
    await companies.upsert(Company(company_id="globex", name="Globex"))
    service = CompanyIntelligenceService(companies, JobPostingRepository(db), EvidenceClaimRepository(db), settings)
    users_repository = Users(*users)
    app = create_app()
    app.dependency_overrides[get_settings_dep] = lambda: settings
    app.dependency_overrides[get_user_repo] = lambda: users_repository
    app.dependency_overrides[get_company_intelligence_service] = lambda: service
    if provider is not None:
        app.dependency_overrides[get_company_research_provider] = lambda: provider
    headers = {
        item.id: {"Authorization": f"Bearer {create_access_token(item.id, item.email, item.role, settings)}"}
        for item in users
    }
    return app, service, headers


@pytest.mark.asyncio
async def test_company_routes_require_authentication():
    app, _, _ = await setup_api(user("student"))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/v1/companies", params={"q": "acme"})).status_code == 401
        assert (await client.post("/api/v1/companies/acme/research")).status_code == 401


@pytest.mark.asyncio
async def test_student_cannot_ingest_companies_or_execute_research():
    student = user("student")
    provider = Provider([])
    app, _, headers = await setup_api(student, provider=provider)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/companies", headers=headers[student.id], json={"company_id": "new", "name": "New"})
        assert response.status_code == 403
        assert (await client.post("/api/v1/companies/acme/research", headers=headers[student.id])).status_code == 403
    assert provider.calls == []


@pytest.mark.asyncio
async def test_admin_can_perform_company_ingestion_operations():
    admin = user("admin", UserRole.ADMIN)
    app, _, headers = await setup_api(admin)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/api/v1/companies", headers=headers[admin.id], json={"company_id": "new", "name": "New"})).status_code == 201
        assert (await client.post("/api/v1/companies/jobs", headers=headers[admin.id], json={"company_id": "new", "title": "Engineer", "url": "https://new.example/jobs/1", "source_type": "OFFICIAL_JOB_POSTING"})).status_code == 201
        assert (await client.post("/api/v1/companies/evidence", headers=headers[admin.id], json={"company_id": "new", "claim_key": "python", "claim_text": "Python", "source_url": "https://new.example/jobs/1", "source_type": "OFFICIAL_JOB_POSTING", "evidence_text": "Python"})).status_code == 201


@pytest.mark.asyncio
async def test_target_company_changes_are_isolated_to_authenticated_user():
    first, second = user("first"), user("second")
    app, _, headers = await setup_api(first, second)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/api/v1/companies/targets/acme", headers=headers[first.id])).status_code == 204
        assert (await client.post("/api/v1/companies/targets/globex", headers=headers[second.id])).status_code == 204

    users = app.dependency_overrides[get_user_repo]()
    assert users.items[first.id].profile.target_companies == ["acme"]
    assert users.items[second.id].profile.target_companies == ["globex"]


def provider_claim(company_id="acme", role_id="backend"):
    return EvidenceClaim(
        company_id=company_id,
        role_id=role_id,
        claim_key="python",
        claim_text="Python is required",
        source_url="https://acme.example/jobs/backend",
        source_type=SourceType.OFFICIAL_JOB_POSTING,
        source_title="Backend Engineer",
        evidence_text="Required qualifications: Python",
    )


@pytest.mark.asyncio
async def test_admin_research_succeeds_with_mocked_provider_and_preserves_provenance():
    admin = user("admin", UserRole.ADMIN)
    provider = Provider([provider_claim()])
    app, _, headers = await setup_api(admin, provider=provider)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/companies/acme/research", params={"role_id": "backend"}, headers=headers[admin.id])

    assert response.status_code == 200
    claim = response.json()[0]
    assert provider.calls == [("acme", "backend")]
    assert claim["source_type"] == "OFFICIAL_JOB_POSTING"
    assert claim["source_title"] == "Backend Engineer"
    assert claim["source_url"] == "https://acme.example/jobs/backend"
    assert claim["evidence_text"] == "Required qualifications: Python"


@pytest.mark.asyncio
async def test_research_rejects_provider_claims_for_another_company_or_role():
    admin = user("admin", UserRole.ADMIN)
    provider = Provider([provider_claim(company_id="globex")])
    app, _, headers = await setup_api(admin, provider=provider)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/companies/acme/research", params={"role_id": "backend"}, headers=headers[admin.id])
    assert response.status_code == 422

    provider.claims = [provider_claim(role_id="data")]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/companies/acme/research", params={"role_id": "backend"}, headers=headers[admin.id])
    assert response.status_code == 422
