"""Build and send daily briefing messages via Telegram."""

import logging
from datetime import datetime, timezone
from app.config import get_settings
from app.services.telegram import send_message

log = logging.getLogger("forge.briefing")

_last_briefing: dict | None = None


def get_last_briefing() -> dict | None:
    return _last_briefing


def _format_briefing(data: dict, briefing_type: str = "morning") -> str:
    lines = []

    if briefing_type == "morning":
        lines.append("FORGE — Morning Briefing")
    else:
        lines.append("FORGE — Check-in")

    lines.append(f"Week {data.get('week', '?')} · {data.get('phase', '?').upper()}")
    lines.append("")

    workout = data.get("expected_workout")
    if workout:
        lines.append(f"Today: {workout}")
    else:
        lines.append("Today: Rest day")

    score = data.get("score")
    if score is not None:
        if score >= 80:
            lines.append(f"Score: {score}/100")
        elif score >= 50:
            lines.append(f"Score: {score}/100 — room to improve")
        else:
            lines.append(f"Score: {score}/100 — needs attention")

    nutrition = data.get("nutrition")
    if nutrition:
        cal = nutrition.get("calories", 0)
        cal_target = nutrition.get("target_calories", 0)
        pro = nutrition.get("protein_g", 0)
        pro_target = nutrition.get("target_protein_g", 0)
        cal_delta = cal - cal_target
        sign = "+" if cal_delta > 0 else ""
        lines.append(f"Cal: {cal}/{cal_target} ({sign}{cal_delta})")
        lines.append(f"Protein: {pro}g/{pro_target}g")

    recovery = data.get("recovery")
    if recovery:
        parts = []
        if recovery.get("sleep_hours"):
            parts.append(f"Sleep {recovery['sleep_hours']}h")
        if recovery.get("hrv_ms"):
            parts.append(f"HRV {recovery['hrv_ms']}")
        if recovery.get("resting_heart_rate"):
            parts.append(f"RHR {recovery['resting_heart_rate']}")
        if parts:
            lines.append(" · ".join(parts))

    workout_data = data.get("workout")
    if workout_data:
        hit_rate = workout_data.get("hit_rate", 0)
        pct = int(hit_rate * 100)
        lines.append(f"Lifts: {pct}% hit rate")
        missed = [e["exercise"].split("(")[0].strip()
                  for e in workout_data.get("exercises", [])
                  if e.get("status") == "missed"]
        if missed:
            lines.append(f"Missed: {', '.join(missed)}")

    recs = data.get("recommendations", [])
    if recs:
        lines.append("")
        lines.append(recs[0])

    return "\n".join(lines)


async def send_briefing(briefing_type: str = "morning") -> dict:
    global _last_briefing
    settings = get_settings()

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        log.warning("Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return {"sent": False, "error": "telegram_not_configured"}

    now = datetime.now(timezone.utc)

    if settings.preview_mode:
        from app.services.preview_data import DASHBOARD
        analysis = DASHBOARD
    else:
        from app.services.analysis_service import analyze_day
        from datetime import date as d
        program_start = d.fromisoformat(settings.program_start)
        analysis = await analyze_day(d.today(), program_start)

    message = _format_briefing(analysis, briefing_type)
    result = await send_message(message, parse_mode=None)

    _last_briefing = {
        "at": now.isoformat(),
        "type": briefing_type,
        "message": message,
        "result": result,
    }

    return _last_briefing
