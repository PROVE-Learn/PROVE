from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_current_user, get_memory_service, get_profile_service
from app.models.memory import MemoryCreate, MemoryUpdate, UserMemoryInDB
from app.models.user import UserInDB, UserProfileResponse, UserProfileUpdate
from app.services.memory_service import MemoryService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserProfileResponse)
async def get_profile(
    current_user: UserInDB = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    return await profile_service.get_profile(current_user.id)


@router.patch("", response_model=UserProfileResponse)
async def update_profile(
    update: UserProfileUpdate,
    current_user: UserInDB = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    return await profile_service.update_profile(current_user.id, update)


@router.get("/memory", response_model=list[UserMemoryInDB], response_model_by_alias=False)
async def get_memory(
    current_user: UserInDB = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service),
) -> list[UserMemoryInDB]:
    return await memory_service.get_user_memory(current_user.id)


@router.post(
    "/memory",
    response_model=UserMemoryInDB,
    response_model_by_alias=False,
    status_code=status.HTTP_201_CREATED,
)
async def create_memory(
    memory: MemoryCreate,
    current_user: UserInDB = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service),
) -> UserMemoryInDB:
    return await memory_service.create_memory(current_user.id, memory)


@router.patch(
    "/memory/{memory_id}", response_model=UserMemoryInDB, response_model_by_alias=False
)
async def update_memory(
    memory_id: str,
    update: MemoryUpdate,
    current_user: UserInDB = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service),
) -> UserMemoryInDB:
    return await memory_service.update_memory(current_user.id, memory_id, update)


@router.delete("/memory/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    current_user: UserInDB = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service),
) -> Response:
    await memory_service.delete_memory(current_user.id, memory_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
