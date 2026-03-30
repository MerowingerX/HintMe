import os
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
        sensitivity = rules.config.get("rules", {}).get("sarcasm", {}).get("sensitivity", "medium")
        active.append(f"sarcasm: Enthält sie Sarkasmus? (Sensitivität: {sensitivity})")

    custom = rules.get_custom_rules()
    for rule in custom:
        if rule.get("enabled"):
            active.append(f"{rule['name']}: {rule['condition']}")

    checks = "\n".join(f"- {a}" for a in active)
    history_text = "\n".join(f"[{h['role']}]: {h['text']}" for h in history[-5:])
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
    body    = "\n".join(hints)
    full    = f"{header}\n{body}"
    return full[:max_len] if len(full) > max_len else full
