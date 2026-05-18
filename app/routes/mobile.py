from fastapi import APIRouter
from app.config import get_settings

router = APIRouter(prefix="/mobile", tags=["mobile"])


@router.get("/config")
async def mobile_config():
    """Bootstrap config for React Native / Expo / Flutter clients."""
    settings = get_settings()
    return {
        "app": "Forge",
        "api_version": "1.0.0",
        "preview_mode": settings.preview_mode,
        "program_start": settings.program_start,
        "sync_interval_hours": settings.sync_interval_hours,
        "web_app_url": "/app",
        "screens": {
            "dashboard": {
                "path": "/api/analysis/today",
                "preview_path": "/api/preview/dashboard",
                "params": ["program_start"],
            },
            "workout": {
                "path": "/api/program/targets/{week}",
                "preview_path": "/api/preview/program/week/{week}",
            },
            "history": {"path": "/api/workouts", "preview_path": "/api/preview/workouts"},
            "nutrition": {"path": "/api/nutrition", "preview_path": "/api/preview/nutrition"},
            "recovery": {"path": "/api/recovery", "preview_path": "/api/preview/recovery"},
            "progress": {"path": "/api/body-metrics", "preview_path": "/api/preview/body-metrics"},
            "schedule": {"path": "/api/program/schedule"},
        },
        "auth": {
            "type": "none",
            "note": "Webhook uses Bearer token; mobile reads data via public API today",
        },
    }


@router.get("/health")
async def health():
    settings = get_settings()
    mongo_status = "skipped" if settings.preview_mode else "unknown"
    if not settings.preview_mode:
        try:
            from app.database import get_client
            await get_client().admin.command("ping")
            mongo_status = "ok"
        except Exception as exc:
            mongo_status = f"error: {exc}"
    return {
        "status": "ok",
        "preview_mode": settings.preview_mode,
        "mongodb": mongo_status,
    }
