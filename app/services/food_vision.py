"""Analyze food photos using OpenAI GPT-4o vision."""

import base64
import json
import logging
import httpx
from app.config import get_settings

log = logging.getLogger("forge.food_vision")

SYSTEM_PROMPT = """You are a precise nutrition analyzer. When shown a photo of food:

1. Identify every food item visible
2. Estimate portion sizes
3. Return ONLY valid JSON (no markdown, no code fences) with this structure:

{
  "items": [
    {
      "name": "food name",
      "quantity": "estimated portion (e.g. 1 cup, 6 oz, 1 medium)",
      "calories": 0,
      "protein_g": 0,
      "carbs_g": 0,
      "fat_g": 0,
      "fiber_g": 0
    }
  ],
  "totals": {
    "calories": 0,
    "protein_g": 0,
    "carbs_g": 0,
    "fat_g": 0,
    "fiber_g": 0
  },
  "confidence": "high/medium/low",
  "notes": "any relevant notes about the estimation"
}

Be accurate with portions. Use USDA data as reference. When unsure, estimate conservatively.
Round all numbers to integers except fiber (1 decimal)."""


async def analyze_food_photo(image_data: bytes, mime_type: str = "image/jpeg") -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        return {"error": "OpenAI API key not configured"}

    b64 = base64.b64encode(image_data).decode()

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Analyze this food and give me the macros."},
                        {"type": "image_url", "image_url": {
                            "url": f"data:{mime_type};base64,{b64}",
                            "detail": "high",
                        }},
                    ]},
                ],
                "max_tokens": 1000,
            },
        )

    if r.status_code != 200:
        log.error(f"OpenAI error {r.status_code}: {r.text}")
        return {"error": f"OpenAI API error: {r.status_code}"}

    content = r.json()["choices"][0]["message"]["content"]

    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        log.warning(f"Could not parse OpenAI response as JSON: {content[:200]}")
        return {"raw_response": content, "error": "could not parse structured data"}


def format_macros_message(result: dict) -> str:
    if "error" in result and "items" not in result:
        return f"Could not analyze: {result['error']}"

    lines = ["*Food Analysis*\n"]

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
        lines.append(f"\n*Totals*")
        lines.append(
            f"  {totals.get('calories', 0)} cal · "
            f"{totals.get('protein_g', 0)}g protein · "
            f"{totals.get('carbs_g', 0)}g carbs · "
            f"{totals.get('fat_g', 0)}g fat"
        )
        if totals.get("fiber_g"):
            lines.append(f"  Fiber: {totals['fiber_g']}g")

    if result.get("confidence"):
        lines.append(f"\nConfidence: {result['confidence']}")
    if result.get("notes"):
        lines.append(f"_{result['notes']}_")

    return "\n".join(lines)
