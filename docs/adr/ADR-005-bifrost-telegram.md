# ADR-005: Bifrost (Telegram) como canal de mensajería
Fecha: 2026-09-25. Estado: aceptado.

## Contexto
Se necesita un canal para que el usuario hable con Mimir sin exponer su número de teléfono. Telegram se elige sobre WhatsApp porque no requiere número de teléfono ni verificación de negocio.

## Decisión
- `BifrostTelegramProvider` en `core/messaging/telegram.py` se conecta a Telegram Bot API usando solo `TELEGRAM_BOT_TOKEN`.
- Falla cerrado si no hay token configurado.
- Endpoint `/bifrost/webhook` recibe updates de Telegram, los procesa en el orchestrator y devuelve la respuesta.
- Endpoint `/bifrost/status` muestra si el proveedor está configurado.
- `MockMessagingProvider` sigue activo por defecto para pruebas sin credenciales.
- Las credenciales nunca se hardcodean; se leen de variables de entorno.
- El usuario obtiene el token hablando con @BotFather en Telegram.

## Consecuencias
- Pro: No se expone el número de teléfono del usuario. Configuración rápida (minutos, no semanas). No hay revisión de Meta.
- Contra: Telegram Bot API tiene límites de tasa y requiere que el usuario inicie la conversación con el bot.