from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.routes.api import router
from app.database import setup_indexes
from app.services.hevy_service import sync_hevy_workouts
from app.services.oura_service import sync_oura
from app.config import get_settings


scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_indexes()
    settings = get_settings()
    if settings.hevy_api_key:
        scheduler.add_job(sync_hevy_workouts, "interval", hours=6, id="hevy_sync")
        print("Hevy auto-sync scheduled every 6 hours")
    if settings.oura_access_token:
        scheduler.add_job(sync_oura, "interval", hours=6, id="oura_sync")
        print("Oura auto-sync scheduled every 6 hours")
    if scheduler.get_jobs():
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"app": "Forge", "status": "running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
