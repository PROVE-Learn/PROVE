from fastapi import APIRouter, Depends, status

from app.dependencies import get_career_discovery_service, get_current_user
from app.models.career import CareerAssessmentInDB
from app.models.career_discovery import (
    AssessmentAnswerSubmission, AssessmentResult, CareerRecommendation, PublicDiscoveryQuestion,
    TargetRoleSelection, TargetRoleSelectionRequest,
)
from app.models.user import UserInDB
from app.services.career_discovery_service import CareerDiscoveryService

router = APIRouter(prefix="/career-discovery", tags=["career-discovery"])


@router.post("/assessments", response_model=CareerAssessmentInDB, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def start_assessment(current_user: UserInDB = Depends(get_current_user), service: CareerDiscoveryService = Depends(get_career_discovery_service)) -> CareerAssessmentInDB:
    return await service.start(current_user.id)


@router.get("/questions", response_model=list[PublicDiscoveryQuestion])
async def get_questions(_: UserInDB = Depends(get_current_user), service: CareerDiscoveryService = Depends(get_career_discovery_service)) -> list[PublicDiscoveryQuestion]:
    return service.questions()


@router.get("/assessments/{assessment_id}", response_model=CareerAssessmentInDB, response_model_by_alias=False)
async def get_assessment(assessment_id: str, current_user: UserInDB = Depends(get_current_user), service: CareerDiscoveryService = Depends(get_career_discovery_service)) -> CareerAssessmentInDB:
    return await service.get_assessment(current_user.id, assessment_id)


@router.put("/assessments/{assessment_id}/answers", response_model=CareerAssessmentInDB, response_model_by_alias=False)
async def submit_answers(assessment_id: str, submission: AssessmentAnswerSubmission, current_user: UserInDB = Depends(get_current_user), service: CareerDiscoveryService = Depends(get_career_discovery_service)) -> CareerAssessmentInDB:
    return await service.submit_answers(current_user.id, assessment_id, submission)


@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentResult)
async def complete_assessment(assessment_id: str, current_user: UserInDB = Depends(get_current_user), service: CareerDiscoveryService = Depends(get_career_discovery_service)) -> AssessmentResult:
    return await service.complete(current_user.id, assessment_id)


@router.get("/assessments/{assessment_id}/results", response_model=AssessmentResult)
async def get_results(assessment_id: str, current_user: UserInDB = Depends(get_current_user), service: CareerDiscoveryService = Depends(get_career_discovery_service)) -> AssessmentResult:
    assessment = await service.get_assessment(current_user.id, assessment_id)
    return service._result(assessment)


@router.get("/assessments/{assessment_id}/recommendations", response_model=list[CareerRecommendation])
async def get_recommendations(assessment_id: str, current_user: UserInDB = Depends(get_current_user), service: CareerDiscoveryService = Depends(get_career_discovery_service)) -> list[CareerRecommendation]:
    return await service.recommendations(current_user, assessment_id)


@router.put("/target-role", response_model=TargetRoleSelection, response_model_by_alias=False)
async def select_target_role(request: TargetRoleSelectionRequest, current_user: UserInDB = Depends(get_current_user), service: CareerDiscoveryService = Depends(get_career_discovery_service)) -> TargetRoleSelection:
    return await service.select_role(current_user, request)


@router.get("/target-role", response_model=TargetRoleSelection | None, response_model_by_alias=False)
async def get_target_role(current_user: UserInDB = Depends(get_current_user), service: CareerDiscoveryService = Depends(get_career_discovery_service)) -> TargetRoleSelection | None:
    return await service.current_role(current_user.id)
