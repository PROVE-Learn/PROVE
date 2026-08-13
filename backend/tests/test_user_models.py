from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.common import UserPhase, UserRole
from app.models.user import UserCreate, UserInDB


def test_user_create_accepts_valid_input():
    user = UserCreate(email="learner@example.com", password="password123", display_name="Learner")

    assert user.email == "learner@example.com"
    assert user.display_name == "Learner"


@pytest.mark.parametrize(
    ("field", "value"),
    [("email", "not-an-email"), ("password", "short"), ("display_name", "")],
)
def test_user_create_rejects_invalid_input(field: str, value: str):
    values = {"email": "learner@example.com", "password": "password123", "display_name": "Learner"}
    values[field] = value

    with pytest.raises(ValidationError):
        UserCreate(**values)


def test_user_in_db_accepts_mongodb_id_and_default_values():
    now = datetime.now(timezone.utc)
    user = UserInDB(
        _id="user-1",
        email="learner@example.com",
        password_hash="hashed-password",
        display_name="Learner",
        created_at=now,
        updated_at=now,
    )

    assert user.id == "user-1"
    assert user.role == UserRole.STUDENT
    assert user.current_phase == UserPhase.ONBOARDING
    assert user.model_dump(by_alias=True)["_id"] == "user-1"
