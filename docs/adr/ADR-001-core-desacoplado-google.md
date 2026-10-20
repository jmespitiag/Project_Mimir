# ADR-001: Mimir Core desacoplado de Google (Core -> abstracciones -> adapters -> Google)

Fecha: 2026-09-25
Estado: aceptado

## Contexto
Mimir objetivo Google, pero el Core no debe depender de Google desde el dia 1 (precision del propietario + sec. 10/11 MASTER).

## Decision
- `LLMProvider` abstrae Gemini/Mock/futuros. Core solo habla con la abstraccion.
- `Tool`/`ToolRegistry`/`ToolExecutor` con interfaz estable. Mocks hoy, `GoogleCalendarTool` manana sin reescribir cerebro.
- `MemoryStore`/`ContextManager`/`PolicyInterface` abstraidos. Postgres/Heimdall real despues.
- `GeminiProvider` vive en `core/llm/` como adapter Bifrost, fail-closed sin GOOGLE_API_KEY.
- Sin OAuth/cloud/Telegram en esta fase (sec. 23 NO implementar todavia).

## Consecuencias
- Pro: crecimiento sin rewrite, tests sin credenciales, seguridad por defecto.
- Contra: retrieval ingenuo y MockProvider simple; se mejoraran en Fases 2-6.
