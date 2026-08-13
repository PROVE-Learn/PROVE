from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.company_intelligence.research import CompanyResearchProvider
from app.config import Settings
from app.models.company_intelligence import Company, EvidenceClaim, SourceType, VerificationStatus
from app.models.user import UserInDB
from app.services.company_intelligence_service import CompanyIntelligenceService


class Companies:
    def __init__(self): self.items = {"acme": Company(company_id="acme", name="Acme", official_website="https://acme.example")}
    async def get(self, key): return self.items.get(key)
    async def lookup(self, query): return [v for k, v in self.items.items() if query in k]
    async def upsert(self, item): self.items[item.company_id] = item; return item
class Jobs:
    async def list_for_company(self, key): return []
    async def create(self, job): return job
class Claims:
    def __init__(self): self.items=[]
    async def create(self, claim): self.items.append(claim); return claim
    async def list_for_company(self, company_id, role_id=None): return self.items
class Users:
    def __init__(self): self.user=UserInDB(_id="64b64c3e5e4f88c9d4000201", email="s@example.com", password_hash="x", display_name="s", created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
    async def get_by_id(self, _): return self.user
    async def set_target_companies(self, _, ids): self.user.profile.target_companies=ids; return self.user
class MockProvider(CompanyResearchProvider):
    async def research(self, company_id, role_id=None): return [EvidenceClaim(company_id=company_id, role_id=role_id, claim_key="python", claim_text="Python mentioned", source_url="https://acme.example/jobs", source_type=SourceType.OFFICIAL_JOB_POSTING, source_title="Role", evidence_text="Python")]

@pytest.fixture
def service(): return CompanyIntelligenceService(Companies(), Jobs(), Claims(), Settings())

@pytest.mark.asyncio
async def test_company_lookup_and_target_company_lifecycle(service):
    users=Users(); assert (await service.lookup("acme"))[0].company_id == "acme"
    await service.add_target_company(users.user.id, "acme", users)
    assert [x.company_id for x in await service.target_companies(users.user.id, users)] == ["acme"]
    with pytest.raises(HTTPException) as duplicate: await service.add_target_company(users.user.id, "acme", users)
    assert duplicate.value.status_code == 409
    await service.remove_target_company(users.user.id, "acme", users)
    assert await service.target_companies(users.user.id, users) == []

@pytest.mark.asyncio
async def test_unknown_target_and_mocked_research_preserve_metadata(service):
    users=Users()
    with pytest.raises(HTTPException) as unknown: await service.add_target_company(users.user.id, "missing", users)
    assert unknown.value.status_code == 404
    claims=await service.research("acme", "backend_developer", MockProvider())
    assert claims[0].source_title == "Role"
    assert claims[0].verification_status == VerificationStatus.HIGH_CONFIDENCE
    assert claims[0].verification_status != VerificationStatus.VERIFIED
