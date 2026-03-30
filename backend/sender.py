import os
import httpx

PHONE_ID    = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
COMPASS_CHAT = os.getenv("COMPASS_CHAT_ID")  # Ziel-Nummer für Hints (= User selbst)
API_URL     = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"


async def send_hint(text: str, reference_id: str | None = None):
    payload = {
        "messaging_product": "whatsapp",
        "to": COMPASS_CHAT,
        "type": "text",
        "text": {"body": text, "preview_url": False}
    }
    if reference_id:
        payload["context"] = {"message_id": reference_id}

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
