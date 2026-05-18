from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

_client: AsyncIOMotorClient | None = None
_db = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=5000,
        )
    return _client


def get_db():
    global _db
    if _db is None:
        settings = get_settings()
        _db = get_client()[settings.mongo_db]
    return _db


class _LazyCollection:
    """Defer MongoDB collection access until first use."""

    def __init__(self, name: str):
        self._name = name

    def __getattr__(self, item):
        return getattr(get_db()[self._name], item)


workouts_col = _LazyCollection("workouts")
nutrition_col = _LazyCollection("nutrition")
recovery_col = _LazyCollection("recovery")
body_metrics_col = _LazyCollection("body_metrics")
program_targets_col = _LazyCollection("program_targets")


async def setup_indexes():
    await workouts_col.create_index([("date", -1)])
    await workouts_col.create_index([("source", 1), ("source_id", 1)], unique=True, sparse=True)
    await nutrition_col.create_index([("date", -1)], unique=True)
    await recovery_col.create_index([("date", -1)], unique=True)
    await body_metrics_col.create_index([("date", -1)])
