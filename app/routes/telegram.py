"""Telegram webhook — receives photos, barcodes, and text food queries."""

import logging
import re
from fastapi import APIRouter, Request
from app.services import telegram, food_vision, barcode
from app.config import get_settings

log = logging.getLogger("forge.telegram_webhook")

router = APIRouter(prefix="/telegram", tags=["telegram"])

UPC_PATTERN = re.compile(r"^\d{8,14}$")


@router.post("/webhook")
async def telegram_webhook(request: Request):
    body = await request.json()
    message = body.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))

    if not chat_id:
        return {"ok": True}

    # Photo message → food vision analysis
    if message.get("photo"):
        await telegram.send_message("Analyzing your food...", chat_id=chat_id)

        photos = message["photo"]
        best = max(photos, key=lambda p: p.get("file_size", 0))
        image_data = await telegram.download_file(best["file_id"])

        if not image_data:
            await telegram.send_message("Could not download the photo.", chat_id=chat_id)
            return {"ok": True}

        result = await food_vision.analyze_food_photo(image_data)
        reply = food_vision.format_macros_message(result)
        await telegram.send_message(reply, chat_id=chat_id)
        return {"ok": True}

    text = (message.get("text") or "").strip()
    if not text:
        return {"ok": True}

    # /start command
    if text.startswith("/start"):
        settings = get_settings()
        welcome = (
            "*Welcome to Forge* 🏋️\n\n"
            "Send me:\n"
            "📸 *Photo of food* → instant macro breakdown\n"
            "🔢 *Barcode number* (UPC) → product nutrition\n"
            "✍️ *Text* like \"2 eggs and toast\" → calorie lookup\n"
            f"\nYour chat ID: `{chat_id}`"
        )
        if not settings.telegram_chat_id:
            welcome += f"\n\n⚠️ Add this to your .env to receive briefings:\n`TELEGRAM_CHAT_ID={chat_id}`"
        await telegram.send_message(welcome, chat_id=chat_id)
        return {"ok": True}

    # /score command — today's analysis
    if text.startswith("/score"):
        settings = get_settings()
        if settings.preview_mode:
            from app.services.preview_data import DASHBOARD
            analysis = DASHBOARD
        else:
            from app.services.analysis_service import analyze_day
            from datetime import date
            program_start = date.fromisoformat(settings.program_start)
            analysis = await analyze_day(date.today(), program_start)

        from app.services.briefing import _format_briefing
        msg = _format_briefing(analysis, "check_in")
        await telegram.send_message(msg, chat_id=chat_id, parse_mode=None)
        return {"ok": True}

    # Barcode (8-14 digits)
    if UPC_PATTERN.match(text):
        await telegram.send_message("Looking up barcode...", chat_id=chat_id)
        result = await barcode.lookup_barcode(text)
        reply = barcode.format_barcode_message(result)
        await telegram.send_message(reply, chat_id=chat_id)
        return {"ok": True}

    # Text food query → Nutritionix natural language
    await telegram.send_message("Looking up nutrition...", chat_id=chat_id)
    result = await barcode.search_food(text)
    reply = barcode.format_search_message(result)
    await telegram.send_message(reply, chat_id=chat_id)
    return {"ok": True}
