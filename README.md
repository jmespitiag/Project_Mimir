# Mimir Core 0.1.0 � cerebro

Fase Core: `Mimir Core -> abstracciones -> adapters -> Google` (no acoplado a Google).

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

## Estructura
- `core/orchestration/`: MimirOrchestrator (piensa, pide herramienta, responde)
- `core/tools/`: Tool + RiskLevel + Registry + Executor + mocks
- `core/policy/`: HeimdallBasicPolicy (LOW/MEDIUM auto, HIGH/CRITICAL confirmacion)
- `core/memory/`: Muninn InMemory (retrieve relevante, nunca todo)
- `core/context/`: ContextManager (cola + presupuesto)
- `core/llm/`: MockProvider hoy, GeminiProvider adapter (necesita GOOGLE_API_KEY)
- `core/security/`: UNTRUSTED DATA + detector secretos

## Seguridad
LLM nunca toca infra. Secrets fuera del modelo. Datos externos = datos.
No se necesita ninguna credencial Google en esta fase.
