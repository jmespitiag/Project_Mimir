import logging
import pathlib
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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
@app.post('/chat')
def chat(inp: ChatIn):
    log.info('chat sid len set')
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
@app.get('/', response_class=HTMLResponse)
def chat_ui():
    return HTMLResponse(content='''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mimir - Chat</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; height: 100vh; display: flex; flex-direction: column; }
  header { background: #1e293b; padding: 1rem 2rem; border-bottom: 1px solid #334155; }
  header h1 { font-size: 1.25rem; letter-spacing: 0.05em; }
  #chat { flex: 1; overflow-y: auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
  .msg { max-width: 70%; padding: 0.75rem 1rem; border-radius: 0.75rem; line-height: 1.5; }
  .msg.user { align-self: flex-end; background: #3b82f6; color: #fff; }
  .msg.assistant { align-self: flex-start; background: #334155; color: #e2e8f0; }
  .msg.system { align-self: center; font-size: 0.85rem; color: #94a3b8; padding: 0.4rem 0.8rem; background: #1e293b; }
  .confirm-box { background: #f59e0b; color: #fff; border-left: 4px solid #d97706; }
  .confirm-box button { background: #10b981; color: #fff; border: none; padding: 0.4rem 0.8rem; margin-right: 0.5rem; border-radius: 0.375rem; cursor: pointer; }
  .confirm-box button.reject { background: #ef4444; }
  form { display: flex; gap: 0.5rem; padding: 1rem; background: #1e293b; border-top: 1px solid #334155; }
  input[type="text"] { flex: 1; padding: 0.75rem 1rem; border: 1px solid #475569; border-radius: 0.5rem; background: #0f172a; color: #e2e8f0; }
  button { padding: 0.75rem 1.5rem; background: #3b82f6; color: #fff; border: none; border-radius: 0.5rem; cursor: pointer; }
  button:hover { background: #2563eb; }
  small { color: #64748b; font-size: 0.8rem; }
</style>
</head>
<body>
<header><h1>Mimir Core 0.4.0</h1><small>Calendario conectado · Finanza · Tareas · Confirmaciones</small></header>
<div id="chat"></div>
<form id="form"><input type="text" id="input" placeholder="Escribe a Mimir…" autocomplete="off"><button type="submit">Enviar</button></form>
<script>
const chat = document.getElementById('chat');
const form = document.getElementById('form');
const input = document.getElementById('input');
let pendingId = null;
function addMsg(text, cls) {
  const div = document.createElement('div');
  div.className = 'msg ' + cls;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}
function addConfirm(id, text) {
  const div = document.createElement('div');
  div.className = 'msg assistant confirm-box';
  div.innerHTML = text + '<br><button onclick="confirmReply(\'' + id + '\', true)">Aprobar</button><button onclick="confirmReply(\'' + id + '\', false)" class="reject">Rechazar</button>';
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}
async function send() {
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  addMsg(text, 'user');
  const res = await fetch('/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: text, session_id: 'web'})});
  const data = await res.json();
  if (data.confirmation) {
    pendingId = data.confirmation.id;
    addConfirm(pendingId, data.confirmation.reason + '<br><b>Tool:</b> ' + data.confirmation.tool + '<br><b>Args:</b> ' + JSON.stringify(data.confirmation.args));
  } else {
    addMsg(data.reply, 'assistant');
  }
}
async function confirmReply(id, approve) {
  if (!approve) {
    addMsg('Confirmacion rechazada.', 'system');
    pendingId = null;
    return;
  }
  const res = await fetch('/confirm/' + id, {method: 'POST'});
  const data = await res.json();
  if (data.ok) {
    addMsg('Accion confirmada y ejecutada: ' + JSON.stringify(data.data), 'assistant');
  } else {
    addMsg('Error al ejecutar: ' + data.error, 'system');
  }
  pendingId = null;
}
form.addEventListener('submit', (e) => { e.preventDefault(); send(); });
input.addEventListener('keypress', (e) => { if (e.key === 'Enter' && !pendingId) send(); });
</script>
</body>
</html>
''')
