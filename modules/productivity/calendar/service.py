from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable
import uuid
import heapq

class ReminderTiming(Enum):
    THREE_DAYS_BEFORE = "3_days_before"
    ONE_DAY_BEFORE = "1_day_before"
    ON_THE_DAY = "on_the_day"

@dataclass
class Reminder:
    reminder_id: str
    event_id: str
    event_title: str
    event_start: datetime
    timing: ReminderTiming
    remind_at: datetime
    sent: bool = False

@dataclass
class CalEvent:
    title: str
    start: str
    end: str = ''
    event_id: str = ''
    reminders: list[ReminderTiming] = field(default_factory=lambda: [ReminderTiming.ONE_DAY_BEFORE, ReminderTiming.THREE_DAYS_BEFORE])

class CalendarService:
    def list_events(self, day: str = '') -> list[dict]:
        raise NotImplementedError
    def create_event(self, title: str, start: str, end: str = '', reminders: list[str] | None = None) -> dict:
        raise NotImplementedError
    def update_event(self, event_id: str, title: str, start: str, end: str = '') -> dict:
        raise NotImplementedError
    def delete_event(self, event_id: str) -> dict:
        raise NotImplementedError
    def get_upcoming_events(self, days: int = 7) -> list[dict]:
        raise NotImplementedError

class ReminderScheduler:
    """Programador de recordatorios para eventos de calendario."""
    
    def __init__(self, send_callback: Callable[[str, str], None]):
        self._reminders: list[Reminder] = []
        self._event_callbacks: dict[str, list[ReminderTiming]] = {}
        self._send_callback = send_callback
    
    def schedule_reminders(self, event_id: str, event_title: str, event_start: datetime, timings: list[ReminderTiming]) -> None:
        """Programa recordatorios para un evento."""
        for timing in timings:
            if timing == ReminderTiming.THREE_DAYS_BEFORE:
                remind_at = event_start - timedelta(days=3)
            elif timing == ReminderTiming.ONE_DAY_BEFORE:
                remind_at = event_start - timedelta(days=1)
            elif timing == ReminderTiming.ON_THE_DAY:
                remind_at = event_start.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                continue
            
            if remind_at > datetime.now():
                reminder = Reminder(
                    reminder_id=str(uuid.uuid4())[:8],
                    event_id=event_id,
                    event_title=event_title,
                    event_start=event_start,
                    timing=timing,
                    remind_at=remind_at,
                    sent=False
                )
                self._reminders.append(reminder)
                # Mantener ordenados por tiempo
                self._reminders.sort(key=lambda r: r.remind_at)
    
    def cancel_reminders(self, event_id: str) -> int:
        """Cancela todos los recordatorios de un evento."""
        before = len(self._reminders)
        self._reminders = [r for r in self._reminders if r.event_id != event_id]
        return before - len(self._reminders)
    
    def process_due_reminders(self) -> list[Reminder]:
        """Procesa recordatorios vencidos y los envía."""
        now = datetime.now()
        due = [r for r in self._reminders if not r.sent and r.remind_at <= now]
        sent = []
        for reminder in due:
            self._send_reminder(reminder)
            reminder.sent = True
            sent.append(reminder)
        return sent
    
    def _send_reminder(self, reminder: Reminder) -> None:
        timing_text = {
            ReminderTiming.THREE_DAYS_BEFORE: "en 3 días",
            ReminderTiming.ONE_DAY_BEFORE: "mañana",
            ReminderTiming.ON_THE_DAY: "hoy"
        }
        text = (
            f"🔔 Recordatorio: «{reminder.event_title}» {timing_text.get(reminder.timing, '')}\n"
            f"📅 {reminder.event_start.strftime('%A %d de %B a las %H:%M')}"
        )
        self._send_callback(reminder.event_id, text)

    def get_pending_reminders(self, event_id: str | None = None) -> list[Reminder]:
        if event_id:
            return [r for r in self._reminders if r.event_id == event_id and not r.sent]
        return [r for r in self._reminders if not r.sent]

class MockCalendarService(CalendarService):
    def __init__(self) -> None:
        self._evs: list[CalEvent] = [
            CalEvent(
                event_id='mock-1',
                title='Reunion de prueba',
                start=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT10:00:00'),
                reminders=[ReminderTiming.ONE_DAY_BEFORE, ReminderTiming.THREE_DAYS_BEFORE]
            ),
        ]
        self._scheduler = ReminderScheduler(self._send_reminder_mock)
        self._reminder_log: list[str] = []
    
    def _send_reminder_mock(self, event_id: str, text: str) -> None:
        self._reminder_log.append(f"[{datetime.now()}] Evento {event_id}: {text}")
    
    def list_events(self, day: str = '') -> list[dict]:
        result = []
        for ev in self._evs:
            result.append({
                'event_id': ev.event_id,
                'title': ev.title,
                'start': ev.start,
                'end': ev.end,
                'reminders': [r.value for r in ev.reminders]
            })
        return result
    
    def create_event(self, title: str, start: str, end: str = '', reminders: list[str] | None = None) -> dict:
        reminder_timings = []
        if reminders:
            for r in reminders:
                try:
                    reminder_timings.append(ReminderTiming(r))
                except ValueError:
                    pass
        if not reminder_timings:
            reminder_timings = [ReminderTiming.ONE_DAY_BEFORE, ReminderTiming.THREE_DAYS_BEFORE]
        
        ev = CalEvent(
            event_id='mock-' + str(uuid.uuid4())[:8],
            title=title,
            start=start,
            end=end,
            reminders=reminder_timings
        )
        self._evs.append(ev)
        
        # Programar recordatorios
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            self._scheduler.schedule_reminders(ev.event_id, ev.title, start_dt, ev.reminders)
        except ValueError:
            pass
        
        return {
            'event_id': ev.event_id,
            'title': ev.title,
            'start': ev.start,
            'end': ev.end,
            'reminders': [r.value for r in ev.reminders]
        }
    
    def update_event(self, event_id: str, title: str, start: str, end: str = '') -> dict:
        for ev in self._evs:
            if ev.event_id == event_id:
                # Cancelar recordatorios antiguos
                self._scheduler.cancel_reminders(event_id)
                ev.title = title
                ev.start = start
                ev.end = end
                # Reprogramar recordatorios
                try:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    self._scheduler.schedule_reminders(ev.event_id, ev.title, start_dt, ev.reminders)
                except ValueError:
                    pass
                return {
                    'event_id': ev.event_id,
                    'title': ev.title,
                    'start': ev.start,
                    'end': ev.end,
                    'reminders': [r.value for r in ev.reminders]
                }
        raise KeyError('event not found')
    
    def delete_event(self, event_id: str) -> dict:
        self._scheduler.cancel_reminders(event_id)
        for i, ev in enumerate(self._evs):
            if ev.event_id == event_id:
                return self._evs.pop(i)
        raise KeyError('event not found')
    
    def get_upcoming_events(self, days: int = 7) -> list[dict]:
        now = datetime.now()
        limit = now + timedelta(days=days)
        result = []
        for ev in self._evs:
            try:
                start_dt = datetime.fromisoformat(ev.start.replace('Z', '+00:00'))
                if now <= start_dt <= limit:
                    result.append({
                        'event_id': ev.event_id,
                        'title': ev.title,
                        'start': ev.start,
                        'end': ev.end,
                        'reminders': [r.value for r in ev.reminders]
                    })
            except ValueError:
                pass
        return result
    
    def get_reminder_log(self) -> list[str]:
        return self._reminder_log
    
    def process_reminders(self) -> list[str]:
        """Procesa recordatorios pendientes (para testing/manual)."""
        sent = self._scheduler.process_due_reminders()
        return [f"Recordatorio enviado para {r.event_title}" for r in sent]