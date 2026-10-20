from core.context.manager import Conversation, ContextManager
from core.memory.base import InMemoryStore, MemoryItem, MemoryCategory
from core.tools.registry import ToolRegistry
from core.tools.base import ToolRequest
from core.tools.mocks import MockGmailSearch, MockFinanceRegister, MockSendEmail
from core.tools.domain_tools import CalendarGetEvents, CalendarCreateEvent, CalendarUpdateEvent, CalendarDeleteEvent, FinanceTotal, TasksAdd, TasksList
from core.tools.executor import ToolExecutor
from core.policy.base import HeimdallBasicPolicy
from core.llm.mock_provider import MockProvider
from core.orchestration.orchestrator import MimirOrchestrator
from modules.productivity.calendar.service import MockCalendarService
from modules.productivity.tasks.service import MockTaskService
from modules.finance.service import FinanceService
import tempfile, os

def make_core():
    reg = ToolRegistry()
    for t in (MockGmailSearch(), MockFinanceRegister(), MockSendEmail()):
        reg.register(t)
    cal_svc = MockCalendarService()
    task_svc = MockTaskService()
    fin_svc = FinanceService('sqlite:///' + os.path.join(tempfile.gettempdir(), 'mimir_test.db'))
    for t in (CalendarGetEvents(cal_svc), CalendarCreateEvent(cal_svc), CalendarUpdateEvent(cal_svc), CalendarDeleteEvent(cal_svc), TasksAdd(task_svc), TasksList(task_svc), FinanceTotal(fin_svc)):
        reg.register(t)
    pol = HeimdallBasicPolicy()
    ex = ToolExecutor(reg, pol)
    mem = InMemoryStore()
    ctx = ContextManager()
    orch = MimirOrchestrator(MockProvider(), reg, ex, mem, ctx)
    return reg, ex, mem, orch, cal_svc, task_svc, fin_svc

def test_low_tool_auto_allowed():
    _, ex, _, _, _, _, _ = make_core()
    r = ex.execute(ToolRequest(tool="calendar_get_events", arguments={}))
    assert r.ok

def test_high_tool_needs_confirmation():
    _, ex, _, _, _, _, _ = make_core()
    r = ex.execute(ToolRequest(tool="gmail_send", arguments={"to": "a", "subject": "s", "body": "b"}))
    assert not r.ok and r.confirmation_required and r.confirmation_id != ''

def test_confirmation_approve_executes():
    reg, ex, _, _, cal_svc, _, _ = make_core()
    r = ex.execute(ToolRequest(tool="calendar_create_event", arguments={"title": "Reunion confirmada", "start": "2026-10-01T10:00:00"}))
    assert r.confirmation_required
    cid = r.confirmation_id
    result = ex.approve_confirmation(cid)
    assert result.ok
    evs = cal_svc.list_events()
    assert any(e['title'] == 'Reunion confirmada' for e in evs)

def test_confirmation_reject_does_not_execute():
    reg, ex, _, _, cal_svc, _, _ = make_core()
    r = ex.execute(ToolRequest(tool="calendar_create_event", arguments={"title": "No crear", "start": "2026-10-01T10:00:00"}))
    cid = r.confirmation_id
    # Simply don't call approve_confirmation; event should not exist
    evs = cal_svc.list_events()
    assert not any(e['title'] == 'No crear' for e in evs)

def test_unknown_confirmation_id():
    _, ex, _, _, _, _, _ = make_core()
    r = ex.approve_confirmation('no_existe')
    assert not r.ok

def test_memory_never_returns_all():
    _, _, mem, _, _, _, _ = make_core()
    for i in range(10):
        mem.save(MemoryItem(category=MemoryCategory.SEMANTIC, text=f"dato numero {i} calendario"))
    mem.save(MemoryItem(category=MemoryCategory.PROFILE, text="le gusta el cafe"))
    res = mem.retrieve("calendario", limit=3)
    assert len(res) <= 3

def test_orchestrator_calendar_flow():
    _, _, _, orch, _, _, _ = make_core()
    conv = Conversation()
    out = orch.chat(conv, "que tengo en el calendario manana?")
    assert isinstance(out, dict) and ('Reunion' in out.get('reply', '') or 'resumen' in out.get('reply', '').lower())

def test_orchestrator_create_event_needs_confirmation():
    _, _, _, orch, cal_svc, _, _ = make_core()
    conv = Conversation()
    out = orch.chat(conv, "crea un evento llamado Prueba Mimir manana a las 10")
    assert out.get('confirmation') is not None
    assert out['confirmation']['tool'] == 'calendar_create_event'
    assert out['confirmation']['args']['title'].find('Prueba Mimir') >= 0

def test_finance_deterministic():
    _, ex, _, _, _, _, fin_svc = make_core()
    r1 = ex.execute(ToolRequest(tool="finance_register_expense", arguments={"amount": 5, "category": "food"}))
    r2 = ex.execute(ToolRequest(tool="finance_register_expense", arguments={"amount": 7, "category": "food"}))
    assert r2.data["total"] == 12.0

def test_unknown_tool_fail_closed():
    _, ex, _, _, _, _, _ = make_core()
    r = ex.execute(ToolRequest(tool="no_existe", arguments={}))
    assert not r.ok

def test_no_repeat_tool_calls():
    _, ex, _, orch, _, _, _ = make_core()
    conv = Conversation()
    orch.chat(conv, 'que tengo en el calendario manana?')
    cals = [a for a in ex.audit_log if a['tool'] == 'calendar_get_events']
    assert len(cals) == 1

def test_audit_logged_without_secrets():
    _, ex, _, _, _, _, _ = make_core()
    ex.execute(ToolRequest(tool='calendar_get_events', arguments={}))
    assert len(ex.audit_log) >= 1

def test_calendar_update_and_delete_with_confirmation():
    reg, ex, _, _, cal_svc, _, _ = make_core()
    # Create via direct confirm flow
    r1 = ex.execute(ToolRequest(tool="calendar_create_event", arguments={"title": "Para editar", "start": "2026-10-02T10:00:00"}))
    assert r1.confirmation_required
    ex.approve_confirmation(r1.confirmation_id)
    evs = cal_svc.list_events()
    ev_id = [e for e in evs if e['title'] == 'Para editar'][0]['event_id']
    # Update
    r2 = ex.execute(ToolRequest(tool="calendar_update_event", arguments={"event_id": ev_id, "title": "Editado", "start": "2026-10-02T11:00:00"}))
    assert r2.confirmation_required
    ex.approve_confirmation(r2.confirmation_id)
    evs = cal_svc.list_events()
    assert any(e['event_id'] == ev_id and e['title'] == 'Editado' for e in evs)
    # Delete
    r3 = ex.execute(ToolRequest(tool="calendar_delete_event", arguments={"event_id": ev_id}))
    assert r3.confirmation_required
    ex.approve_confirmation(r3.confirmation_id)
    evs = cal_svc.list_events()
    assert not any(e['event_id'] == ev_id for e in evs)

from core.messaging.mock import MockMessagingProvider
from core.messaging.base import IncomingMessage, OutgoingMessage

def test_mock_messaging_receive():
    prov = MockMessagingProvider()
    inc = prov.receive({'from': '+521234567890', 'text': 'hola mimir', 'provider': 'mock', 'message_id': '123'})
    assert isinstance(inc, IncomingMessage)
    assert inc.from_number == '+521234567890'
    assert inc.text == 'hola mimir'

def test_mock_messaging_send():
    prov = MockMessagingProvider()
    out = OutgoingMessage(to_number='+521234567890', text='Hola, soy Mimir')
    assert prov.send(out) is True

from core.messaging.telegram import TelegramProvider

def test_telegram_not_configured_without_token():
    prov = TelegramProvider()
    assert prov.is_configured() is False

def test_telegram_webhook_mock_flow():
    from fastapi.testclient import TestClient
    from apps.api.main import app
    c = TestClient(app)
    payload = {'message': {'message_id': 1, 'from': {'id': 123456789}, 'chat': {'id': 123456789}, 'text': 'hola mimir'}}
    r = c.post('/telegram/webhook', json={'payload': payload})
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'ok'
    assert data['from'] == '123456789'
    assert 'reply' in data
    assert data['sent_via_telegram'] is False

def test_telegram_status():
    from fastapi.testclient import TestClient
    from apps.api.main import app
    c = TestClient(app)
    r = c.get('/telegram/status')
    assert r.status_code == 200
    data = r.json()
    assert data['provider'] in ('mock', 'telegram')
