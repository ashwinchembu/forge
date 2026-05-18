import httpx
from datetime import date, datetime, timedelta
from app.config import get_settings
from app.database import recovery_col

OURA_BASE = "https://api.ouraring.com/v2"


def _headers():
    s = get_settings()
    return {"Authorization": f"Bearer {s.oura_access_token}"}


async def fetch_sleep(start_date: date, end_date: date) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{OURA_BASE}/usercollection/daily_sleep",
            headers=_headers(),
            params={"start_date": str(start_date), "end_date": str(end_date)},
        )
        resp.raise_for_status()
        return resp.json().get("data", [])


async def fetch_readiness(start_date: date, end_date: date) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{OURA_BASE}/usercollection/daily_readiness",
            headers=_headers(),
            params={"start_date": str(start_date), "end_date": str(end_date)},
        )
        resp.raise_for_status()
        return resp.json().get("data", [])


async def fetch_activity(start_date: date, end_date: date) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{OURA_BASE}/usercollection/daily_activity",
            headers=_headers(),
            params={"start_date": str(start_date), "end_date": str(end_date)},
        )
        resp.raise_for_status()
        return resp.json().get("data", [])


async def sync_oura(days_back: int = 7) -> dict:
    end = date.today()
    start = end - timedelta(days=days_back)
    stats = {"days_updated": 0}

    sleep_data = await fetch_sleep(start, end)
    readiness_data = await fetch_readiness(start, end)
    activity_data = await fetch_activity(start, end)

    # Index by date
    readiness_by_date = {r["day"]: r for r in readiness_data}
    activity_by_date = {a["day"]: a for a in activity_data}

    for sleep in sleep_data:
        d = sleep.get("day", "")
        if not d:
            continue

        dt = datetime.combine(date.fromisoformat(d), datetime.min.time())
        readiness = readiness_by_date.get(d, {})
        activity = activity_by_date.get(d, {})

        contributors = sleep.get("contributors", {})

        doc = {
            "date": dt,
            "source": "oura",
            "sleep": {
                "total_hours": round(sleep.get("total_sleep_duration", 0) / 3600, 2),
                "deep_hours": round(sleep.get("deep_sleep_duration", 0) / 3600, 2),
                "rem_hours": round(sleep.get("rem_sleep_duration", 0) / 3600, 2),
                "light_hours": round(sleep.get("light_sleep_duration", 0) / 3600, 2),
                "sleep_score": sleep.get("score"),
            },
            "resting_heart_rate": contributors.get("resting_heart_rate"),
            "hrv_ms": contributors.get("hrv_balance"),
            "readiness_score": readiness.get("score"),
            "activity_score": activity.get("score"),
            "steps": activity.get("steps"),
        }

        await recovery_col.update_one(
            {"date": dt},
            {"$set": doc},
            upsert=True,
        )
        stats["days_updated"] += 1

    return stats
