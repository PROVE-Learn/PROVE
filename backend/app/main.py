from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.config import get_settings
from app.db.client import close_mongodb_connection, connect_to_mongodb, get_database
from app.db.repositories.career_assessment_repository import CareerAssessmentRepository
from app.db.repositories.human_review_queue_repository import HumanReviewQueueRepository
from app.db.repositories.skill_repository import SkillRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.user_skill_progress_repository import UserSkillProgressRepository
from app.db.repositories.verification_record_repository import VerificationRecordRepository


async def _ensure_indexes() -> None:
    db = get_database()
    repos = [
        UserRepository(db),
        SkillRepository(db),
        UserSkillProgressRepository(db),
        CareerAssessmentRepository(db),
        VerificationRecordRepository(db),
        HumanReviewQueueRepository(db),
    ]
    for repo in repos:
        await repo.ensure_indexes()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await connect_to_mongodb(settings)
    await _ensure_indexes()
    yield
    await close_mongodb_connection()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="AI Career Mastery Agent - Closed Beta",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    return app


app = create_app()
