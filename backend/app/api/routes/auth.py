from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.jwt import create_access_token
from app.auth.passwords import hash_password, verify_password
from app.config import Settings
from app.db.repositories.user_repository import BetaCapacityError, UserRepository
from app.dependencies import get_current_user, get_db, get_settings_dep, get_user_repo
from app.models.user import UserCreate, UserInDB, UserLogin, UserPublic
from app.api.schemas import TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_public(user: UserInDB) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        beta_slot=user.beta_slot,
        current_phase=user.current_phase,
        created_at=user.created_at,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    user_repo: UserRepository = Depends(get_user_repo),
    settings: Settings = Depends(get_settings_dep),
) -> TokenResponse:
    existing = await user_repo.get_by_email(user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    try:
        user = await user_repo.create(user_in, hash_password(user_in.password))
    except BetaCapacityError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    token = create_access_token(user.id, user.email, user.role, settings)
    return TokenResponse(access_token=token, user=_to_public(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    user_repo: UserRepository = Depends(get_user_repo),
    settings: Settings = Depends(get_settings_dep),
) -> TokenResponse:
    user = await user_repo.get_by_email(credentials.email)
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id, user.email, user.role, settings)
    return TokenResponse(access_token=token, user=_to_public(user))


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: UserInDB = Depends(get_current_user)) -> UserPublic:
    return _to_public(current_user)
