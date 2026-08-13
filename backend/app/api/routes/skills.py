from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_learning_service
from app.models.skill import SkillCreate
from app.models.user import UserInDB
from app.services.learning_service import LearningService

router = APIRouter(prefix="/skills", tags=["skills"])
@router.get("", response_model=list[SkillCreate])
async def list_skills(_: UserInDB = Depends(get_current_user), service: LearningService = Depends(get_learning_service)): return await service.list_skills()
@router.get("/{skill_id}", response_model=SkillCreate)
async def get_skill(skill_id: str, _: UserInDB = Depends(get_current_user), service: LearningService = Depends(get_learning_service)): return await service.get_skill(skill_id)
