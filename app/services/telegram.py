"""Telegram Bot — send messages and handle incoming photos/barcodes."""

import logging
import httpx
from app.config import get_settings

log = logging.getLogger("forge.telegram")

_BASE = "https://api.telegram.org/bot"


def _url(method: str) -> str:
    return f"{_BASE}{get_settings().telegram_bot_token}/{method}"


async def send_message(text: str, chat_id: str | None = None, parse_mode: str = "Markdown") -> dict:
    settings = get_settings()
    cid = chat_id or settings.telegram_chat_id
    if not cid or not settings.telegram_bot_token:
        return {"sent": False, "error": "telegram not configured"}

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(_url("sendMessage"), json={
            "chat_id": cid,
            "text": text,
            "parse_mode": parse_mode,
        })
    data = r.json()
    if data.get("ok"):
        log.info(f"Telegram message sent to {cid}")
        return {"sent": True}
    log.error(f"Telegram error: {data}")
    return {"sent": False, "error": data.get("description", "unknown")}


async def send_photo_reply(chat_id: str, text: str) -> dict:
    return await send_message(text, chat_id=chat_id)


async def get_file_url(file_id: str) -> str | None:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(_url("getFile"), json={"file_id": file_id})
    data = r.json()
    if data.get("ok"):
        path = data["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{path}"
    return None


async def download_file(file_id: str) -> bytes | None:
    url = await get_file_url(file_id)
    if not url:
        return None
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
    return r.content if r.status_code == 200 else None


async def set_webhook(webhook_url: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(_url("setWebhook"), json={"url": webhook_url})
    return r.json()
