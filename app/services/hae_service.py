from datetime import datetime, date
from app.database import nutrition_col, recovery_col, body_metrics_col

# Mapping Health Auto Export metric names to our fields
NUTRITION_METRICS = {
    "dietary_energy": "calories",
    "dietary_protein": "protein_g",
    "dietary_carbohydrates": "carbs_g",
    "dietary_fat_total": "fat_g",
    "dietary_fiber": "fiber_g",
    "dietary_sugar": "sugar_g",
    "dietary_sodium": "sodium_mg",
    "dietary_water": "water_ml",
}

RECOVERY_METRICS = {
    "heart_rate": "resting_heart_rate",
    "heart_rate_variability": "hrv_ms",
    "resting_heart_rate": "resting_heart_rate",
    "sleep_analysis": "sleep",
    "apple_sleeping_wrist_temperature": "body_temp_deviation",
    "step_count": "steps",
}

BODY_METRICS_MAP = {
    "body_mass": "weight_lbs",
    "body_fat_percentage": "body_fat_pct",
    "lean_body_mass": "lean_mass_lbs",
}


def _parse_date(date_str: str) -> date:
    for fmt in ["%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()


def _aggregate_by_date(data_points: list[dict]) -> dict[date, float]:
    by_date = {}
    for dp in data_points:
        d = _parse_date(dp.get("date", ""))
        val = dp.get("qty") or dp.get("value") or 0
        if d in by_date:
            by_date[d] += val
        else:
            by_date[d] = val
    return by_date


def _aggregate_sleep_by_date(data_points: list[dict]) -> dict[date, dict]:
    by_date = {}
    for dp in data_points:
        d = _parse_date(dp.get("date", ""))
        val = dp.get("qty") or dp.get("value") or 0
        source = dp.get("source", "")
        category = dp.get("value", dp.get("category", ""))
        if d not in by_date:
            by_date[d] = {"total_hours": 0}
        by_date[d]["total_hours"] += val / 60 if val > 10 else val  # handle minutes vs hours
    return by_date


async def process_hae_payload(payload: dict) -> dict:
    metrics = payload.get("data", {}).get("metrics", [])
    stats = {"nutrition_days": 0, "recovery_days": 0, "body_days": 0}

    nutrition_by_date: dict[date, dict] = {}
    recovery_by_date: dict[date, dict] = {}
    body_by_date: dict[date, dict] = {}

    for metric in metrics:
        name = metric.get("name", "").lower().replace(" ", "_")
        data_points = metric.get("data", [])
        units = metric.get("units", "")

        if not data_points:
            continue

        # Nutrition metrics
        if name in NUTRITION_METRICS:
            field = NUTRITION_METRICS[name]
            by_date = _aggregate_by_date(data_points)
            for d, val in by_date.items():
                if d not in nutrition_by_date:
                    nutrition_by_date[d] = {"date": d, "source": "health_auto_export"}
                # Convert kJ to kcal if needed
                if "kj" in units.lower() and field == "calories":
                    val = val / 4.184
                nutrition_by_date[d][field] = round(val, 1)

        # Recovery metrics
        elif name in RECOVERY_METRICS:
            field = RECOVERY_METRICS[name]
            if name == "sleep_analysis":
                sleep_data = _aggregate_sleep_by_date(data_points)
                for d, sleep in sleep_data.items():
                    if d not in recovery_by_date:
                        recovery_by_date[d] = {"date": d, "source": "health_auto_export"}
                    recovery_by_date[d]["sleep"] = sleep
            else:
                by_date = _aggregate_by_date(data_points)
                for d, val in by_date.items():
                    if d not in recovery_by_date:
                        recovery_by_date[d] = {"date": d, "source": "health_auto_export"}
                    if field == "resting_heart_rate":
                        recovery_by_date[d][field] = round(val)
                    else:
                        recovery_by_date[d][field] = round(val, 2)

        # Body metrics
        elif name in BODY_METRICS_MAP:
            field = BODY_METRICS_MAP[name]
            by_date = _aggregate_by_date(data_points)
            for d, val in by_date.items():
                if d not in body_by_date:
                    body_by_date[d] = {"date": d}
                # Convert kg to lbs if needed
                if "kg" in units.lower():
                    val = val * 2.20462
                body_by_date[d][field] = round(val, 1)

    # Upsert nutrition
    for d, doc in nutrition_by_date.items():
        doc["date"] = datetime.combine(d, datetime.min.time())
        await nutrition_col.update_one(
            {"date": doc["date"]},
            {"$set": doc},
            upsert=True,
        )
        stats["nutrition_days"] += 1

    # Upsert recovery
    for d, doc in recovery_by_date.items():
        doc["date"] = datetime.combine(d, datetime.min.time())
        await recovery_col.update_one(
            {"date": doc["date"]},
            {"$set": doc},
            upsert=True,
        )
        stats["recovery_days"] += 1

    # Upsert body metrics
    for d, doc in body_by_date.items():
        doc["date"] = datetime.combine(d, datetime.min.time())
        await body_metrics_col.update_one(
            {"date": doc["date"]},
            {"$set": doc},
            upsert=True,
        )
        stats["body_days"] += 1

    return stats
