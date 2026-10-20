from __future__ import annotations
from dataclasses import dataclass
import uuid
@dataclass
class CalEvent:
    title: str
    start: str
    end: str = ''
    event_id: str = ''
class CalendarService:
    def list_events(self, day: str = '') -> list[dict]:
        raise NotImplementedError
    def create_event(self, title: str, start: str) -> dict:
        raise NotImplementedError
    def update_event(self, event_id: str, title: str, start: str) -> dict:
        raise NotImplementedError
    def delete_event(self, event_id: str) -> dict:
        raise NotImplementedError
class MockCalendarService(CalendarService):
    def __init__(self) -> None:
        self._evs = [
            {'event_id': 'mock-1', 'title': 'Reunion de prueba', 'start': '2026-09-26T10:00:00', 'end': ''},
        ]
    def list_events(self, day: str = '') -> list[dict]:
        return list(self._evs)
    def create_event(self, title: str, start: str) -> dict:
        ev = {'event_id': 'mock-' + str(uuid.uuid4())[:8], 'title': title, 'start': start, 'end': ''}
        self._evs.append(ev)
        return ev
    def update_event(self, event_id: str, title: str, start: str) -> dict:
        for ev in self._evs:
            if ev['event_id'] == event_id:
                ev['title'] = title
                ev['start'] = start
                return ev
        raise KeyError('event not found')
    def delete_event(self, event_id: str) -> dict:
        for i, ev in enumerate(self._evs):
            if ev['event_id'] == event_id:
                return self._evs.pop(i)
        raise KeyError('event not found')
