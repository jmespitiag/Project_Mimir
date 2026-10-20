# ADR-005: Telegram Bot API como canal de mensajeria
Fecha: 2026-09-25. Estado: aceptado.

## Contexto
Se necesita un canal para que el usuario hable con Mimir sin exponer su numero de telefono. Telegram se elige sobre WhatsApp porque no requiere numero de telefono ni verificacion de negocio.

## Decision
- `TelegramProvider` en `core/messaging/telegram.py` se conecta a Telegram Bot API usando solo `TELEGRAM_BOT_TOKEN`.
- Falla cerrado si no hay token configurado.
- Endpoint `/telegram/webhook` recibe updates de Telegram, los procesa en el orchestrator y devuelve la respuesta.
- Endpoint `/telegram/status` muestra si el proveedor esta configurado.
- `MockMessagingProvider` sigue activo por defecto para pruebas sin credenciales.
- Las credenciales nunca se hardcodean; se leen de variables de entorno.
- El usuario obtiene el token hablando con @BotFather en Telegram.

## Consecuencias
- Pro: No se expone el numero de telefono del usuario. Configuracion rapida (minutos, no semanas). No hay revisión de Meta.
- Contra: Telegram Bot API tiene limites de tasa y requiere que el usuario inicie la conversacion con el bot.
