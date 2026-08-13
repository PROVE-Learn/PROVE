import httpx
import pytest

from app.dependencies import get_company_intelligence_service, get_current_admin, get_current_user, get_user_repo
from app.main import create_app
from app.models.company_intelligence import Company, EvidenceClaim, JobPosting, SourceType
from app.models.common import UserRole
from app.models.user import UserInDB
from datetime import UTC, datetime


def make_user(role=UserRole.STUDENT):
    return UserInDB(_id="64b64c3e5e4f88c9d4000301", email="student@example.com", password_hash="private", display_name="Student", role=role, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))


class Service:
    def __init__(self): self.company_data=Company(company_id="acme", name="Acme")
    async def lookup(self, q): return [self.company_data] if q == "acme" else []
    async def company(self, _): return self.company_data
    async def jobs_for_company(self, _): return [JobPosting(company_id="acme", title="Backend", url="https://acme.example/job", source_type=SourceType.OFFICIAL_JOB_POSTING)]
    async def evidence(self, *_): return [EvidenceClaim(company_id="acme", claim_key="python", claim_text="Python", source_url="https://acme.example/job", source_type=SourceType.OFFICIAL_JOB_POSTING, evidence_text="Python")]
    async def target_companies(self, *_): return [self.company_data]
    async def add_company(self, x): return x
    async def add_job(self, x): return x
    async def add_claim(self, x): return x
    async def research(self, *_): return await self.evidence("acme")


@pytest.mark.asyncio
async def test_company_read_and_admin_routes_use_dependencies():
    app=create_app(); service=Service(); student=make_user(); admin=make_user(UserRole.ADMIN)
    app.dependency_overrides[get_company_intelligence_service]=lambda: service
    app.dependency_overrides[get_current_user]=lambda: student
    app.dependency_overrides[get_user_repo]=lambda: object()
    app.dependency_overrides[get_current_admin]=lambda: admin
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        assert (await c.get("/api/v1/companies", params={"q":"acme"})).json()[0]["company_id"] == "acme"
        assert (await c.get("/api/v1/companies/acme/jobs")).json()[0]["title"] == "Backend"
        assert (await c.get("/api/v1/companies/acme/evidence")).json()[0]["source_type"] == "OFFICIAL_JOB_POSTING"
        assert (await c.post("/api/v1/companies", json={"company_id":"new","name":"New"})).status_code == 201
        assert (await c.post("/api/v1/companies/acme/research")).status_code == 503
