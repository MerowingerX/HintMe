# Onboarding – WhatsApp Social Compass

## Was du brauchst

**Accounts & Zugänge**

1. **Meta Developer Account** – kostenlos auf [developers.facebook.com](https://developers.facebook.com)
2. **WhatsApp Business-Nummer** – eine Telefonnummer, die als Business-Nummer registriert wird (kann eine normale SIM sein)
3. **Anthropic API Key** – für Claude Haiku ([console.anthropic.com](https://console.anthropic.com))
4. **Einen Server** – z.B. Hetzner CX11 (~€4/Monat), oder lokal mit ngrok zum Testen

---

## Schritt-für-Schritt Einrichtung

### 1. Repo klonen & konfigurieren

```bash
git clone https://github.com/MerowingerX/whatsapp-social-compass
cd whatsapp-social-compass
cp .env.example .env
cp config/rules.example.yaml config/rules.yaml
```

### 2. `.env` ausfüllen

| Variable | Woher |
|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | Meta Developer Console → WhatsApp → API Setup |
| `WHATSAPP_ACCESS_TOKEN` | Ebenda (temporär oder permanent via System User) |
| `WHATSAPP_APP_SECRET` | Meta App → Settings → Basic |
| `WHATSAPP_VERIFY_TOKEN` | Frei wählbar (z.B. `mein-geheimer-token-123`) |
| `USER_PHONE_NUMBER` | Deine eigene Nummer (Format: `4917612345678`) |
| `COMPASS_CHAT_ID` | Dieselbe Nummer – Hints kommen als Selbst-Nachrichten an |
| `ANTHROPIC_API_KEY` | Anthropic Console |
| `CLAUDE_MODEL` | Standard: `claude-haiku-4-5` |

### 3. `config/rules.yaml` anpassen

- `user.name` auf den richtigen Namen setzen
- Regeln nach Bedarf aktivieren/deaktivieren
- Hint-Texte nach eigenem Geschmack formulieren

```yaml
user:
  name: "Anna"

rules:
  humor_irony:
    enabled: true
    hint: "Das ist wahrscheinlich nicht ernst gemeint: {explanation}"
```

### 4. Docker starten

```bash
docker compose up -d
```

Startet zwei Container: die FastAPI-App auf Port 8000 und Redis.

### 5. Webhook bei Meta registrieren

**Lokal zum Testen (ngrok):**

```bash
ngrok http 8000
# → gibt eine HTTPS-URL wie https://abc123.ngrok.io aus
```

**In der Meta Developer Console:**

1. WhatsApp → Configuration → Webhook
2. Callback URL: `https://abc123.ngrok.io/webhook`
3. Verify Token: denselben Wert wie `WHATSAPP_VERIFY_TOKEN` in `.env`
4. Event abonnieren: `messages`

Meta sendet beim Speichern einen Verifikations-Request – die App antwortet automatisch korrekt.

---

## Wie das Programm funktioniert

```
Jemand schreibt eine WhatsApp-Nachricht an deine Business-Nummer
                        ↓
     Meta Cloud API → POST /webhook (mit HMAC-Signatur)
                        ↓
         main.py prüft Signatur, extrahiert Nachricht
                        ↓
     Redis: letzten Gesprächskontext laden (bis 10 Nachrichten)
                        ↓
              analyzer.py: Prompt an Claude Haiku
                        ↓
     Claude antwortet als JSON: { addressee, reply_needed, humor, sarcasm }
                        ↓
         Aus aktivierten Regeln werden Hints zusammengebaut
                        ↓
     sender.py: Hint-Nachricht an deine eigene Nummer schicken
```

### Was analysiert wird

| Regel | Was sie erkennt |
|---|---|
| `addressee_check` | Ist die Nachricht überhaupt an dich gerichtet? |
| `reply_needed` | Wird eine Antwort erwartet, oder ist es nur Info? |
| `humor_irony` | Ist das ein Witz / ironisch gemeint? |
| `sarcasm` | Könnte das sarkastisch sein? (Sensitivität: low / medium / high) |
| `custom_rules` | Frei definierbare Bedingungen in YAML |

### Beispiel

> Gruppenfreund schreibt: *"Na, wer kommt morgen? 😄"*

Du bekommst kurz danach von der Business-Nummer eine Nachricht:

```
📨 *Max Mustermann*
🔵 Diese Nachricht scheint nicht direkt an dich gerichtet zu sein.
🟡 Hier wird wahrscheinlich keine Antwort erwartet.
```

---

## Kosten im Betrieb

| Posten | Kosten/Monat |
|---|---|
| Meta WhatsApp Cloud API | $0 (Service-Nachrichten kostenlos) |
| Claude Haiku (~100 Nachrichten/Tag) | ~$1 |
| Hetzner CX11 VPS | ~€4 |
| **Gesamt** | **~€5** |

---

## Wichtige Hinweise

- **Datenschutz:** Alle Nachrichten gehen durch Anthropics API. Für sensible Kontexte beachten.
- **Business-Nummer:** Die Nummer kann nicht gleichzeitig in der normalen WhatsApp-App aktiv sein – sie ist dann exklusiv für die Business API.
- **Redis-Kontext** wird nach 24 Stunden Inaktivität pro Chat automatisch gelöscht.
- **Regeländerungen** in `rules.yaml` erfordern einen Server-Neustart:
  ```bash
  docker compose restart app
  ```
