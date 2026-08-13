from fastapi import APIRouter, Depends

from app.dependencies import (
    get_current_user,
    get_readiness_review_service,
    get_readiness_service,
)
from app.models.readiness import CareerReadiness, ReadinessReview
from app.models.user import UserInDB
from app.services.readiness_review_service import ReadinessReviewService
from app.services.readiness_service import ReadinessService

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.get("", response_model=CareerReadiness)
async def get_readiness(
    user: UserInDB = Depends(get_current_user),
    service: ReadinessService = Depends(get_readiness_service),
) -> CareerReadiness:
    return await service.get(user)


@router.get("/review", response_model=ReadinessReview)
async def review_readiness(
    user: UserInDB = Depends(get_current_user),
    service: ReadinessReviewService = Depends(get_readiness_review_service),
) -> ReadinessReview:
    return await service.review(user)
