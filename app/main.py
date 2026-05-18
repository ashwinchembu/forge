from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.routes.api import router
from app.routes.preview import router as preview_router
from app.routes.mobile import router as mobile_router
from app.database import setup_indexes
from app.services.sync_scheduler import run_scheduled_sync
from app.services.briefing import send_briefing
from app.config import get_settings


scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if not settings.preview_mode:
        try:
            await setup_indexes()
        except Exception as e:
            print(f"MongoDB unavailable ({e}). Set PREVIEW_MODE=true for local preview.")
    else:
        print("Preview mode — using demo data, MongoDB optional")

    # 1) Data sync: every N minutes (default 15)
    interval_min = settings.sync_interval_minutes
    await run_scheduled_sync()
    scheduler.add_job(
        run_scheduled_sync,
        "interval",
        minutes=interval_min,
        id="forge_data_sync",
    )
    print(f"Data sync: every {interval_min} minutes (Hevy + Oura)")

    # 2) iMessage briefings: at configured hours (default 7am, 1pm, 7pm)
    briefing_hours = [int(h.strip()) for h in settings.briefing_hours.split(",") if h.strip()]
    if settings.imessage_recipient and briefing_hours:
        for hour in briefing_hours:
            briefing_type = "morning" if hour == briefing_hours[0] else "check_in"
            scheduler.add_job(
                send_briefing,
                "cron",
                hour=hour,
                minute=0,
                args=[briefing_type],
                id=f"briefing_{hour}",
            )
        hours_str = ", ".join(f"{h}:00" for h in briefing_hours)
        print(f"iMessage briefings: {hours_str} -> {settings.imessage_recipient}")
    elif not settings.imessage_recipient:
        print("iMessage: no recipient set (add IMESSAGE_RECIPIENT to .env)")

    scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title="Forge",
    description="AI-powered fitness pipeline. Syncs Hevy, MFP, and Oura into one backend with program-aware analysis.",
    version="1.0.0",
    lifespan=lifespan,
)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(preview_router, prefix="/api")
app.include_router(mobile_router, prefix="/api")


@app.get("/app", response_class=RedirectResponse, include_in_schema=False)
async def app_redirect():
    return RedirectResponse(url="/api/app", status_code=302)


@app.get("/")
async def root():
    settings = get_settings()
    return {
        "app": "Forge",
        "status": "running",
        "preview_mode": settings.preview_mode,
        "docs": "/docs",
        "app_url": "/app",
        "preview": "/api/preview",
        "mobile_config": "/api/mobile/config",
    }


if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
