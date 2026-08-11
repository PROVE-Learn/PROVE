from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_current_admin,
    get_human_review_queue_repo,
    get_skill_repo,
)
from app.db.repositories.human_review_queue_repository import HumanReviewQueueRepository
from app.db.repositories.skill_repository import SkillRepository
from app.models.common import ReviewStatus
from app.models.skill import SkillInDB
from app.models.user import UserInDB
from app.models.verification import HumanReviewItemInDB
from app.api.schemas import MessageResponse, ReviewActionRequest

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/review-queue", response_model=list[HumanReviewItemInDB])
async def list_review_queue(
    _: UserInDB = Depends(get_current_admin),
    review_repo: HumanReviewQueueRepository = Depends(get_human_review_queue_repo),
) -> list[HumanReviewItemInDB]:
    return await review_repo.list_pending()


@router.post("/review-queue/{item_id}", response_model=HumanReviewItemInDB)
async def update_review_item(
    item_id: str,
    action: ReviewActionRequest,
    admin: UserInDB = Depends(get_current_admin),
    review_repo: HumanReviewQueueRepository = Depends(get_human_review_queue_repo),
) -> HumanReviewItemInDB:
    if action.status == ReviewStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be approved or rejected",
        )

    item = await review_repo.update_status(
        item_id,
        action.status,
        reviewed_by=action.reviewed_by or admin.id,
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.get("/skills", response_model=list[SkillInDB])
async def list_skills(
    _: UserInDB = Depends(get_current_admin),
    skill_repo: SkillRepository = Depends(get_skill_repo),
) -> list[SkillInDB]:
    return await skill_repo.list_all()
