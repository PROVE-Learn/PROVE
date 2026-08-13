from fastapi import APIRouter, Depends, status

from app.dependencies import get_company_intelligence_service, get_company_research_provider, get_current_admin, get_current_user, get_user_repo
from app.company_intelligence.research import CompanyResearchProvider
from app.db.repositories.user_repository import UserRepository
from app.models.company_intelligence import Company, EvidenceClaim, JobPosting
from app.models.user import UserInDB
from app.services.company_intelligence_service import CompanyIntelligenceService

router = APIRouter(prefix="/companies", tags=["company-intelligence"])

@router.get("", response_model=list[Company], response_model_by_alias=False)
async def lookup(q: str, _: UserInDB = Depends(get_current_user), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): return await service.lookup(q)
@router.get("/{company_id}", response_model=Company, response_model_by_alias=False)
async def company(company_id: str, _: UserInDB = Depends(get_current_user), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): return await service.company(company_id)
@router.get("/{company_id}/jobs", response_model=list[JobPosting], response_model_by_alias=False)
async def jobs(company_id: str, _: UserInDB = Depends(get_current_user), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): return await service.jobs_for_company(company_id)
@router.get("/{company_id}/roles/{role_id}/skills", response_model=list[str], response_model_by_alias=False)
async def role_skills(company_id: str, role_id: str, _: UserInDB = Depends(get_current_user), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): return await service.extract_role_skills(company_id, role_id)
@router.get("/{company_id}/evidence", response_model=list[EvidenceClaim], response_model_by_alias=False)
async def evidence(company_id: str, role_id: str | None = None, _: UserInDB = Depends(get_current_user), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): return await service.evidence(company_id, role_id)
@router.post("", response_model=Company, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def add_company(data: Company, _: UserInDB = Depends(get_current_admin), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): return await service.add_company(data)
@router.post("/jobs", response_model=JobPosting, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def add_job(data: JobPosting, _: UserInDB = Depends(get_current_admin), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): return await service.add_job(data)
@router.post("/evidence", response_model=EvidenceClaim, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def add_evidence(data: EvidenceClaim, _: UserInDB = Depends(get_current_admin), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): return await service.add_claim(data)
@router.get("/targets/me", response_model=list[Company], response_model_by_alias=False)
async def targets(user: UserInDB = Depends(get_current_user), users: UserRepository = Depends(get_user_repo), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): return await service.target_companies(user.id, users)
@router.post("/targets/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_target(company_id: str, user: UserInDB = Depends(get_current_user), users: UserRepository = Depends(get_user_repo), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): await service.add_target_company(user.id, company_id, users)
@router.delete("/targets/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_target(company_id: str, user: UserInDB = Depends(get_current_user), users: UserRepository = Depends(get_user_repo), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): await service.remove_target_company(user.id, company_id, users)
@router.post("/{company_id}/research", response_model=list[EvidenceClaim], response_model_by_alias=False)
async def research(company_id: str, role_id: str | None = None, _: UserInDB = Depends(get_current_admin), provider: CompanyResearchProvider = Depends(get_company_research_provider), service: CompanyIntelligenceService = Depends(get_company_intelligence_service)): return await service.research(company_id, role_id, provider)
