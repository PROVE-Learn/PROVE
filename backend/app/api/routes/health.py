from fastapi import APIRouter, Depends

from app.config import Settings
from app.db.client import get_database
from app.dependencies import get_settings_dep
from app.api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings_dep)) -> HealthResponse:
    db_status = "disconnected"
    try:
        db = get_database()
        await db.command("ping")
        db_status = "connected"
    except RuntimeError:
        db_status = "disconnected"
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        app_name=settings.app_name,
        database=db_status,
    )
