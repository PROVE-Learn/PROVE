from fastapi import HTTPException, status

from app.db.repositories.user_repository import UserRepository
from app.models.user import UserInDB, UserProfileResponse, UserProfileUpdate


class ProfileService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def get_profile(self, user_id: str) -> UserProfileResponse:
        user = await self._user_repo.get_profile(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return self._to_response(user)

    async def update_profile(self, user_id: str, update: UserProfileUpdate) -> UserProfileResponse:
        user = await self._user_repo.update_profile(user_id, update)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return self._to_response(user)

    @staticmethod
    def _to_response(user: UserInDB) -> UserProfileResponse:
        return UserProfileResponse(
            id=user.id,
            display_name=user.display_name,
            email=user.email,
            learning_preferences=user.preferences,
            **user.profile.model_dump(),
        )
