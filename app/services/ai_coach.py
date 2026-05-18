"""AI-powered workout coaching using OpenAI GPT-4o."""

import json
import logging
import httpx
from app.config import get_settings

log = logging.getLogger("forge.ai_coach")

SYSTEM_PROMPT = """You are a strength coach analyzing a trainee's workout data from a structured hypertrophy program (Upper/Lower split, 4 days/week).

You will receive:
- Today's workout results (exercises, target vs actual weight, reps, hit/close/missed status)
- Recent nutrition (calories, protein vs targets)
- Recovery data (sleep, HRV, resting heart rate)
- Program context (current week, phase, upcoming workout)

Respond with ONLY valid JSON (no markdown, no code fences):

{
  "next_workout_adjustments": [
    {
      "exercise": "exercise name",
      "suggestion": "keep weight / increase to X / drop to X / add a set / etc",
      "reason": "brief reason"
    }
  ],
  "recovery_note": "one sentence on recovery status",
  "nutrition_note": "one sentence on nutrition adjustments",
  "overall": "1-2 sentence summary of what to focus on next session"
}

Rules:
- If an exercise was "hit" at target weight with reps at the high end of range, suggest increasing weight by 5 lbs next session
- If "hit" but reps at the low end, suggest keeping the same weight
- If "close" (within 5% of target), suggest staying at current weight and focusing on form
- If "missed" by more than 5%, suggest dropping weight 5-10 lbs
- Factor in sleep (<7h = suggest conservative weights) and protein (under target = flag it)
- Be concise. This goes to a mobile notification."""


async def get_ai_suggestions(analysis: dict, next_workout_name: str | None = None) -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        return _rule_based_suggestions(analysis, next_workout_name)

    prompt = f"""Today's analysis:
{json.dumps(analysis, indent=2, default=str)}

Next scheduled workout: {next_workout_name or 'unknown'}

Give me specific weight/rep adjustments for the next session."""

    try:
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
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 600,
                },
            )

        if r.status_code != 200:
            log.error(f"OpenAI error {r.status_code}: {r.text[:200]}")
            return _rule_based_suggestions(analysis, next_workout_name)

        content = r.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]

        return json.loads(content.strip())
    except Exception as e:
        log.error(f"AI coach error: {e}")
        return _rule_based_suggestions(analysis, next_workout_name)


def _rule_based_suggestions(analysis: dict, next_workout_name: str | None = None) -> dict:
    """Fallback when OpenAI is unavailable."""
    adjustments = []
    workout = analysis.get("workout")

    if workout:
        for ex in workout.get("exercises", []):
            name = ex.get("exercise", "")
            status = ex.get("status", "")
            target_w = ex.get("target_weight", 0)
            actual_reps = ex.get("actual_reps", [])

            if status == "hit":
                rep_range = ex.get("target_reps", "6-8")
                high = int(rep_range.split("-")[-1]) if "-" in rep_range else 8
                if actual_reps and min(actual_reps) >= high:
                    adjustments.append({
                        "exercise": name,
                        "suggestion": f"Increase to {target_w + 5} lbs",
                        "reason": "Hit all reps at the top of the range",
                    })
                else:
                    adjustments.append({
                        "exercise": name,
                        "suggestion": f"Keep at {target_w} lbs",
                        "reason": "Hit target but room to grow in reps",
                    })
            elif status == "close":
                adjustments.append({
                    "exercise": name,
                    "suggestion": f"Stay at {ex.get('actual_weight', target_w)} lbs",
                    "reason": "Close to target — focus on form and full ROM",
                })
            elif status == "missed":
                drop = max(target_w - 10, 0)
                adjustments.append({
                    "exercise": name,
                    "suggestion": f"Drop to {drop} lbs",
                    "reason": "Missed target — reduce weight and rebuild",
                })

    recovery = analysis.get("recovery", {})
    sleep = recovery.get("sleep_hours")
    recovery_note = "Recovery data not available."
    if sleep:
        if sleep < 7:
            recovery_note = f"Only {sleep}h sleep. Go conservative on heavy compounds."
        else:
            recovery_note = f"{sleep}h sleep — recovery is solid."

    nutrition = analysis.get("nutrition", {})
    nutrition_note = "No nutrition data."
    if nutrition:
        pro_delta = nutrition.get("protein_delta", 0)
        if pro_delta < -10:
            nutrition_note = f"Protein is {abs(pro_delta)}g under target. Prioritize protein today."
        elif pro_delta < 0:
            nutrition_note = f"Protein slightly under ({abs(pro_delta)}g). Try to close the gap."
        else:
            nutrition_note = "Protein is on target."

    return {
        "next_workout_adjustments": adjustments,
        "recovery_note": recovery_note,
        "nutrition_note": nutrition_note,
        "overall": f"Next session: {next_workout_name or 'check schedule'}. "
                   + ("Sleep was low — keep intensity moderate." if sleep and sleep < 7
                      else "You're recovering well — push the weights."),
    }


def format_suggestions_message(suggestions: dict) -> str:
    lines = ["*Next Workout Plan*\n"]

    for adj in suggestions.get("next_workout_adjustments", []):
        name = adj["exercise"].split("(")[0].strip()
        lines.append(f"*{name}*: {adj['suggestion']}")
        lines.append(f"  _{adj['reason']}_")

    if suggestions.get("recovery_note"):
        lines.append(f"\n{suggestions['recovery_note']}")
    if suggestions.get("nutrition_note"):
        lines.append(suggestions["nutrition_note"])
    if suggestions.get("overall"):
        lines.append(f"\n{suggestions['overall']}")

    return "\n".join(lines)
