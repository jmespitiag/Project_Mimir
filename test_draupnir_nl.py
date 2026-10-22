from core.config.settings import Settings
from core.llm.mock_provider import MockProvider
from core.orchestration.orchestrator import MimirOrchestrator
from core.tools.registry import ToolRegistry
from core.tools.mocks import MockGmailSearch, MockSendEmail
from core.tools.domain_tools import (
    CalendarGetEvents, CalendarCreateEvent, CalendarUpdateEvent, CalendarDeleteEvent,
    TasksAdd, TasksList,
    FinanceRegisterExpense, FinanceRegisterIncome, FinanceGetSummary, FinanceGetExpenses,
    FinanceGetIncomes, FinanceDeleteExpense, FinanceDeleteIncome, FinanceGetCategories,
)
from core.tools.executor import ToolExecutor
from core.policy.base import HeimdallBasicPolicy
from core.context.manager import Conversation, ContextManager
from core.memory.base import InMemoryStore, MemoryItem, MemoryCategory
from modules.productivity.calendar.service import MockCalendarService
from modules.productivity.tasks.service import MockTaskService
from modules.finance.service import FinanceService
import tempfile, os

settings = Settings()
registry = ToolRegistry()
for t in (MockGmailSearch(), MockSendEmail()):
    registry.register(t)
cal_svc = MockCalendarService()
task_svc = MockTaskService()
fin_svc = FinanceService('sqlite:///' + os.path.join(tempfile.gettempdir(), 'test_draupnir.db'))
for t in (
    CalendarGetEvents(cal_svc), CalendarCreateEvent(cal_svc), CalendarUpdateEvent(cal_svc), CalendarDeleteEvent(cal_svc),
    TasksAdd(task_svc), TasksList(task_svc),
    FinanceRegisterExpense(fin_svc), FinanceRegisterIncome(fin_svc), FinanceGetSummary(fin_svc),
    FinanceGetExpenses(fin_svc), FinanceGetIncomes(fin_svc), FinanceDeleteExpense(fin_svc),
    FinanceDeleteIncome(fin_svc), FinanceGetCategories(fin_svc),
):
    registry.register(t)
policy = HeimdallBasicPolicy()
executor = ToolExecutor(registry, HeimdallBasicPolicy())
memory = InMemoryStore()
memory.save(MemoryItem(category=MemoryCategory.PROFILE, text='Propietario Roman'))
ctx = ContextManager()
orch = MimirOrchestrator(MockProvider(), registry, executor, memory, ctx, max_steps=3)

tests = [
    'registra un gasto de 25 en transporte para metro',
    'registra un ingreso de 2000 en salario por nomina',
    'cual es mi resumen financiero',
    'muestra mis gastos',
    'muestra mis ingresos',
    'que categorias tengo',
    'crea un evento llamado Reunion manana a las 10 con recordatorio 3 dias antes',
]

for msg in tests:
    conv = Conversation()
    out = orch.chat(conv, msg)
    reply = str(out.get('reply', out))
    # Remove emojis for Windows console
    safe_reply = reply.encode('ascii', 'ignore').decode('ascii')
    print('>>> ' + msg)
    print('<<< ' + safe_reply[:300])
    print('---')