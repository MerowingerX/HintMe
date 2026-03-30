# Alternatives KI-Modell einrichten

Statt Claude Haiku kann jedes Modell mit einer OpenAI-kompatiblen API verwendet werden.
Diese Anleitung zeigt das Setup am Beispiel **Llama 3.3 via Groq** – kostenlos und schnell.

## Anbieter im Vergleich

| Anbieter | Modell | Kosten | Besonderheit |
|---|---|---|---|
| [Groq](https://console.groq.com) | llama-3.3-70b-versatile | Kostenlos (Rate Limits) | Sehr schnell (LPU-Hardware) |
| [Together AI](https://api.together.xyz) | Meta-Llama-3.3-70B-Instruct | ~$0.18/1M Tokens | Große Modellauswahl |
| [Meta Llama API](https://llama.developer.meta.com) | llama3.3-70b | Kostenlos (Beta) | Direkt von Meta |
| [OpenRouter](https://openrouter.ai) | beliebig | Variabel | Viele Modelle, eine API |

Alle nutzen die **OpenAI-kompatible API** – der Code ist für alle identisch, nur `base_url` und Modellname ändern sich.

---

## Einrichtung (Beispiel: Groq)

### 1. API Key holen

1. Account erstellen auf [console.groq.com](https://console.groq.com)
2. API Keys → Create API Key
3. Key kopieren

### 2. `.env` anpassen

```bash
# Claude-Zeilen ersetzen:
# ANTHROPIC_API_KEY=sk-ant-...
# CLAUDE_MODEL=claude-haiku-4-5

# Neu:
GROQ_API_KEY=gsk_...
CLAUDE_MODEL=llama-3.3-70b-versatile
```

### 3. `requirements.txt` anpassen

```diff
- anthropic>=0.25.0
+ openai>=1.30.0
```

### 4. `backend/analyzer.py` anpassen

```diff
- from anthropic import AsyncAnthropic
- client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
+ from openai import AsyncOpenAI
+ client = AsyncOpenAI(
+     api_key=os.getenv("GROQ_API_KEY"),
+     base_url="https://api.groq.com/openai/v1",
+ )
```

```diff
- response = await client.messages.create(
-     model=model,
-     max_tokens=300,
-     system=f"Antworte immer auf {lang}, Stil: {style}. Nur valides JSON, kein Markdown.",
-     messages=[{"role": "user", "content": prompt}]
- )
- result = json.loads(response.content[0].text)
+ response = await client.chat.completions.create(
+     model=model,
+     max_tokens=300,
+     messages=[
+         {"role": "system", "content": f"Antworte immer auf {lang}, Stil: {style}. Nur valides JSON, kein Markdown."},
+         {"role": "user", "content": prompt},
+     ],
+ )
+ result = json.loads(response.choices[0].message.content)
```

---

## Andere Anbieter

Nur `base_url` und Key-Variable tauschen – der Rest bleibt gleich.

**Together AI:**
```python
client = AsyncOpenAI(
    api_key=os.getenv("TOGETHER_API_KEY"),
    base_url="https://api.together.xyz/v1",
)
# Modell: "meta-llama/Llama-3.3-70B-Instruct-Turbo"
```

**Meta Llama API:**
```python
client = AsyncOpenAI(
    api_key=os.getenv("LLAMA_API_KEY"),
    base_url="https://api.llama.com/compat/v1",
)
# Modell: "llama3.3-70b"
```

**OpenRouter:**
```python
client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)
# Modell: z.B. "meta-llama/llama-3.3-70b-instruct"
```

---

## Neustart

```bash
docker compose build
docker compose up -d
```

---

## Hinweise zur Modellwahl

- **JSON-Zuverlässigkeit** ist entscheidend: Das Modell muss strukturiertes JSON ohne Markdown-Wrapper ausgeben. Llama 3.3 70B macht das zuverlässig; kleinere Modelle (z.B. 8B) neigen zu Abweichungen.
- **Latenz**: Groq ist durch LPU-Hardware deutlich schneller als GPU-basierte Anbieter – wichtig, da jede eingehende Nachricht synchron analysiert wird.
- **Rate Limits bei Groq**: Im kostenlosen Tier ca. 30 Anfragen/Minute – für persönlichen Gebrauch ausreichend.
