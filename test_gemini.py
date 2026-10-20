from core.config.settings import Settings
from core.llm.gemini_provider import GeminiProvider
from core.orchestration.orchestrator import MimirOrchestrator
from core.tools.registry import ToolRegistry
from core.tools.mocks import MockGmailSearch, MockSendEmail
from core.tools.domain_tools import CalendarGetEvents, CalendarCreateEvent, CalendarUpdateEvent, CalendarDeleteEvent, TasksAdd, TasksList, FinanceGetSummary
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
db_file = os.path.join(tempfile.gettempdir(), 'test_gemini.db')
fin_svc = FinanceService('sqlite:///' + db_file)
for t in (CalendarGetEvents(MockCalendarService()), CalendarCreateEvent(MockCalendarService()), CalendarUpdateEvent(MockCalendarService()), CalendarDeleteEvent(MockCalendarService()), TasksAdd(task_svc), TasksList(task_svc), FinanceGetSummary(FinanceService('sqlite:///' + db_file))):
    registry.register(t)
policy = HeimdallBasicPolicy()
executor = ToolExecutor(registry, HeimdallBasicPolicy())
memory = InMemoryStore()
ctx = ContextManager()
llm = GeminiProvider(model=settings.gemini_model, api_key=settings.google_api_key)
orch = MimirOrchestrator(llm, registry, executor, InMemoryStore(), ContextManager(), max_steps=3)
conv = Conversation()
out = orch.chat(conv, 'Hola, ¿cómo estás?')
print('Respuesta:', out['reply'][:500])