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
        creation = any(w in low for w in ['crea', 'crear', 'create', 'add', 'agregar', 'registra', 'registrar'])
        delete = any(w in low for w in ['borra', 'borrar', 'elimina', 'eliminar', 'delete', 'remove'])

        # ── Calendario ──────────────────────────────────────────────────
        if ('evento' in low or 'event' in low) and creation:
            title = context.split('USUARIO:')[-1].strip() if 'USUARIO:' in context else context[:60]
            for prefix in ['crea un evento llamado ', 'crear evento ', 'create event ', 'agregar evento ', 'add event ', 'registra un evento ', 'registrar evento ']:
                if title.lower().startswith(prefix):
                    title = title[len(prefix):].strip()
            start = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT10:00:00')
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='calendar_create_event', arguments={'title': title, 'start': start}, reason='usuario pide crear evento')])

        if ('evento' in low or 'event' in low) and delete:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='calendar_delete_event', arguments={'event_id': 'demo'}, reason='usuario pide borrar evento')])

        if 'calendario' in low or 'calendar' in low or 'eventos' in low:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='calendar_get_events', arguments={}, reason='usuario pide calendario')])

        # ── Correo ──────────────────────────────────────────────────────
        if 'correo' in low or 'email' in low or 'gmail' in low:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='gmail_search', arguments={'query': context[:60]}, reason='buscar correos')])

        # ── Finanzas (Draupnir) ────────────────────────────────────────
        # Gastos
        if ('gast' in low or 'expense' in low) and creation:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_register_expense', arguments={'amount': 10.0, 'category': 'general'}, reason='registrar gasto demo')])

        if ('gast' in low or 'expense' in low) and delete:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_delete_expense', arguments={'expense_id': 1}, reason='borrar gasto demo')])

        if 'gast' in low or 'expense' in low or 'gasto' in low:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_get_expenses', arguments={}, reason='listar gastos')])

        # Ingresos
        if ('ingres' in low or 'income' in low or 'salario' in low or 'sueldo' in low) and creation:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_register_income', arguments={'amount': 1000.0, 'category': 'salario'}, reason='registrar ingreso demo')])

        if ('ingres' in low or 'income' in low) and delete:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_delete_income', arguments={'income_id': 1}, reason='borrar ingreso demo')])

        if 'ingres' in low or 'income' in low or 'salario' in low or 'sueldo' in low:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_get_incomes', arguments={}, reason='listar ingresos')])

        # Resumen y categorías
        if 'resumen' in low or 'summary' in low or 'balance' in low or 'total' in low or 'cuánto' in low or 'cuanto' in low:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_get_summary', arguments={}, reason='resumen financiero')])

        if 'categ' in low or 'categor' in low:
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_get_categories', arguments={}, reason='listar categorías')])

        # Import/Export
        if 'import' in low and ('excel' in low or 'csv' in low):
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_import_excel', arguments={'file_path': 'demo.xlsx', 'type': 'expense'}, reason='importar excel demo')])

        if 'export' in low and ('excel' in low or 'csv' in low):
            return LLMResponse(text='', tool_requests=[ToolRequest(tool='finance_export_csv', arguments={}, reason='exportar csv')])

        # ── Default ────────────────────────────────────────────────────
        return LLMResponse(text='Mock: entendi tu mensaje. Soy el nucleo Mimir sin Gemini aun. Puedo ayudarte con calendario, gastos, ingresos, resumen financiero, categorías, import/export.')