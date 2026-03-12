from __future__ import annotations

from fastapi import APIRouter, Depends

from ..api_dependencies import require_admin
from ..api_models import SettingsModel
from ..services import settings as settings_service
from ..services.jobs import get_repository

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings", dependencies=[Depends(require_admin)])
def get_settings():
    repo = get_repository()
    return settings_service.get_settings(repo)


@router.post("/settings", dependencies=[Depends(require_admin)])
def update_settings(settings: SettingsModel):
    settings_dict = settings.model_dump() if hasattr(settings, "model_dump") else settings.dict()
    repo = get_repository()
    return settings_service.update_settings(repo, settings_dict)
