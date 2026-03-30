
import os

os.makedirs("output/whatsapp-social-compass/backend", exist_ok=True)
os.makedirs("output/whatsapp-social-compass/config", exist_ok=True)

# main.py
main_py = '''import os
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
'''

# analyzer.py
analyzer_py = '''import os
import json
from anthropic import AsyncAnthropic
from config import RulesConfig

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
rules  = RulesConfig("config/rules.yaml")


def build_prompt(text: str, sender: str, is_group: bool, history: list) -> str:
    active = []
    if rules.is_enabled("addressee_check"):
        active.append("addressee_check: Geht diese Nachricht direkt an den Nutzer?")
    if rules.is_enabled("reply_needed"):
        active.append("reply_needed: Wird eine Antwort erwartet?")
    if rules.is_enabled("humor_irony"):
        active.append("humor_irony: Enthält sie Humor oder Ironie?")
    if rules.is_enabled("sarcasm"):
        active.append("sarcasm: Enthält sie Sarkasmus?")

    custom = rules.get_custom_rules()
    for rule in custom:
        if rule.get("enabled"):
            active.append(f"{rule[\'name\']}: {rule[\'condition\']}")

    checks = "\\n".join(f"- {a}" for a in active)
    history_text = "\\n".join(f"[{h[\'role\']}]: {h[\'text\']}" for h in history[-5:])
    user_name = rules.config["user"]["name"]

    return f"""Du hilfst {user_name}, WhatsApp-Nachrichten richtig einzuordnen.
{user_name} ist Autistin und braucht klare, freundliche Hinweise.

Aktive Prüfungen:
{checks}

Letzter Gesprächsverlauf:
{history_text or "(kein Kontext)"}

Neue Nachricht von "{sender}" ({'Gruppe' if is_group else 'Einzelchat'}):
"{text}"

Antworte NUR als JSON (kein Markdown):
{{
  "addressee": true | false | null,
  "reply_needed": true | false | null,
  "humor": false | {{"explanation": "..."}},
  "sarcasm": false | {{"explanation": "..."}},
  "custom": []
}}
null = nicht eindeutig bestimmbar"""


async def analyze_message(text: str, sender: str, is_group: bool, history: list) -> str | None:
    prompt = build_prompt(text, sender, is_group, history)
    style  = rules.config.get("hints", {}).get("style", "freundlich")
    lang   = rules.config.get("hints", {}).get("language", "de")
    model  = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")

    response = await client.messages.create(
        model=model,
        max_tokens=300,
        system=f"Antworte immer auf {lang}, Stil: {style}. Nur valides JSON, kein Markdown.",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        result = json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return None

    hints = []

    if result.get("addressee") is False and rules.is_enabled("addressee_check"):
        hints.append("🔵 " + rules.get_hint("addressee_check"))

    if result.get("reply_needed") is False and rules.is_enabled("reply_needed"):
        hints.append("🟡 " + rules.get_hint("reply_needed"))

    if result.get("humor") and rules.is_enabled("humor_irony"):
        explanation = result["humor"].get("explanation", "")
        hints.append("😄 " + rules.get_hint("humor_irony", explanation=explanation))

    if result.get("sarcasm") and rules.is_enabled("sarcasm"):
        explanation = result["sarcasm"].get("explanation", "")
        hints.append("⚠️ " + rules.get_hint("sarcasm", explanation=explanation))

    for item in result.get("custom", []):
        hints.append(f"ℹ️ {item}")

    if not hints:
        return None

    max_len = rules.config.get("hints", {}).get("max_length", 200)
    header  = f"📨 *{sender}*"
    body    = "\\n".join(hints)
    full    = f"{header}\\n{body}"
    return full[:max_len] if len(full) > max_len else full
'''

# config.py
config_py = '''import yaml


class RulesConfig:
    def __init__(self, path: str = "config/rules.yaml"):
        with open(path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def is_enabled(self, rule: str) -> bool:
        return self.config.get("rules", {}).get(rule, {}).get("enabled", False)

    def get_hint(self, rule: str, **kwargs) -> str:
        template = self.config["rules"][rule]["hint"]
        return template.format(**kwargs)

    def get_custom_rules(self) -> list:
        return self.config.get("custom_rules", [])
'''

# context.py
context_py = '''import os
import json
import redis

REDIS_URL    = os.getenv("REDIS_URL", "redis://localhost:6379")
WINDOW_SIZE  = int(os.getenv("CONTEXT_WINDOW", "10"))

r = redis.from_url(REDIS_URL, decode_responses=True)


class ContextStore:
    def get(self, chat_id: str) -> list:
        raw = r.get(f"ctx:{chat_id}")
        return json.loads(raw) if raw else []

    def add(self, chat_id: str, message: dict):
        history = self.get(chat_id)
        history.append(message)
        history = history[-WINDOW_SIZE:]
        r.set(f"ctx:{chat_id}", json.dumps(history), ex=86400)

    def clear(self, chat_id: str):
        r.delete(f"ctx:{chat_id}")
'''

# sender.py
sender_py = '''import os
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
'''

# rules.yaml
rules_yaml = '''user:
  name: "Anna"
  language: "de"

rules:
  addressee_check:
    enabled: true
    hint: "Diese Nachricht scheint nicht direkt an dich gerichtet zu sein."
    confidence_threshold: 0.7

  reply_needed:
    enabled: true
    hint: "Hier wird wahrscheinlich keine Antwort erwartet."

  humor_irony:
    enabled: true
    hint: "Das ist wahrscheinlich nicht ernst gemeint: {explanation}"

  sarcasm:
    enabled: true
    sensitivity: high  # low / medium / high
    hint: "Achtung – das könnte sarkastisch sein: {explanation}"

  outgoing_guard:
    enabled: true
    checks:
      - too_direct
      - inappropriate
      - oversharing
    hint: "Überlege nochmal, ob du das so schicken möchtest: {explanation}"

custom_rules:
  - name: "Gruppenkontext"
    enabled: true
    condition: "Nachricht in Gruppe ohne direkten @-Mention"
    hint: "In dieser Gruppe wurde niemand direkt angesprochen."

  - name: "Rhetorische Fragen"
    enabled: true
    condition: "Frage ohne echte Antworterwartung"
    hint: "Das ist wahrscheinlich eine rhetorische Frage."

hints:
  style: "freundlich"     # freundlich / neutral / direkt
  max_length: 300
  show_confidence: false
  language: "de"
'''

# rules.example.yaml (same as rules.yaml – template for new users)
rules_example_yaml = rules_yaml

# .env.example
env_example = '''# WhatsApp Business Cloud API
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_APP_SECRET=your_app_secret

# Die Telefonnummer der Person (Format: 491234567890)
USER_PHONE_NUMBER=49...
COMPASS_CHAT_ID=49...   # gleiche Nummer – Hints kommen im eigenen Chat an

# KI
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-haiku-4-5

# Redis
REDIS_URL=redis://redis:6379
CONTEXT_WINDOW=10
'''

# requirements.txt
requirements_txt = '''fastapi>=0.110.0
uvicorn[standard]>=0.29.0
anthropic>=0.25.0
httpx>=0.27.0
redis>=5.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
'''

# docker-compose.yml
docker_compose = '''services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env
    volumes:
      - ./config:/app/config
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
'''

# Dockerfile
dockerfile = '''FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY config/ ./config/

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

# README.md
readme_md = '''# 🧭 WhatsApp Social Compass

> An open-source AI filter for WhatsApp that helps autistic users navigate social communication.

## What it does

Every incoming WhatsApp message is automatically analyzed and the user receives a small hint in a dedicated chat:

- 🔵 **Not addressed to you** – message was directed at someone else
- 🟡 **No reply needed** – no response is expected
- 😄 **Humor / Irony detected** – this is probably not meant literally
- ⚠️ **Sarcasm detected** – be careful, this might not be sincere

All rules are fully configurable in `config/rules.yaml` – no coding required.

## Architecture

```
Incoming WhatsApp Message
        ↓
Meta Cloud API Webhook (FastAPI)
        ↓
Claude Haiku (AI Analysis)
        ↓
Hint → sent back to user via Business API
```

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/MerowingerX/whatsapp-social-compass
cd whatsapp-social-compass
cp .env.example .env
cp config/rules.example.yaml config/rules.yaml
# Edit .env and config/rules.yaml
```

### 2. Start

```bash
docker compose up -d
```

### 3. Expose webhook (dev)

```bash
ngrok http 8000
# Set the HTTPS URL as webhook in Meta Developer Console
# Webhook path: /webhook
```

### 4. Meta Setup

1. Create a [Meta Developer App](https://developers.facebook.com/apps)
2. Add WhatsApp product
3. Configure webhook URL + verify token (from your `.env`)
4. Subscribe to `messages` events

## Configuration

Edit `config/rules.yaml` to customize behavior per user:

```yaml
user:
  name: "Anna"

rules:
  humor_irony:
    enabled: true
    hint: "Das ist wahrscheinlich nicht ernst gemeint: {explanation}"
```

## Cost Estimate

| Component | Cost/month |
|---|---|
| Meta WhatsApp Cloud API | $0 (service messages free) |
| Claude Haiku 4.5 (~100 msgs/day) | ~$1 |
| VPS (e.g. Hetzner CX11) | ~€4 |
| **Total** | **~€5** |

## License

MIT
'''

files = {
    "output/whatsapp-social-compass/backend/main.py": main_py,
    "output/whatsapp-social-compass/backend/analyzer.py": analyzer_py,
    "output/whatsapp-social-compass/backend/config.py": config_py,
    "output/whatsapp-social-compass/backend/context.py": context_py,
    "output/whatsapp-social-compass/backend/sender.py": sender_py,
    "output/whatsapp-social-compass/config/rules.yaml": rules_yaml,
    "output/whatsapp-social-compass/config/rules.example.yaml": rules_example_yaml,
    "output/whatsapp-social-compass/.env.example": env_example,
    "output/whatsapp-social-compass/requirements.txt": requirements_txt,
    "output/whatsapp-social-compass/docker-compose.yml": docker_compose,
    "output/whatsapp-social-compass/Dockerfile": dockerfile,
    "output/whatsapp-social-compass/README.md": readme_md,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("All files written:")
for path in files:
    print(f"  {path}")