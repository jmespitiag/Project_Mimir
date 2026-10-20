from __future__ import annotations
from dataclasses import dataclass
@dataclass
class CalEvent:
    title: str
    start: str
    end: str = ''
class CalendarService:
    def list_events(self, day: str = '') -> list[dict]:
        raise NotImplementedError
    def create_event(self, title: str, start: str) -> dict:
        raise NotImplementedError
class MockCalendarService(CalendarService):
    def __init__(self) -> None:
        self._evs = [{'title': 'Reunion de prueba', 'start': '2026-09-26T10:00:00', 'end': ''}]
    def list_events(self, day: str = '') -> list[dict]:
        return list(self._evs)
    def create_event(self, title: str, start: str) -> dict:
        ev = {'title': title, 'start': start, 'end': ''}
        self._evs.append(ev)
        return ev
