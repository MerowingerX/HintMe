# WhatsApp Social Compass

> Ein KI-gestützter Filter für WhatsApp, der autistischen Nutzerinnen hilft, soziale Kommunikation einzuordnen.

Jede eingehende WhatsApp-Nachricht wird automatisch analysiert. Der Nutzer bekommt einen kurzen Hinweis in einem eigenen Chat:

- 🔵 **Nicht an dich gerichtet** – die Nachricht galt jemand anderem
- 🟡 **Keine Antwort nötig** – es wird keine Reaktion erwartet
- 😄 **Humor / Ironie erkannt** – wahrscheinlich nicht wörtlich gemeint
- ⚠️ **Sarkasmus erkannt** – Vorsicht, möglicherweise nicht ernst gemeint

Alle Regeln sind in `config/rules.yaml` konfigurierbar – ohne Programmierkenntnisse.

---

## Architektur

```
Eingehende WhatsApp-Nachricht
            ↓
Meta Cloud API Webhook (FastAPI)
            ↓
      KI-Analyse (Claude / Llama)
            ↓
  Hint → per Business API an Nutzer
```

---

## Dokumentation

| Dokument | Inhalt |
|---|---|
| [ONBOARDING.md](ONBOARDING.md) | Vollständige Einrichtung Schritt für Schritt |
| [PHONE_NUMBER.md](PHONE_NUMBER.md) | Welche Telefonnummer du brauchst (und welche nicht) |
| [ALTERNATIVE_MODEL.md](ALTERNATIVE_MODEL.md) | Llama / Groq statt Claude verwenden |

---

## Schnellstart

```bash
git clone https://github.com/MerowingerX/whatsapp-social-compass
cd whatsapp-social-compass
cp .env.example .env
cp config/rules.example.yaml config/rules.yaml
# .env und config/rules.yaml anpassen
docker compose up -d
```

Die vollständige Anleitung inkl. Meta-Setup und Webhook-Registrierung: [ONBOARDING.md](ONBOARDING.md)

---

## Konfiguration

`config/rules.yaml` steuert, was analysiert wird und wie die Hinweise formuliert sind:

```yaml
user:
  name: "Anna"

rules:
  humor_irony:
    enabled: true
    hint: "Das ist wahrscheinlich nicht ernst gemeint: {explanation}"

  sarcasm:
    enabled: true
    sensitivity: high   # low / medium / high
    hint: "Achtung – das könnte sarkastisch sein: {explanation}"
```

---

## Kosten

| Komponente | Kosten/Monat |
|---|---|
| Meta WhatsApp Cloud API | $0 (Service-Nachrichten kostenlos) |
| Claude Haiku (~100 Nachrichten/Tag) | ~$1 |
| VPS (z.B. Hetzner CX11) | ~€4 |
| **Gesamt** | **~€5** |

Mit Llama über Groq entfallen die KI-Kosten vollständig. Siehe [ALTERNATIVE_MODEL.md](ALTERNATIVE_MODEL.md).

---

## Lizenz

MIT
