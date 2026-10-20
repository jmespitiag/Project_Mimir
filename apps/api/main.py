import logging
import pathlib
from fastapi import FastAPI
from pydantic import BaseModel
from core.config.settings import Settings
from core.context.manager import Conversation, ContextManager
from core.memory.base import InMemoryStore, MemoryItem, MemoryCategory
from core.tools.registry import ToolRegistry
from core.tools.mocks import MockGmailSearch, MockFinanceRegister, MockSendEmail
from core.tools.domain_tools import CalendarCreateEvent, CalendarGetEvents, CalendarUpdateEvent, CalendarDeleteEvent, TasksAdd, TasksList, FinanceTotal
from core.tools.executor import ToolExecutor
from core.policy.base import HeimdallBasicPolicy
from core.llm.mock_provider import MockProvider
from core.llm.gemini_provider import GeminiProvider
from core.orchestration.orchestrator import MimirOrchestrator
from core.events.bus import EventBus
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
for t in (MockGmailSearch(), MockFinanceRegister(), MockSendEmail()):
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
for t in (CalendarGetEvents(cal_svc), CalendarCreateEvent(cal_svc), CalendarUpdateEvent(cal_svc), CalendarDeleteEvent(cal_svc), TasksAdd(task_svc), TasksList(task_svc), FinanceTotal(fin_svc)):
    registry.register(t)
policy = HeimdallBasicPolicy(owner_id=settings.owner_id)
executor = ToolExecutor(registry, policy)
memory = InMemoryStore()
memory.save(MemoryItem(category=MemoryCategory.PROFILE, text='Propietario Roman ecosistema Google'))
ctx = ContextManager(max_chars=settings.context_max_chars)
def _llm():
    return GeminiProvider(model=settings.gemini_model) if settings.llm_provider == 'gemini' else MockProvider()
orch = MimirOrchestrator(_llm(), registry, executor, memory, ctx, max_steps=settings.max_tool_steps)
sessions: dict[str, Conversation] = {}
def get_conv(sid: str) -> Conversation:
    if sid not in sessions:
        sessions[sid] = Conversation()
    return sessions[sid]
app = FastAPI(title='Mimir Core', version='0.4.0')
class ChatIn(BaseModel):
    message: str
    session_id: str = 'default'
class ExpenseIn(BaseModel):
    amount: float
    category: str = 'general'
    note: str = ''
class TaskIn(BaseModel):
    title: str
    due: str = ''
def is_google_calendar() -> bool:
    return GoogleCalendarAdapter is not None and isinstance(cal_svc, GoogleCalendarAdapter)
@app.get('/health')
def health():
    return {'status': 'ok', 'core': 'mimir-0.4.0', 'tools': registry.names(), 'provider': _llm().name, 'db': settings.database_url.split('://')[0], 'calendar': 'google' if is_google_calendar() else 'mock'}
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
    result = orch.chat(conv, inp.message)
    audit_tail = executor.audit_log[-3:]
    if 'confirmation' in result:
        return {'reply': result['reply'], 'confirmation': result['confirmation'], 'audit': audit_tail}
    return {'reply': result['reply'], 'audit': audit_tail}
@app.post('/confirm/{confirmation_id}')
def confirm(confirmation_id: str):
    result = executor.approve_confirmation(confirmation_id)
    return {'ok': result.ok, 'data': result.data, 'error': result.error}
@app.post('/finance/expenses')
def add_expense(inp: ExpenseIn):
    d = fin_svc.add_expense(inp.amount, inp.category, inp.note)
    bus.publish('finance.expense_added', d)
    return d
@app.get('/finance/summary')
def finance_summary():
    return {'total': fin_svc.total(), 'by_category': fin_svc.totals_by_category()}
@app.get('/finance/export')
def finance_export():
    return {'csv': fin_svc.export_csv()}
@app.post('/tasks')
def tasks_add(inp: TaskIn):
    return task_svc.add(inp.title, inp.due)
@app.get('/tasks')
def tasks_list():
    return {'tasks': task_svc.list()}
