from bson import ObjectId
from fastapi import HTTPException, status

from app.db.repositories.user_memory_repository import UserMemoryRepository
from app.models.memory import MemoryCreate, MemoryUpdate, UserMemoryInDB


class MemoryService:
    def __init__(self, memory_repo: UserMemoryRepository) -> None:
        self._memory_repo = memory_repo

    async def create_memory(self, user_id: str, memory: MemoryCreate) -> UserMemoryInDB:
        return await self._memory_repo.create(user_id, memory)

    async def get_user_memory(self, user_id: str) -> list[UserMemoryInDB]:
        return await self._memory_repo.list_for_user(user_id)

    async def update_memory(
        self, user_id: str, memory_id: str, update: MemoryUpdate
    ) -> UserMemoryInDB:
        self._validate_memory_id(memory_id)
        memory = await self._memory_repo.update(user_id, memory_id, update)
        if memory is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
        return memory

    async def delete_memory(self, user_id: str, memory_id: str) -> None:
        self._validate_memory_id(memory_id)
        deleted = await self._memory_repo.delete(user_id, memory_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    @staticmethod
    def _validate_memory_id(memory_id: str) -> None:
        if not ObjectId.is_valid(memory_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid memory id",
            )
