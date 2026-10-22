# Mimir Core 0.5.0 — cerebro

Fase Core: `Mimir Core -> abstracciones -> adapters -> Google` (no acoplado a Google).

## Requisitos de Python

| Componente | Versión requerida |
|------------|-------------------|
| Core, Telegram, Calendar, Finanzas | Python 3.11 - 3.12 |
| **Gemini API (real)** | **Python 3.11 - 3.12** (no 3.13+) |

> **Importante**: `google-generativeai` solo soporta Python 3.11 y 3.12 actualmente. Python 3.13+ no es compatible con `google-generativeai`. Para usar Gemini real, usa Python 3.11 o 3.12.

## Quickstart sin credenciales
```
pip install fastapi uvicorn pydantic pydantic-settings httpx pytest
pytest -q
uvicorn apps.api.main:app --reload
# GET /health, POST /chat {"message": "que tengo en el calendario?"}
```

## Conectar Google Calendar (readonly, opcional)
Requisitos: proyecto Google Cloud, Calendar API habilitada, credenciales OAuth Escritorio.
```
# 1) Rellena .env (no commitear): GOOGLE_CLOUD_PROJECT, GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET
# 2) Autoriza:
py scripts/google_oauth_calendar.py
# -> abre URL, autoriza SOLO calendar.readonly, pega el codigo
# 3) Prueba lectura real:
py scripts/google_oauth_calendar.py
```
El token queda solo en `.secrets/calendar_token.json` (ignorado por git). Escritura bloqueada por politica hasta tu OK explícito.

## Conectar Telegram Bot
1. Crea bot con `@BotFather` en Telegram
2. Copia el token a `.env`: `TELEGRAM_BOT_TOKEN=...`
3. Con ngrok: `ngrok http 8000` y `curl -X POST "http://localhost:8000/telegram/set-webhook?url=https://TU_URL/telegram/webhook"`
4. Habla con tu bot en Telegram

## Conectar Gemini (opcional)
1. Obtén API key en [Google AI Studio](https://aistudio.google.com/)
2. Agrega a `.env`: `GOOGLE_API_KEY=...` y `LLM_PROVIDER=gemini`
3. Requiere **Python 3.11 o 3.12** (no 3.13+)

## Estructura
- `core/orchestration/`: MimirOrchestrator (piensa, pide herramienta, responde)
- `core/tools/`: Tool + RiskLevel + Registry + Executor + mocks
- `core/policy/`: HeimdallBasicPolicy (LOW/MEDIUM auto, HIGH/CRITICAL confirmacion)
- `core/memory/`: Muninn InMemory (retrieve relevante, nunca todo)
- `core/context/`: ContextManager (cola + presupuesto)
- `core/llm/`: MockProvider hoy, GeminiProvider adapter (necesita GOOGLE_API_KEY)
- `core/security/`: UNTRUSTED DATA + detector secretos
- `modules/finance/`: Draupnir (finanzas deterministas SQL, import/export Excel/CSV)
- `core/messaging/`: TelegramProvider + MockMessagingProvider

## Seguridad
LLM nunca toca infra. Secrets fuera del modelo. Datos externos = datos.
No se necesita ninguna credencial Google en esta fase.