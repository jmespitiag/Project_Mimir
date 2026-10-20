# ADR-004: WhatsApp Business API como canal de mensajeria
Fecha: 2026-09-25. Estado: aceptado.

## Contexto
Se necesita un canal para que el usuario hable con Mimir. WhatsApp es la opcion elegida.

## Decision
- `MessagingProvider` abstrae el proveedor de mensajeria (como `LLMProvider` abstrae al LLM).
- `MockMessagingProvider` activo por defecto: permite probar sin credenciales.
- `WhatsAppProvider` adapter real a WhatsApp Business API (Meta): requiere `WHATSAPP_ACCESS_TOKEN` y `WHATSAPP_PHONE_NUMBER_ID`. Falla cerrado si no estan configurados.
- Endpoint `/whatsapp/webhook` recibe mensajes entrantes y los envia al orchestrator.
- Endpoint `/whatsapp/send` envia mensajes salientes (confirmaciones, recordatorios).
- Las credenciales nunca se hardcodean; se leen de variables de entorno.
- No se asume acceso a WhatsApp sin credenciales reales del usuario.

## Consecuencias
- Pro: Core desacoplado; se puede probar sin WhatsApp real; se activa solo con credenciales del usuario.
- Contra: WhatsApp Business API requiere verificacion de Meta (puede tardar); para pruebas rapidas se usa el mock.
