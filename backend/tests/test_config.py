import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_defaults_include_local_mongodb_configuration():
    settings = Settings()

    assert settings.mongodb_uri == "mongodb://localhost:27017"
    assert settings.mongodb_db_name == "prove"
    assert settings.app_env == "development"


def test_production_requires_secure_jwt_secret_and_llm_key():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(app_env="production")

    with pytest.raises(ValidationError, match="LLM_API_KEY"):
        Settings(
            app_env="production",
            jwt_secret="a-secure-secret-that-is-at-least-32-characters",
        )


def test_production_settings_accept_configured_values():
    settings = Settings(
        app_env="production",
        jwt_secret="a-secure-secret-that-is-at-least-32-characters",
        llm_api_key="test-key",
        mongodb_uri="mongodb://database:27017",
        mongodb_db_name="prove_production",
    )

    assert settings.mongodb_uri == "mongodb://database:27017"
    assert settings.mongodb_db_name == "prove_production"
