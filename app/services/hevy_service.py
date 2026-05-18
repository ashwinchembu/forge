import httpx
from datetime import datetime
from app.config import get_settings
from app.models.schemas import Workout, Exercise, ExerciseSet, WorkoutSource
from app.database import workouts_col

HEVY_BASE = "https://api.hevyapp.com/v1"


def _headers():
    s = get_settings()
    return {"api-key": s.hevy_api_key, "Accept": "application/json"}


async def fetch_workouts(page: int = 1, page_size: int = 10) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{HEVY_BASE}/workouts",
            headers=_headers(),
            params={"page": page, "pageSize": page_size},
        )
        resp.raise_for_status()
        return resp.json().get("workouts", [])


async def fetch_all_workouts(max_pages: int = 50) -> list[dict]:
    all_workouts = []
    for page in range(1, max_pages + 1):
        batch = await fetch_workouts(page=page, page_size=10)
        if not batch:
            break
        all_workouts.extend(batch)
    return all_workouts


def parse_hevy_workout(raw: dict) -> Workout:
    exercises = []
    for ex in raw.get("exercises", []):
        sets = []
        for i, s in enumerate(ex.get("sets", []), 1):
            sets.append(ExerciseSet(
                set_number=i,
                weight_lbs=s.get("weight_kg", 0) * 2.20462 if s.get("weight_kg") else s.get("weight_lbs", 0),
                reps=s.get("reps", 0),
                rpe=s.get("rpe"),
            ))
        exercises.append(Exercise(
            name=ex.get("title", ex.get("exercise_template_id", "Unknown")),
            sets=sets,
            notes=ex.get("notes"),
        ))

    total_vol = sum(s.weight_lbs * s.reps for e in exercises for s in e.sets)

    start = raw.get("start_time", raw.get("created_at", ""))
    end = raw.get("end_time", "")
    duration = None
    if start and end:
        try:
            t0 = datetime.fromisoformat(start.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(end.replace("Z", "+00:00"))
            duration = int((t1 - t0).total_seconds() / 60)
        except Exception:
            pass

    return Workout(
        date=datetime.fromisoformat(start.replace("Z", "+00:00")) if start else datetime.utcnow(),
        name=raw.get("title", "Untitled"),
        duration_minutes=duration,
        exercises=exercises,
        total_volume_lbs=round(total_vol, 1),
        source=WorkoutSource.hevy,
        source_id=raw.get("id", ""),
    )


async def sync_hevy_workouts() -> dict:
    raw_workouts = await fetch_all_workouts()
    new_count = 0
    updated_count = 0

    for raw in raw_workouts:
        workout = parse_hevy_workout(raw)
        doc = workout.model_dump()
        doc["date"] = doc["date"]

        result = await workouts_col.update_one(
            {"source": "hevy", "source_id": workout.source_id},
            {"$set": doc},
            upsert=True,
        )
        if result.upserted_id:
            new_count += 1
        elif result.modified_count:
            updated_count += 1

    return {"new": new_count, "updated": updated_count, "total_fetched": len(raw_workouts)}


async def get_exercise_templates() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{HEVY_BASE}/exercise_templates", headers=_headers(), params={"pageSize": 100})
        resp.raise_for_status()
        return resp.json().get("exercise_templates", [])
