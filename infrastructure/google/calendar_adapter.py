from __future__ import annotations
import json
import pathlib
from modules.productivity.calendar.service import CalendarService
from infrastructure.google.oauth import NeedsGoogleAuth

TOKEN_PATH = pathlib.Path('.secrets') / 'calendar_token.json'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/calendar.events']


class GoogleCalendarAdapter(CalendarService):
    """Adapter Bifrost -> Google Calendar API.
    Lee y escribe eventos. Escritura requiere confirmacion del usuario (HIGH).
    Token OAuth guardado solo en .secrets/calendar_token.json (local, no git).
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

    def _event_body(self, title: str, start: str) -> dict:
        return {
            'summary': title,
            'start': {'dateTime': start, 'timeZone': 'UTC'},
            'end': {'dateTime': start, 'timeZone': 'UTC'},
        }

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
                'event_id': e.get('id', ''),
                'title': e.get('summary', '(sin titulo)'),
                'start': (e.get('start') or {}).get('dateTime') or (e.get('start') or {}).get('date'),
                'end': (e.get('end') or {}).get('dateTime') or (e.get('end') or {}).get('date'),
            }
            for e in items
        ]

    def create_event(self, title: str, start: str) -> dict:
        if self._svc is None:
            raise NeedsGoogleAuth('Calendar no inicializado.')
        created = self._svc.events().insert(calendarId='primary', body=self._event_body(title, start)).execute()
        return {
            'event_id': created.get('id', ''),
            'title': created.get('summary', title),
            'start': (created.get('start') or {}).get('dateTime') or (created.get('start') or {}).get('date'),
        }

    def update_event(self, event_id: str, title: str, start: str) -> dict:
        if self._svc is None:
            raise NeedsGoogleAuth('Calendar no inicializado.')
        updated = self._svc.events().update(
            calendarId='primary', eventId=event_id, body=self._event_body(title, start),
        ).execute()
        return {
            'event_id': updated.get('id', event_id),
            'title': updated.get('summary', title),
            'start': (updated.get('start') or {}).get('dateTime') or (updated.get('start') or {}).get('date'),
        }

    def delete_event(self, event_id: str) -> dict:
        if self._svc is None:
            raise NeedsGoogleAuth('Calendar no inicializado.')
        self._svc.events().delete(calendarId='primary', eventId=event_id).execute()
        return {'event_id': event_id, 'deleted': True}
