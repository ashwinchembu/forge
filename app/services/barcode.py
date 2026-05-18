"""Barcode/UPC nutrition lookup via Nutritionix API."""

import logging
import httpx
from app.config import get_settings

log = logging.getLogger("forge.barcode")


async def lookup_barcode(upc: str) -> dict:
    settings = get_settings()
    if not settings.nutritionix_app_id or not settings.nutritionix_api_key:
        return {"error": "Nutritionix API not configured (set NUTRITIONIX_APP_ID and NUTRITIONIX_API_KEY)"}

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"https://trackapi.nutritionix.com/v2/search/item?upc={upc}",
            headers={
                "x-app-id": settings.nutritionix_app_id,
                "x-app-key": settings.nutritionix_api_key,
            },
        )

    if r.status_code == 404:
        return {"error": f"No product found for barcode {upc}"}
    if r.status_code != 200:
        log.error(f"Nutritionix error {r.status_code}: {r.text}")
        return {"error": f"Nutritionix API error: {r.status_code}"}

    data = r.json()
    foods = data.get("foods", [])
    if not foods:
        return {"error": f"No nutrition data for barcode {upc}"}

    food = foods[0]
    return {
        "name": food.get("food_name", "Unknown"),
        "brand": food.get("brand_name", ""),
        "serving": f"{food.get('serving_qty', 1)} {food.get('serving_unit', 'serving')}",
        "serving_weight_g": food.get("serving_weight_grams"),
        "calories": round(food.get("nf_calories", 0)),
        "protein_g": round(food.get("nf_protein", 0)),
        "carbs_g": round(food.get("nf_total_carbohydrate", 0)),
        "fat_g": round(food.get("nf_total_fat", 0)),
        "fiber_g": round(food.get("nf_dietary_fiber", 0), 1),
        "sugar_g": round(food.get("nf_sugars", 0), 1),
        "sodium_mg": round(food.get("nf_sodium", 0)),
        "photo": food.get("photo", {}).get("thumb"),
    }


async def search_food(query: str) -> dict:
    """Natural language food search (e.g. '2 eggs and a banana')."""
    settings = get_settings()
    if not settings.nutritionix_app_id or not settings.nutritionix_api_key:
        return {"error": "Nutritionix API not configured"}

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            "https://trackapi.nutritionix.com/v2/natural/nutrients",
            headers={
                "x-app-id": settings.nutritionix_app_id,
                "x-app-key": settings.nutritionix_api_key,
                "Content-Type": "application/json",
            },
            json={"query": query},
        )

    if r.status_code != 200:
        return {"error": f"Nutritionix error: {r.status_code}"}

    data = r.json()
    items = []
    totals = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0}

    for food in data.get("foods", []):
        item = {
            "name": food.get("food_name", "Unknown"),
            "quantity": f"{food.get('serving_qty', 1)} {food.get('serving_unit', 'serving')}",
            "calories": round(food.get("nf_calories", 0)),
            "protein_g": round(food.get("nf_protein", 0)),
            "carbs_g": round(food.get("nf_total_carbohydrate", 0)),
            "fat_g": round(food.get("nf_total_fat", 0)),
            "fiber_g": round(food.get("nf_dietary_fiber", 0), 1),
        }
        items.append(item)
        for k in totals:
            totals[k] += item[k]

    for k in totals:
        totals[k] = round(totals[k], 1) if k == "fiber_g" else round(totals[k])

    return {"items": items, "totals": totals}


def format_barcode_message(result: dict) -> str:
    if "error" in result and "name" not in result:
        return f"Could not look up barcode: {result['error']}"

    lines = [f"*{result['name']}*"]
    if result.get("brand"):
        lines[0] += f" ({result['brand']})"
    lines.append(f"Serving: {result.get('serving', '?')}")
    lines.append(
        f"\n{result.get('calories', 0)} cal · "
        f"{result.get('protein_g', 0)}P · "
        f"{result.get('carbs_g', 0)}C · "
        f"{result.get('fat_g', 0)}F"
    )
    if result.get("fiber_g"):
        lines.append(f"Fiber: {result['fiber_g']}g")
    if result.get("sugar_g"):
        lines.append(f"Sugar: {result['sugar_g']}g")

    return "\n".join(lines)


def format_search_message(result: dict) -> str:
    if "error" in result:
        return f"Could not look up food: {result['error']}"

    lines = ["*Nutrition Lookup*\n"]
    for item in result.get("items", []):
        lines.append(f"*{item['name']}* ({item.get('quantity', '?')})")
        lines.append(
            f"  {item.get('calories', 0)} cal · "
            f"{item.get('protein_g', 0)}P · "
            f"{item.get('carbs_g', 0)}C · "
            f"{item.get('fat_g', 0)}F"
        )

    totals = result.get("totals", {})
    if totals:
        lines.append(f"\n*Totals:* {totals.get('calories', 0)} cal · "
                     f"{totals.get('protein_g', 0)}P · "
                     f"{totals.get('carbs_g', 0)}C · "
                     f"{totals.get('fat_g', 0)}F")
    return "\n".join(lines)
