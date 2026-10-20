# ADR-002: Bifrost Google en espera (fail-closed hasta OAuth)
Fecha: 2026-09-25. Estado: aceptado.
Decision: adapters Google existen pero lanzan NeedsGoogleAuth. Nada llama a Google sin OAuth del propietario.
Scopes minimos previstos: calendar.readonly primero, luego calendar.events, gmail.readonly, tasks.
No hay secretos en codigo ni logs. .env.example solo con nombres.
