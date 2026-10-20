from __future__ import annotations
from datetime import datetime, timedelta
from core.llm.base import LLMProvider, LLMResponse
from core.tools.base import ToolRequest
class MockProvider(LLMProvider):
    name: str = 'mock'
    def complete(self, system: str, context: str, tools: list[dict]) -> LLMResponse:
        if 'UNTRUSTED DATA' in context or 'Continua con estos resultados' in context:
            return LLMResponse(text='He consultado herramientas. Sintetizo con los datos obtenidos.')
        low = context.lower()
        creation = any(w in low for w in ['crea', 'crear', 'create', 'add', 'agregar'])
        if ('evento' in low or 'event' in low) and creation:
            title = context.split('USUARIO:')[-1].strip() if 'USUARIO:' in context else context[:60]
            for prefix in ['crea un evento llamado ', 'crear evento ', 'create event ', 'agregar evento ', 'add event ']:
                if title.lower().startswith(prefix):
                    title = title[len(prefix):].strip()
            start = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT10:00:00')
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='calendar_create_event', arguments={'title': title, 'start': start}, reason='usuario pide crear evento')])
        if 'calendario' in low or 'calendar' in low or 'eventos' in low:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='calendar_get_events', arguments={}, reason='usuario pide calendario')])
        if 'correo' in low or 'email' in low or 'gmail' in low:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='gmail_search', arguments={'query': context[:60]}, reason='buscar correos')])
        if 'gast' in low or 'expense' in low:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_register_expense', arguments={'amount': 10.0, 'category': 'general'}, reason='registrar gasto demo')])
        return LLMResponse(text='Mock: entendi tu mensaje. Soy el nucleo Mimir sin Gemini aun.')
