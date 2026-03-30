# Telefonnummer für die WhatsApp Business API

Die WhatsApp Business API benötigt eine eigene Telefonnummer – getrennt von deiner persönlichen WhatsApp.
Du brauchst **keine physische SIM-Karte**. Die Nummer wird einmalig per SMS oder Anruf verifiziert, danach läuft alles über die API.

## Wie das Zusammenspiel funktioniert

```
Business-Nummer (API)          Deine persönliche Nummer
       │                                  │
       │  empfängt Nachrichten            │  empfängt die Hints
       │  von anderen                     │  (normales WhatsApp)
       └──────────── WhatsApp Business API ┘
```

Dein persönliches WhatsApp bleibt **unverändert**. Die Business-Nummer existiert nur im Hintergrund.

---

## Optionen im Vergleich

| Option | Kosten | Aufwand | Geeignet |
|---|---|---|---|
| **sipgate basic** | Kostenlos | Gering | Beste Wahl |
| Prepaid-SIM (Callya, Aldi Talk …) | ~€10 Startpaket | Mittel | Funktioniert, überdimensioniert |
| Bestehende Festnetznummer | €0 | Gering | Geht (Verifikation per Anruf) |
| Twilio-Nummer | ~$1/Monat | Gering | Geht, laufende Kosten |

---

## Empfehlung: sipgate basic

sipgate gibt jedem kostenlosen Account eine deutsche Festnetznummer. SMS werden im Webinterface angezeigt – das reicht für die einmalige WhatsApp-Verifikation.

### Einrichtung

1. Kostenlosen Account erstellen auf [sipgate.de/basic](https://www.sipgate.de/basic)
2. Die zugewiesene Nummer notieren (Format: `+4921199999xx`)
3. Diese Nummer als `WHATSAPP_PHONE_NUMBER_ID` in der Meta Developer Console registrieren
4. Verifikationscode: In der sipgate-Weboberfläche unter **SMS** abrufen
5. Fertig – die sipgate-Nummer wird danach nicht mehr benötigt

---

## Was du vermeiden solltest

- **Deine persönliche WhatsApp-Nummer** als Business-Nummer eintragen – sie würde aus der normalen WhatsApp-App ausgeloggt.
- Eine Nummer, die bereits auf einem anderen WhatsApp-Account aktiv ist – Meta lehnt die Registrierung ab.
