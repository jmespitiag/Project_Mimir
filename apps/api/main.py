import logging
import pathlib
import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from core.config.settings import Settings
from core.context.manager import Conversation, ContextManager
from core.memory.base import InMemoryStore, MemoryItem, MemoryCategory
from core.tools.registry import ToolRegistry
from core.tools.mocks import MockGmailSearch, MockSendEmail
from core.tools.domain_tools import (
    CalendarCreateEvent, CalendarGetEvents, CalendarUpdateEvent, CalendarDeleteEvent,
    TasksAdd, TasksList,
    FinanceRegisterExpense, FinanceRegisterIncome, FinanceGetSummary, FinanceGetExpenses,
    FinanceGetIncomes, FinanceDeleteExpense, FinanceDeleteIncome, FinanceGetCategories,
    FinanceImportExcel, FinanceExportCSV,
)
from core.tools.executor import ToolExecutor
from core.policy.base import HeimdallBasicPolicy
from core.llm.mock_provider import MockProvider
from core.llm.gemini_provider import GeminiProvider
from core.orchestration.orchestrator import MimirOrchestrator
from core.events.bus import EventBus
from core.messaging.mock import MockMessagingProvider
from core.messaging.telegram import TelegramProvider
from core.messaging.base import IncomingMessage, OutgoingMessage
try:
    from infrastructure.google.calendar_adapter import GoogleCalendarAdapter
except Exception:  # noqa
    GoogleCalendarAdapter = None
from modules.productivity.calendar.service import MockCalendarService
from modules.productivity.tasks.service import MockTaskService
from modules.finance.service import FinanceService
from infrastructure.google.oauth import NeedsGoogleAuth
settings = Settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
log = logging.getLogger('mimir')
registry = ToolRegistry()
for t in (MockGmailSearch(), MockSendEmail()):
    registry.register(t)
cal_svc = None
try:
    cal_svc = GoogleCalendarAdapter()
except NeedsGoogleAuth:
    cal_svc = MockCalendarService()
    log.info('Calendar usando MOCK (no hay token OAuth de Google)')
except Exception as e:
    cal_svc = MockCalendarService()
    log.warning('Calendar fallback a MOCK: ' + str(e))
task_svc = MockTaskService()
fin_svc = FinanceService(settings.database_url)
bus = EventBus()
for t in (
    CalendarGetEvents(cal_svc), CalendarCreateEvent(cal_svc), CalendarUpdateEvent(cal_svc), CalendarDeleteEvent(cal_svc),
    TasksAdd(task_svc), TasksList(task_svc),
    FinanceRegisterExpense(fin_svc), FinanceRegisterIncome(fin_svc), FinanceGetSummary(fin_svc),
    FinanceGetExpenses(fin_svc), FinanceGetIncomes(fin_svc), FinanceDeleteExpense(fin_svc),
    FinanceDeleteIncome(fin_svc), FinanceGetCategories(fin_svc), FinanceImportExcel(fin_svc), FinanceExportCSV(fin_svc),
):
    registry.register(t)
policy = HeimdallBasicPolicy(owner_id=settings.owner_id)
executor = ToolExecutor(registry, policy)
memory = InMemoryStore()
memory.save(MemoryItem(category=MemoryCategory.PROFILE, text='Propietario Roman ecosistema Google'))
ctx = ContextManager(max_chars=settings.context_max_chars)
def _llm():
    return GeminiProvider(model=settings.gemini_model, api_key=settings.google_api_key) if settings.llm_provider == 'gemini' else MockProvider()
orch = MimirOrchestrator(_llm(), registry, executor, memory, ctx, max_steps=settings.max_tool_steps)
msg_provider = MockMessagingProvider()
tp = TelegramProvider(token=settings.telegram_bot_token)
if tp.is_configured():
    msg_provider = tp
    log.info('Telegram provider real activado')
else:
    log.info('Telegram no configurado (falta TELEGRAM_BOT_TOKEN). Usando mock.')
sessions: dict[str, Conversation] = {}
def get_conv(sid: str) -> Conversation:
    if sid not in sessions:
        sessions[sid] = Conversation()
    return sessions[sid]
app = FastAPI(title='Mimir Core', version='0.5.0')
class ChatIn(BaseModel):
    message: str
    session_id: str = 'default'
class ExpenseIn(BaseModel):
    amount: float
    category: str = 'general'
    note: str = ''
    date: str | None = None
class IncomeIn(BaseModel):
    amount: float
    category: str = 'general'
    note: str = ''
    date: str | None = None
class TaskIn(BaseModel):
    title: str
    due: str = ''
class WebhookIn(BaseModel):
    update_id: int = 0
    message: dict = {}
class ImportExcelIn(BaseModel):
    file_path: str
    type: str = 'expense'
def is_google_calendar() -> bool:
    return GoogleCalendarAdapter is not None and isinstance(cal_svc, GoogleCalendarAdapter)
@app.get('/health')
def health():
    return {'status': 'ok', 'core': 'mimir-0.5.0', 'tools': registry.names(), 'provider': _llm().name, 'db': settings.database_url.split('://')[0], 'calendar': 'google' if is_google_calendar() else 'mock', 'messaging': msg_provider.name, 'finance': 'draupnir'}
@app.get('/tools')
def tools():
    return {'tools': registry.definitions_for_llm()}
@app.get('/audit')
def audit():
    return {'audit': executor.audit_log[-20:]}
@app.get('/google/status')
def google_status():
    token_path = pathlib.Path('.secrets/calendar_token.json')
    return {
        'bifrost': 'google_calendar',
        'token_present': bool(token_path.exists()),
        'readwrite': bool(token_path.exists()),
        'note': 'OAuth conectado. Lectura y escritura de calendario con confirmacion. No Gmail.',
    }
@app.get('/calendar/status')
def calendar_status():
    token_path = pathlib.Path('.secrets/calendar_token.json')
    if not token_path.exists():
        return {'configured': False, 'note': 'No hay token. Ejecuta scripts/google_oauth_calendar.py'}
    try:
        import json
        data = json.loads(token_path.read_text(encoding='utf-8'))
        scopes = data.get('scope', '')
        return {
            'configured': True,
            'scopes': scopes,
            'has_write': 'calendar.events' in scopes,
            'note': 'Si no tiene calendar.events, re-ejecuta scripts/google_oauth_calendar.py y autoriza ambos scopes.',
        }
    except Exception as e:
        return {'configured': False, 'error': str(e)}
@app.post('/chat')
def chat(inp: ChatIn):
    log.info('chat sid=%s len=%d', inp.session_id, len(inp.message))
    conv = get_conv(inp.session_id)
    result = orch.chat(conv, inp.message, session_id=inp.session_id)
    audit_tail = executor.audit_log[-3:]
    if 'confirmation' in result:
        return {'reply': result['reply'], 'confirmation': result['confirmation'], 'audit': audit_tail}
    return {'reply': result['reply'], 'audit': audit_tail}
@app.post('/confirm/{confirmation_id}')
def confirm(confirmation_id: str):
    result = executor.approve_confirmation(confirmation_id)
    return {'ok': result.ok, 'data': result.data, 'error': result.error}
@app.post('/telegram/webhook')
def telegram_webhook(inp: WebhookIn):
    try:
        incoming = msg_provider.receive(inp.model_dump())
    except Exception as e:
        return {'status': 'error', 'error': 'payload invalido: ' + str(e)}
    conv = get_conv(incoming.from_number)
    result = orch.chat(conv, incoming.text, session_id=incoming.from_number)
    audit_tail = executor.audit_log[-3:]
    out_text = result.get('reply', 'Sin respuesta')
    if 'confirmation' in result:
        cid = result['confirmation']['id']
        out_text += '\n\nEsta accion requiere confirmacion. Responde con: confirmar ' + cid
    sent = False
    if msg_provider.name == 'telegram':
        try:
            sent = msg_provider.send(OutgoingMessage(to_number=incoming.from_number, text=out_text))
        except Exception as e:
            log.warning('No se pudo enviar por Telegram: ' + str(e))
    return {
        'status': 'ok',
        'from': incoming.from_number,
        'message_id': incoming.message_id,
        'reply': out_text,
        'sent_via_telegram': sent,
        'confirmation': result.get('confirmation'),
        'audit': audit_tail,
    }
@app.get('/telegram/status')
def telegram_status():
    return {
        'provider': msg_provider.name,
        'configured': bool(msg_provider.name == 'telegram' and getattr(msg_provider, 'is_configured', lambda: False)()),
        'note': 'Telegram mock activo. Para usar Telegram real, configura TELEGRAM_BOT_TOKEN y pon el webhook en /telegram/set-webhook.',
    }
@app.post('/telegram/set-webhook')
def set_telegram_webhook(url: str):
    if msg_provider.name != 'telegram':
        return {'ok': False, 'error': 'Telegram no configurado'}
    result = msg_provider.set_webhook(url)
    return {'ok': result, 'url': url}
# ── Draupnir: Finanzas ────────────────────────────────────────────────
@app.post('/finance/expenses')
def add_expense(inp: ExpenseIn):
    d = fin_svc.add_expense(inp.amount, inp.category, inp.note, inp.date)
    bus.publish('finance.expense_added', d)
    return d
@app.post('/finance/incomes')
def add_income(inp: IncomeIn):
    d = fin_svc.add_income(inp.amount, inp.category, inp.note, inp.date)
    bus.publish('finance.income_added', d)
    return d
@app.get('/finance/summary')
def finance_summary():
    return fin_svc.summary()
@app.get('/finance/expenses')
def finance_expenses(limit: int = 50, category: str | None = None, start: str | None = None, end: str | None = None):
    return fin_svc.list_expenses(limit=limit, category=category, start=start, end=end)
@app.get('/finance/incomes')
def finance_incomes(limit: int = 50, category: str | None = None, start: str | None = None, end: str | None = None):
    return fin_svc.list_incomes(limit=limit, category=category, start=start, end=end)
@app.get('/finance/categories')
def finance_categories(type: str | None = None):
    return fin_svc.list_categories(type_filter=type)
@app.delete('/finance/expenses/{expense_id}')
def finance_delete_expense(expense_id: int):
    return fin_svc.delete_expense(expense_id)
@app.delete('/finance/incomes/{income_id}')
def finance_delete_income(income_id: int):
    return fin_svc.delete_income(income_id)
@app.get('/finance/export/csv')
def finance_export_csv(start: str | None = None, end: str | None = None):
    return {
        'expenses': fin_svc.export_expenses_csv(start, end),
        'incomes': fin_svc.export_incomes_csv(start, end),
        'summary': fin_svc.export_summary_csv(start, end),
    }
@app.post('/finance/import/excel')
def finance_import_excel(inp: ImportExcelIn):
    return fin_svc.import_expenses_from_excel(inp.file_path) if inp.type == 'expense' else fin_svc.import_incomes_from_excel(inp.file_path)
# ── Tareas ──────────────────────────────────────────────────────────────
@app.post('/tasks')
def tasks_add(inp: TaskIn):
    return task_svc.add(inp.title, inp.due)
@app.get('/tasks')
def tasks_list():
    return {'tasks': task_svc.list()}
