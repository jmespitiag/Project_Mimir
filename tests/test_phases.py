import os
from core.tools.base import ToolRequest
from core.tools.registry import ToolRegistry
from core.tools.executor import ToolExecutor
from core.policy.base import HeimdallBasicPolicy
from modules.finance.service import FinanceService
from modules.productivity.tasks.service import MockTaskService
from core.tools.domain_tools import FinanceTotal, TasksAdd
from infrastructure.google.oauth import NeedsGoogleAuth
from infrastructure.google.calendar_adapter import GoogleCalendarAdapter
def test_finance_sql_deterministic(tmp_path):
    url = 'sqlite:///' + str(tmp_path / 't.db')
    svc = FinanceService(url)
    svc.add_expense(5, 'food')
    svc.add_expense(7, 'food')
    svc.add_expense(10, 'transport')
    assert svc.total() == 22.0
    by = {x['category']: x['total'] for x in svc.totals_by_category()}
    assert by['food'] == 12.0 and by['transport'] == 10.0
def test_tasks_mock():
    svc = MockTaskService()
    d = svc.add('probar mimir')
    assert svc.list()[0]['title'] == 'probar mimir'
    svc.complete(d['id'])
    assert svc.list()[0]['done'] is True
def test_high_blocked_and_low_allowed():
    from core.tools.mocks import MockCalendarGetEvents, MockSendEmail
    reg = ToolRegistry()
    reg.register(MockCalendarGetEvents())
    reg.register(MockSendEmail())
    ex = ToolExecutor(reg, HeimdallBasicPolicy())
    assert ex.execute(ToolRequest(tool='calendar_get_events', arguments={})).ok
    r = ex.execute(ToolRequest(tool='gmail_send', arguments={'to': 'a', 'subject': 's', 'body': 'b'}))
    assert not r.ok
def test_google_adapter_state():
    import pathlib
    from infrastructure.google.calendar_adapter import GoogleCalendarAdapter, TOKEN_PATH
    from infrastructure.google.oauth import NeedsGoogleAuth
    if not TOKEN_PATH.exists():
        try:
            GoogleCalendarAdapter()
            assert False, 'debio exigir auth sin token'
        except NeedsGoogleAuth:
            assert True
    else:
        # Con token real, el adapter carga y lista eventos (integracion real)
        ad = GoogleCalendarAdapter()
        evs = ad.list_events()
        assert isinstance(evs, list)
