import csv
import io
from datetime import datetime, date
from app.database import nutrition_col


async def parse_mfp_csv(file_content: str) -> dict:
    reader = csv.DictReader(io.StringIO(file_content))
    stats = {"rows_processed": 0, "days_upserted": 0}
    daily: dict[str, dict] = {}

    for row in reader:
        stats["rows_processed"] += 1
        d = row.get("Date", row.get("date", ""))
        if not d:
            continue

        # Parse date - MFP uses various formats
        parsed_date = None
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
            try:
                parsed_date = datetime.strptime(d, fmt).date()
                break
            except ValueError:
                continue
        if not parsed_date:
            continue

        date_key = str(parsed_date)

        if date_key not in daily:
            daily[date_key] = {
                "date": datetime.combine(parsed_date, datetime.min.time()),
                "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0,
                "fiber_g": 0, "sugar_g": 0, "sodium_mg": 0,
                "meals": [], "source": "mfp_csv",
            }

        # Map MFP column names (they vary between exports)
        cal = _get_float(row, ["Calories", "calories", "Energy (kcal)"])
        pro = _get_float(row, ["Protein (g)", "protein", "Protein"])
        carb = _get_float(row, ["Carbohydrates (g)", "carbs", "Carbohydrates"])
        fat = _get_float(row, ["Fat (g)", "fat", "Total Fat"])
        fiber = _get_float(row, ["Fiber (g)", "fiber", "Fiber"])
        sugar = _get_float(row, ["Sugar (g)", "sugar", "Sugar"])
        sodium = _get_float(row, ["Sodium (mg)", "sodium", "Sodium"])

        daily[date_key]["calories"] += cal
        daily[date_key]["protein_g"] += pro
        daily[date_key]["carbs_g"] += carb
        daily[date_key]["fat_g"] += fat
        daily[date_key]["fiber_g"] += fiber
        daily[date_key]["sugar_g"] += sugar
        daily[date_key]["sodium_mg"] += sodium

        # Track individual foods if available
        food_name = row.get("Food Name", row.get("food", row.get("Meal", "")))
        meal_name = row.get("Meal", row.get("meal", ""))
        if food_name:
            daily[date_key]["meals"].append({
                "name": meal_name,
                "foods": [food_name],
                "calories": cal,
                "protein_g": pro,
                "carbs_g": carb,
                "fat_g": fat,
            })

    for doc in daily.values():
        # Round values
        for k in ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg"]:
            doc[k] = round(doc[k], 1)

        await nutrition_col.update_one(
            {"date": doc["date"]},
            {"$set": doc},
            upsert=True,
        )
        stats["days_upserted"] += 1

    return stats


def _get_float(row: dict, keys: list[str]) -> float:
    for k in keys:
        val = row.get(k)
        if val is not None and val != "":
            try:
                return float(str(val).replace(",", ""))
            except ValueError:
                continue
    return 0.0
