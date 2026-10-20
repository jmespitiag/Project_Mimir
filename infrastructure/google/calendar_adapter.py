from __future__ import annotations
import json
import pathlib
from modules.productivity.calendar.service import CalendarService
from infrastructure.google.oauth import NeedsGoogleAuth

TOKEN_PATH = pathlib.Path('.secrets') / 'calendar_token.json'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class GoogleCalendarAdapter(CalendarService):
    """Adapter Bifrost -> Google Calendar API (readonly).
    Lee token OAuth guardado solo en .secrets/calendar_token.json (local, no git).
    Sin token -> NeedGoogleAuth (fail closed). Nunca escribe en Calendar.
    """

    def __init__(self) -> None:
        self._svc = None
        if not TOKEN_PATH.exists():
            raise NeedsGoogleAuth('No hay token OAuth de Calendar. Ejecuta scripts/google_oauth_calendar.py.')
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError as e:
            raise NeedsGoogleAuth('Faltan dependencias Google: ' + str(e))
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
            self._svc = build('calendar', 'v3', credentials=creds)
        except Exception as e:
            raise NeedsGoogleAuth('No se pudo cargar credenciales de Calendar: ' + str(e))

    def list_events(self, day: str = '') -> list[dict]:
        if self._svc is None:
            raise NeedsGoogleAuth('Calendar no inicializado.')
        evs = self._svc.events().list(
            calendarId='primary',
            maxResults=10,
            singleEvents=True,
            orderBy='startTime',
        ).execute()
        items = evs.get('items', [])
        return [
            {
                'title': e.get('summary', '(sin titulo)'),
                'start': (e.get('start') or {}).get('dateTime') or (e.get('start') or {}).get('date'),
                'end': (e.get('end') or {}).get('dateTime') or (e.get('end') or {}).get('date'),
            }
            for e in items
        ]

    def create_event(self, title: str, start: str) -> dict:
        # Escritura bloqueada deliberadamente en fase readonly. Requiere tu OK explícito antes de activar.
        raise NotImplementedError('Crear eventos esta bloqueado por politica de confirmacion (HIGH).')
