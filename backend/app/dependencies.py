from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.jwt import decode_access_token
from app.config import Settings, get_settings
from app.db.client import get_database
from app.db.repositories.career_assessment_repository import CareerAssessmentRepository
from app.db.repositories.human_review_queue_repository import HumanReviewQueueRepository
from app.db.repositories.skill_repository import SkillRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.user_skill_progress_repository import UserSkillProgressRepository
from app.db.repositories.verification_record_repository import VerificationRecordRepository
from app.models.common import UserRole
from app.models.user import UserInDB
from app.verification.pipeline import VerificationPipeline

security = HTTPBearer(auto_error=False)


def get_settings_dep() -> Settings:
    return get_settings()


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


def get_user_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_skill_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> SkillRepository:
    return SkillRepository(db)


def get_user_skill_progress_repo(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserSkillProgressRepository:
    return UserSkillProgressRepository(db)


def get_career_assessment_repo(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> CareerAssessmentRepository:
    return CareerAssessmentRepository(db)


def get_verification_record_repo(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> VerificationRecordRepository:
    return VerificationRecordRepository(db)


def get_human_review_queue_repo(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> HumanReviewQueueRepository:
    return HumanReviewQueueRepository(db)


def get_verification_pipeline(
    verification_repo: VerificationRecordRepository = Depends(get_verification_record_repo),
    review_queue_repo: HumanReviewQueueRepository = Depends(get_human_review_queue_repo),
    settings: Settings = Depends(get_settings_dep),
) -> VerificationPipeline:
    from app.verification.policy import get_verification_policy

    return VerificationPipeline(
        verification_repo=verification_repo,
        review_queue_repo=review_queue_repo,
        policy=get_verification_policy(settings),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
    settings: Settings = Depends(get_settings_dep),
) -> UserInDB:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_access_token(credentials.credentials, settings)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user = await user_repo.get_by_id(payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def get_current_admin(user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
