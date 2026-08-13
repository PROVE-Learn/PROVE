from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.dependencies import get_current_user, get_learning_service
from app.dependencies import get_company_intelligence_service
from app.models.learning import LearningActivity, LearningPlan, ProgressItem, SkillGap
from app.models.user import UserInDB
from app.services.learning_service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])
class CompleteActivityRequest(BaseModel):
    evidence: list[str] = Field(min_length=1, max_length=10)
@router.get("/skill-gaps", response_model=list[SkillGap])
async def skill_gaps(user: UserInDB = Depends(get_current_user), service: LearningService = Depends(get_learning_service)): return await service.gaps(user.id)
@router.get("/plan", response_model=LearningPlan, response_model_by_alias=False)
async def plan(user: UserInDB = Depends(get_current_user), service: LearningService = Depends(get_learning_service)): return await service.plan(user.id)
@router.post("/activities/{activity_id}/start", response_model=LearningActivity, response_model_by_alias=False)
async def start(activity_id: str, user: UserInDB = Depends(get_current_user), service: LearningService = Depends(get_learning_service)): return await service.start(user.id, activity_id)
@router.post("/activities/{activity_id}/complete", response_model=LearningActivity, response_model_by_alias=False)
async def complete(activity_id: str, request: CompleteActivityRequest, user: UserInDB = Depends(get_current_user), service: LearningService = Depends(get_learning_service)): return await service.complete(user.id, activity_id, request.evidence)
@router.get("/progress", response_model=list[ProgressItem])
async def progress(user: UserInDB = Depends(get_current_user), service: LearningService = Depends(get_learning_service)): return await service.progress_view(user.id)


@router.get("/plan/company/{company_id}/role/{role_id}", response_model=LearningPlan, response_model_by_alias=False)
async def plan_for_company_role(company_id: str, role_id: str, user: UserInDB = Depends(get_current_user), service: LearningService = Depends(get_learning_service), company_service = Depends(get_company_intelligence_service)):
    return await service.plan_for_company_role(user.id, company_id, role_id, company_service)
