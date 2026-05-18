from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.routes.api import router
from app.routes.preview import router as preview_router
from app.routes.mobile import router as mobile_router
from app.database import setup_indexes
from app.services.sync_scheduler import run_scheduled_sync, get_sync_status
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

    interval = settings.sync_interval_hours
    await run_scheduled_sync()
    scheduler.add_job(
        run_scheduled_sync,
        "interval",
        hours=interval,
        id="forge_sync",
    )
    scheduler.start()
    print(f"Data sync scheduled every {interval} hours (Hevy + Oura)")
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
        "app": "/app",
        "preview": "/api/preview",
        "mobile_config": "/api/mobile/config",
    }


if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
