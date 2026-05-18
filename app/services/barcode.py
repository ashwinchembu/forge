"""Barcode/UPC nutrition lookup via Open Food Facts (free, no API key needed)."""

import logging
import httpx

log = logging.getLogger("forge.barcode")

OFF_BASE = "https://world.openfoodfacts.org/api/v2"
OFF_HEADERS = {"User-Agent": "Forge/1.0 (fitness tracker)"}


def _sodium_mg(n: dict) -> float:
    """Open Food Facts stores sodium in grams; convert to mg. Cap at 10000."""
    val = n.get("sodium_serving", n.get("sodium_100g", 0)) or 0
    if val > 100:
        return val
    return min(val * 1000, 10000)


async def lookup_barcode(upc: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{OFF_BASE}/product/{upc}",
            headers=OFF_HEADERS,
            params={"fields": "product_name,brands,serving_size,nutriments,image_thumb_url"},
        )

    if r.status_code == 404:
        return {"error": f"No product found for barcode {upc}"}
    if r.status_code != 200:
        log.error(f"Open Food Facts error {r.status_code}: {r.text[:200]}")
        return {"error": f"API error: {r.status_code}"}

    data = r.json()
    if data.get("status") == 0:
        return {"error": f"No product found for barcode {upc}"}

    product = data.get("product", {})
    n = product.get("nutriments", {})

    return {
        "name": product.get("product_name", "Unknown"),
        "brand": product.get("brands", ""),
        "serving": product.get("serving_size", "per 100g"),
        "calories": round(n.get("energy-kcal_serving", n.get("energy-kcal_100g", 0))),
        "protein_g": round(n.get("proteins_serving", n.get("proteins_100g", 0))),
        "carbs_g": round(n.get("carbohydrates_serving", n.get("carbohydrates_100g", 0))),
        "fat_g": round(n.get("fat_serving", n.get("fat_100g", 0))),
        "fiber_g": round(n.get("fiber_serving", n.get("fiber_100g", 0)), 1),
        "sugar_g": round(n.get("sugars_serving", n.get("sugars_100g", 0)), 1),
        "sodium_mg": round(_sodium_mg(n)),
        "photo": product.get("image_thumb_url"),
        "source": "Open Food Facts",
    }


async def search_food(query: str) -> dict:
    """Search Open Food Facts by product name."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{OFF_BASE}/search",
            headers=OFF_HEADERS,
            params={
                "search_terms": query,
                "fields": "product_name,brands,nutriments,serving_size",
                "page_size": 5,
                "sort_by": "popularity",
            },
        )

    if r.status_code != 200:
        return {"error": f"Search error: {r.status_code}"}

    data = r.json()
    products = data.get("products", [])
    if not products:
        return {"error": f"No results for '{query}'"}

    items = []
    for p in products[:5]:
        n = p.get("nutriments", {})
        items.append({
            "name": p.get("product_name", "Unknown"),
            "brand": p.get("brands", ""),
            "serving": p.get("serving_size", "per 100g"),
            "calories": round(n.get("energy-kcal_serving", n.get("energy-kcal_100g", 0))),
            "protein_g": round(n.get("proteins_serving", n.get("proteins_100g", 0))),
            "carbs_g": round(n.get("carbohydrates_serving", n.get("carbohydrates_100g", 0))),
            "fat_g": round(n.get("fat_serving", n.get("fat_100g", 0))),
        })

    return {"items": items, "source": "Open Food Facts"}


def format_barcode_message(result: dict) -> str:
    if "error" in result and "name" not in result:
        return f"Could not look up barcode: {result['error']}"

    lines = [f"*{result['name']}*"]
    if result.get("brand"):
        lines[0] += f" ({result['brand']})"
    lines.append(f"Serving: {result.get('serving', '?')}")
    lines.append(
        f"\n{result.get('calories', 0)} cal | "
        f"{result.get('protein_g', 0)}P | "
        f"{result.get('carbs_g', 0)}C | "
        f"{result.get('fat_g', 0)}F"
    )
    if result.get("fiber_g"):
        lines.append(f"Fiber: {result['fiber_g']}g")
    if result.get("sugar_g"):
        lines.append(f"Sugar: {result['sugar_g']}g")

    return "\n".join(lines)


def format_search_message(result: dict) -> str:
    if "error" in result:
        return f"Could not find food: {result['error']}"

    lines = ["*Food Search Results*\n"]
    for item in result.get("items", []):
        name = item.get("name", "?")
        brand = f" ({item['brand']})" if item.get("brand") else ""
        lines.append(f"*{name}*{brand}")
        lines.append(
            f"  {item.get('calories', 0)} cal | "
            f"{item.get('protein_g', 0)}P | "
            f"{item.get('carbs_g', 0)}C | "
            f"{item.get('fat_g', 0)}F"
        )
        lines.append("")

    return "\n".join(lines)
