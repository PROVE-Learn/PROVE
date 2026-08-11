import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import Settings
from app.db.client import close_mongodb_connection, connect_to_mongodb, get_database
from app.main import create_app


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        app_env="test",
        debug=True,
        mongodb_uri=os.getenv("TEST_MONGODB_URI", "mongodb://localhost:27017"),
        mongodb_db_name="prove_test",
        jwt_secret="test-secret-key-at-least-32-characters-long",
        max_beta_users=10,
    )


@pytest_asyncio.fixture
async def test_db(test_settings: Settings):
    client = AsyncIOMotorClient(test_settings.mongodb_uri)
    db = client[test_settings.mongodb_db_name]
    await client.admin.command("ping")

    collections = await db.list_collection_names()
    for name in collections:
        await db.drop_collection(name)

    yield db

    collections = await db.list_collection_names()
    for name in collections:
        await db.drop_collection(name)
    client.close()


@pytest_asyncio.fixture
async def app(test_settings: Settings, test_db, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("MONGODB_DB_NAME", test_settings.mongodb_db_name)
    monkeypatch.setenv("JWT_SECRET", test_settings.jwt_secret)

    from app.config import get_settings

    get_settings.cache_clear()

    application = create_app()

    await close_mongodb_connection()
    await connect_to_mongodb(test_settings)

    from app.db.repositories.career_assessment_repository import CareerAssessmentRepository
    from app.db.repositories.human_review_queue_repository import HumanReviewQueueRepository
    from app.db.repositories.skill_repository import SkillRepository
    from app.db.repositories.user_repository import UserRepository
    from app.db.repositories.user_skill_progress_repository import UserSkillProgressRepository
    from app.db.repositories.verification_record_repository import VerificationRecordRepository

    db = get_database()
    for repo in [
        UserRepository(db),
        SkillRepository(db),
        UserSkillProgressRepository(db),
        CareerAssessmentRepository(db),
        VerificationRecordRepository(db),
        HumanReviewQueueRepository(db),
    ]:
        await repo.ensure_indexes()

    yield application

    await close_mongodb_connection()
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
