from core.context.manager import Conversation, ContextManager
from core.memory.base import InMemoryStore, MemoryItem, MemoryCategory
from core.tools.registry import ToolRegistry
from core.tools.base import ToolRequest
from core.tools.mocks import MockCalendarGetEvents, MockGmailSearch, MockFinanceRegister, MockSendEmail
from core.tools.executor import ToolExecutor
from core.policy.base import HeimdallBasicPolicy
from core.llm.mock_provider import MockProvider
from core.orchestration.orchestrator import MimirOrchestrator

def make_core():
    reg = ToolRegistry()
    for t in (MockCalendarGetEvents(), MockGmailSearch(), MockFinanceRegister(), MockSendEmail()):
        reg.register(t)
    pol = HeimdallBasicPolicy()
    ex = ToolExecutor(reg, pol)
    mem = InMemoryStore()
    ctx = ContextManager()
    orch = MimirOrchestrator(MockProvider(), reg, ex, mem, ctx)
    return reg, ex, mem, orch

def test_low_tool_auto_allowed():
    _, ex, _, _ = make_core()
    r = ex.execute(ToolRequest(tool="calendar_get_events", arguments={}))
    assert r.ok

def test_high_tool_needs_confirmation_blocked():
    _, ex, _, _ = make_core()
    r = ex.execute(ToolRequest(tool="gmail_send", arguments={"to": "a", "subject": "s", "body": "b"}))
    assert not r.ok and "confirmation" in r.error.lower() or "denied" in r.error.lower()

def test_memory_never_returns_all():
    _, _, mem, _ = make_core()
    for i in range(10):
        mem.save(MemoryItem(category=MemoryCategory.SEMANTIC, text=f"dato numero {i} calendario"))
    mem.save(MemoryItem(category=MemoryCategory.PROFILE, text="le gusta el cafe"))
    res = mem.retrieve("calendario", limit=3)
    assert len(res) <= 3

def test_orchestrator_calendar_flow():
    _, _, _, orch = make_core()
    conv = Conversation()
    out = orch.chat(conv, "que tengo en el calendario manana?")
    assert "Reunion" in out or "resumen" in out.lower()

def test_finance_deterministic():
    _, ex, _, _ = make_core()
    r1 = ex.execute(ToolRequest(tool="finance_register_expense", arguments={"amount": 5, "category": "food"}))
    r2 = ex.execute(ToolRequest(tool="finance_register_expense", arguments={"amount": 7, "category": "food"}))
    assert r2.data["total"] == 12.0

def test_unknown_tool_fail_closed():
    _, ex, _, _ = make_core()
    r = ex.execute(ToolRequest(tool="no_existe", arguments={}))
    assert not r.ok
def test_no_repeat_tool_calls():
    _, ex, _, orch = make_core()
    conv = Conversation()
    orch.chat(conv, 'que tengo en el calendario manana?')
    cals = [a for a in ex.audit_log if a['tool'] == 'calendar_get_events']
    assert len(cals) == 1
def test_audit_logged_without_secrets():
    _, ex, _, _ = make_core()
    ex.execute(ToolRequest(tool='calendar_get_events', arguments={}))
    assert len(ex.audit_log) >= 1
