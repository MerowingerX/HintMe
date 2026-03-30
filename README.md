# 🧭 WhatsApp Social Compass

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
