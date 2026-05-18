from datetime import datetime, timezone
from app.config import get_settings

_last_sync: dict | None = None
_next_sync_at: datetime | None = None


def get_sync_status() -> dict:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    next_at = _next_sync_at
    seconds_until = None
    if next_at:
        seconds_until = max(0, int((next_at - now).total_seconds()))
    return {
        "interval_hours": settings.sync_interval_hours,
        "last_sync": _last_sync,
        "next_sync_at": next_at.isoformat() if next_at else None,
        "seconds_until_next": seconds_until,
    }


def _set_next_run(interval_hours: int):
    global _next_sync_at
    from datetime import timedelta
    _next_sync_at = datetime.now(timezone.utc) + timedelta(hours=interval_hours)


async def run_scheduled_sync() -> dict:
    """Pull Hevy + Oura on the configured interval."""
    global _last_sync
    settings = get_settings()
    results = {"at": datetime.now(timezone.utc).isoformat(), "hevy": None, "oura": None}

    if not settings.preview_mode:
        from app.services.hevy_service import sync_hevy_workouts
        from app.services.oura_service import sync_oura

        if settings.hevy_api_key:
            try:
                results["hevy"] = await sync_hevy_workouts()
            except Exception as e:
                results["hevy"] = {"error": str(e)}
        if settings.oura_access_token:
            try:
                results["oura"] = await sync_oura()
            except Exception as e:
                results["oura"] = {"error": str(e)}
    else:
        results["hevy"] = {"skipped": "preview_mode"}
        results["oura"] = {"skipped": "preview_mode"}

    _last_sync = results
    _set_next_run(settings.sync_interval_hours)
    return results
