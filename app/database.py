from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()
client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db]

# Collections
workouts_col = db["workouts"]
nutrition_col = db["nutrition"]
recovery_col = db["recovery"]
body_metrics_col = db["body_metrics"]
program_targets_col = db["program_targets"]


async def setup_indexes():
    await workouts_col.create_index([("date", -1)])
    await workouts_col.create_index([("source", 1), ("source_id", 1)], unique=True, sparse=True)
    await nutrition_col.create_index([("date", -1)], unique=True)
    await recovery_col.create_index([("date", -1)], unique=True)
    await body_metrics_col.create_index([("date", -1)])
