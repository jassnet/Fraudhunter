from __future__ import annotations

from fastapi import APIRouter, Depends

from ..api_dependencies import require_protected_access
from ..api_models import SettingsModel
from ..service_dependencies import get_repository
from ..services import settings as settings_service

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings", dependencies=[Depends(require_protected_access)])
def get_settings():
    return settings_service.get_settings(get_repository())


@router.post("/settings", dependencies=[Depends(require_protected_access)])
def update_settings(settings: SettingsModel):
    settings_dict = settings.model_dump() if hasattr(settings, "model_dump") else settings.dict()
    return settings_service.update_settings(get_repository(), settings_dict)
