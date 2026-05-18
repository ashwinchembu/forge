from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Query
from datetime import date, datetime
from app.config import get_settings
from app.services import hevy_service, hae_service, mfp_service, analysis_service, oura_service
from app.services.sync_scheduler import run_scheduled_sync, get_sync_status
from app.services.briefing import send_briefing, get_last_briefing
from app.services import food_vision, barcode
from app.database import workouts_col, nutrition_col, recovery_col, body_metrics_col

router = APIRouter()


@router.get("/sync/status")
async def sync_status():
    return get_sync_status()


@router.post("/briefing/send")
async def trigger_briefing(briefing_type: str = "check_in"):
    """Send an iMessage briefing right now."""
    result = await send_briefing(briefing_type)
    return result


@router.get("/briefing/last")
async def last_briefing():
    """Last briefing sent."""
    return get_last_briefing() or {"message": "No briefing sent yet"}


@router.post("/food/photo")
async def analyze_food_photo(file: UploadFile = File(...)):
    """Upload a food photo, get macro breakdown via GPT-4o vision."""
    image_data = await file.read()
    mime = file.content_type or "image/jpeg"
    result = await food_vision.analyze_food_photo(image_data, mime)
    return result


@router.get("/food/barcode/{upc}")
async def lookup_barcode_endpoint(upc: str):
    """Look up nutrition by barcode/UPC number."""
    result = await barcode.lookup_barcode(upc)
    return result


@router.post("/food/search")
async def search_food_endpoint(query: str = Query(..., description="e.g. '2 eggs and a banana'")):
    """Natural language food search via Nutritionix."""
    result = await barcode.search_food(query)
    return result


# ---- Health Auto Export Webhook ----

@router.post("/webhook/health-auto-export")
async def receive_hae_data(payload: dict, authorization: str = Header(default="")):
    settings = get_settings()
    if settings.webhook_secret and authorization != f"Bearer {settings.webhook_secret}":
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    stats = await hae_service.process_hae_payload(payload)
    return {"status": "ok", "ingested": stats}


# ---- Hevy Sync ----

@router.post("/sync/hevy")
async def sync_hevy():
    try:
        result = await hevy_service.sync_hevy_workouts()
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/oura")
async def sync_oura(days: int = 7):
    try:
        result = await oura_service.sync_oura(days_back=days)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/all")
async def sync_all():
    results = await run_scheduled_sync()
    return {"status": "ok", "results": results}


# ---- MFP CSV Upload ----

@router.post("/upload/mfp-csv")
async def upload_mfp_csv(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    stats = await mfp_service.parse_mfp_csv(text)
    return {"status": "ok", "result": stats}


# ---- Analysis ----

@router.get("/analysis/today")
async def analyze_today(program_start: str = Query(..., description="YYYY-MM-DD")):
    start = date.fromisoformat(program_start)
    result = await analysis_service.analyze_day(date.today(), start)
    return result


@router.get("/analysis/day/{target_date}")
async def analyze_specific_day(target_date: str, program_start: str = Query(...)):
    start = date.fromisoformat(program_start)
    target = date.fromisoformat(target_date)
    result = await analysis_service.analyze_day(target, start)
    return result


@router.get("/analysis/week/{week_num}")
async def analyze_week(week_num: int, program_start: str = Query(...)):
    start = date.fromisoformat(program_start)
    result = await analysis_service.weekly_summary(start, week_num)
    return result


# ---- Data Retrieval ----

@router.get("/workouts")
async def get_workouts(days: int = 7):
    cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0) - __import__("datetime").timedelta(days=days)
    cursor = workouts_col.find({"date": {"$gte": cutoff}}).sort("date", -1)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results


@router.get("/nutrition")
async def get_nutrition(days: int = 7):
    cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0) - __import__("datetime").timedelta(days=days)
    cursor = nutrition_col.find({"date": {"$gte": cutoff}}).sort("date", -1)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results


@router.get("/recovery")
async def get_recovery(days: int = 7):
    cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0) - __import__("datetime").timedelta(days=days)
    cursor = recovery_col.find({"date": {"$gte": cutoff}}).sort("date", -1)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results


@router.get("/body-metrics")
async def get_body_metrics(days: int = 30):
    cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0) - __import__("datetime").timedelta(days=days)
    cursor = body_metrics_col.find({"date": {"$gte": cutoff}}).sort("date", -1)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results


# ---- Program Info ----

@router.get("/program/targets/{week}")
async def get_weekly_targets(week: int):
    phase = analysis_service.get_phase(week)
    program = {}
    for day_name, exercises in analysis_service.PROGRAM.items():
        program[day_name] = {}
        for ex_name, target in exercises.items():
            program[day_name][ex_name] = {
                "sets": target["sets"],
                "reps": f'{target["rep_low"]}-{target["rep_high"]}',
                "weight": target["weekly_weights"].get(week, 0),
                "rest_seconds": target["rest"],
            }
    return {"week": week, "phase": phase, "program": program}


@router.get("/program/schedule")
async def get_schedule():
    return {
        "Monday": "Upper A - Bench Priority",
        "Tuesday": "Lower A - Quad Focus",
        "Wednesday": "Rest (30 min incline walk)",
        "Thursday": "Upper B - Volume + Bench Support",
        "Friday": "Lower B - Hip/Hamstring Focus",
        "Saturday": "Rest (30 min incline walk)",
        "Sunday": "Rest (30 min incline walk)",
    }
