import os
import json
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from analyzer import analyze_message
from sender import send_hint
from context import ContextStore

load_dotenv()

app = FastAPI(title="WhatsApp Social Compass")
context = ContextStore()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
APP_SECRET   = os.getenv("WHATSAPP_APP_SECRET")
USER_PHONE   = os.getenv("USER_PHONE_NUMBER")  # die Nummer der Person


def verify_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(APP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(params.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Invalid verify token")


@app.post("/webhook")
async def receive_message(request: Request):
    signature = request.headers.get("X-Hub-Signature-256", "")
    body = await request.body()

    if APP_SECRET and not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = json.loads(body)

    try:
        entry = data["entry"][0]["changes"][0]["value"]
        messages = entry.get("messages", [])
        metadata = entry.get("metadata", {})

        for msg in messages:
            if msg["type"] != "text":
                continue

            sender     = msg["from"]
            text       = msg["text"]["body"]
            msg_id     = msg["id"]
            chat_name  = entry.get("contacts", [{}])[0].get("profile", {}).get("name", sender)
            is_group   = sender != USER_PHONE

            ctx = context.get(sender)
            context.add(sender, {"role": "contact", "text": text})

            hint = await analyze_message(
                text=text,
                sender=chat_name,
                is_group=is_group,
                history=ctx
            )

            if hint:
                await send_hint(hint, reference_id=msg_id)

    except (KeyError, IndexError):
        pass  # Kein gültiger Nachrichtenblock

    return {"status": "ok"}
