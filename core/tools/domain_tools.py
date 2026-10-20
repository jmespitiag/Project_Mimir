from __future__ import annotations
from pydantic import PrivateAttr
from core.tools.base import Tool, ToolResult, RiskLevel
class CalendarGetEvents(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='calendar_get_events', description='Listar eventos de calendario (Freyja, Google Calendar readonly)', risk_level=RiskLevel.LOW, input_schema={'required': []}, concept='Freyja', **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.list_events(args.get('day', '')))
class CalendarCreateEvent(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='calendar_create_event', description='Crear evento de calendario (Freyja). Requiere confirmacion del usuario.', risk_level=RiskLevel.HIGH, input_schema={'required': ['title', 'start']}, concept='Freyja', required_permissions=['calendar.write'], **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.create_event(args['title'], args['start']))
class CalendarUpdateEvent(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='calendar_update_event', description='Modificar evento de calendario (Freyja). Requiere confirmacion del usuario.', risk_level=RiskLevel.HIGH, input_schema={'required': ['event_id', 'title', 'start']}, concept='Freyja', required_permissions=['calendar.write'], **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.update_event(args['event_id'], args['title'], args['start']))
class CalendarDeleteEvent(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='calendar_delete_event', description='Eliminar evento de calendario (Freyja). Requiere confirmacion del usuario.', risk_level=RiskLevel.HIGH, input_schema={'required': ['event_id']}, concept='Freyja', required_permissions=['calendar.write'], **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.delete_event(args['event_id']))
class TasksAdd(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='tasks_add', description='Agregar tarea (Skadi)', risk_level=RiskLevel.MEDIUM, input_schema={'required': ['title']}, concept='Skadi', required_permissions=['tasks.write'], **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.add(args['title'], args.get('due', '')))
class TasksList(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='tasks_list', description='Listar tareas (Skadi)', risk_level=RiskLevel.LOW, input_schema={}, concept='Skadi', **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.list())
class FinanceTotal(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_totals', description='Totales por categoria determinista SQL (Draupnir)', risk_level=RiskLevel.LOW, input_schema={}, concept='Draupnir', **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data={'total': self._svc.total(), 'by_category': self._svc.totals_by_category()})
