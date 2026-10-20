# ADR-003: OAuth local readonly Google Calendar (Bifrost)
Fecha: 2026-09-25. Estado: aceptado.

## Contexto
Se necesita conectar Mimir Core a Google Calendar sin exponer secretos ni dar acceso directo al LLM. Google One no implica acceso API; se requiere proyecto Cloud + OAuth client.

## Decision
- Script local `scripts/google_oauth_calendar.py` implementa flujo OAuth `authorization_code` con `redirect_uri=urn:ietf:wg:oauth:2.0:oob` (escritorio).
- Scope limitado a `calendar.readonly` (solo lectura).
- Token guardado solo en `.secrets/calendar_token.json` (ignorado por git via `.gitignore`).
- `GoogleCalendarAdapter` carga token con `google.oauth2.credentials.Credentials` y llama `calendar.events().list`.
- `create_event` bloqueado (NotImplementedError): escritura requiere confirmacion explícita del usuario (HIGH).
- Fallback a `MockCalendarService` si no hay token, para que el Core arranque sin Google.

## Consecuencias
- Pro: Core desacoplado; se puede probar sin credenciales; producción usa adapter real sin reescribir cerebro.
- Contra: app no verificada muestra aviso en consentimiento (modo test, usuario único). Para quitarlo se requiere verificacion de Google (mas adelante).
- Seguridad: token nunca viaja a git, nunca al modelo, nunca en logs.

## Requisitos para activar
1. Proyecto Google Cloud propio.
2. Google Calendar API habilitada.
3. Pantalla consentimiento: externo, usuario de prueba = tu Gmail, scope calendar.readonly.
4. Credenciales OAuth Escritorio en `.env` (GOOGLE_CLOUD_PROJECT, GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET).
5. Ejecutar `py scripts/google_oauth_calendar.py` y autorizar en navegador.
