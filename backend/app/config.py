from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PROVE"
    app_env: Literal["development", "production", "test"] = "development"
    debug: bool = False

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "prove"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    max_beta_users: int = 10

    llm_api_key: str | None = None

    verification_aptitude_max_retries: int = 2
    verification_coding_max_retries: int = 2
    cache_ttl_technical_days: int = 180
    cache_ttl_job_posting_days: int = 90
    cache_ttl_question_reverify_days: int = 90

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.app_env == "production":
            if self.jwt_secret == "change-me" or len(self.jwt_secret) < 32:
                raise ValueError("JWT_SECRET must be set to a secure value in production")
            if not self.llm_api_key:
                raise ValueError("LLM_API_KEY is required in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
