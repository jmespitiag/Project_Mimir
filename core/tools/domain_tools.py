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
# ── Draupnir: Finanzas ──────────────────────────────────────────────────
class FinanceRegisterExpense(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_register_expense', description='Registrar gasto (Draupnir). Requiere confirmacion si es monto elevado.', risk_level=RiskLevel.MEDIUM, input_schema={'required': ['amount', 'category']}, concept='Draupnir', required_permissions=['finance.write'], **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.add_expense(args['amount'], args.get('category', 'general'), args.get('note', ''), args.get('date')))
class FinanceRegisterIncome(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_register_income', description='Registrar ingreso (Draupnir). Requiere confirmacion si es monto elevado.', risk_level=RiskLevel.MEDIUM, input_schema={'required': ['amount', 'category']}, concept='Draupnir', required_permissions=['finance.write'], **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.add_income(args['amount'], args.get('category', 'general'), args.get('note', ''), args.get('date')))
class FinanceGetSummary(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_get_summary', description='Resumen financiero determinista SQL (Draupnir): totales, balance, por categoría.', risk_level=RiskLevel.LOW, input_schema={}, concept='Draupnir', **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.summary(args.get('start'), args.get('end')))
class FinanceGetExpenses(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_get_expenses', description='Listar gastos (Draupnir).', risk_level=RiskLevel.LOW, input_schema={}, concept='Draupnir', **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.list_expenses(limit=args.get('limit', 50), category=args.get('category'), start=args.get('start'), end=args.get('end')))
class FinanceGetIncomes(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_get_incomes', description='Listar ingresos (Draupnir).', risk_level=RiskLevel.LOW, input_schema={}, concept='Draupnir', **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.list_incomes(limit=args.get('limit', 50), category=args.get('category'), start=args.get('start'), end=args.get('end')))
class FinanceDeleteExpense(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_delete_expense', description='Eliminar gasto (Draupnir). Requiere confirmacion.', risk_level=RiskLevel.HIGH, input_schema={'required': ['expense_id']}, concept='Draupnir', required_permissions=['finance.write'], **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.delete_expense(args['expense_id']))
class FinanceDeleteIncome(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_delete_income', description='Eliminar ingreso (Draupnir). Requiere confirmacion.', risk_level=RiskLevel.HIGH, input_schema={'required': ['income_id']}, concept='Draupnir', required_permissions=['finance.write'], **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.delete_income(args['income_id']))
class FinanceGetCategories(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_get_categories', description='Listar categorías financieras (Draupnir).', risk_level=RiskLevel.LOW, input_schema={}, concept='Draupnir', **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data=self._svc.list_categories(args.get('type')))
class FinanceImportExcel(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_import_excel', description='Importar gastos o ingresos desde archivo Excel (Draupnir). Requiere confirmacion.', risk_level=RiskLevel.MEDIUM, input_schema={'required': ['file_path', 'type']}, concept='Draupnir', required_permissions=['finance.write'], **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        t = args.get('type', 'expense')
        if t == 'income':
            return ToolResult(ok=True, data=self._svc.import_incomes_from_excel(args['file_path']))
        return ToolResult(ok=True, data=self._svc.import_expenses_from_excel(args['file_path']))
class FinanceExportCSV(Tool):
    _svc: object = PrivateAttr()
    def __init__(self, svc, **kw) -> None:
        super().__init__(name='finance_export_csv', description='Exportar finanzas a CSV (Draupnir, solo vista).', risk_level=RiskLevel.LOW, input_schema={}, concept='Draupnir', **kw)
        self._svc = svc
    def run(self, args: dict) -> ToolResult:
        return ToolResult(ok=True, data={'expenses': self._svc.export_expenses_csv(args.get('start'), args.get('end')), 'incomes': self._svc.export_incomes_csv(args.get('start'), args.get('end')), 'summary': self._svc.export_summary_csv(args.get('start'), args.get('end'))})
