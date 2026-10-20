from __future__ import annotations
import os
import io
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import Session
from infrastructure.database.base import (
    Expense, Income, Category, Budget, get_engine, init_db, SessionLocal, ensure_default_categories
)

def _round2(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

class FinanceService:
    """Draupnir: dominio financiero con cálculos deterministas en SQL.
    Fuente de verdad: PostgreSQL/SQLite. Excel/Sheets solo vista/exportación.
    """

    def __init__(self, db_url: str) -> None:
        self.db_url = db_url
        self.eng = init_db(db_url)
        self._ensure_schema()
        ensure_default_categories(db_url)

    def _ensure_schema(self) -> None:
        """En desarrollo local (SQLite), asegura esquema limpio recreando tablas."""
        if not self.db_url.startswith('sqlite:///./'):
            return
        # Para desarrollo local: dropear y recrear tablas para evitar esquemas viejos
        from infrastructure.database.base import Base
        Base.metadata.drop_all(self.eng)
        Base.metadata.create_all(self.eng)

    # ── Categorías ──────────────────────────────────────────────────────
    def list_categories(self, type_filter: str | None = None) -> list[dict]:
        with Session(self.eng) as s:
            stmt = select(Category)
            if type_filter:
                stmt = stmt.where(Category.type == type_filter)
            rows = s.execute(stmt.order_by(Category.name)).scalars().all()
            return [{'id': c.id, 'name': c.name, 'type': c.type, 'color': c.color, 'is_active': c.is_active} for c in rows]

    def add_category(self, name: str, type_: str = 'expense', color: str = '#6366f1') -> dict:
        with Session(self.eng) as s:
            c = Category(name=name, type=type_, color=color)
            s.add(c)
            s.commit()
            return {'id': c.id, 'name': c.name, 'type': c.type}

    # ── Gastos ──────────────────────────────────────────────────────────
    def add_expense(self, amount: float, category: str = 'general', note: str = '', date: str | None = None) -> dict:
        date = date or datetime.utcnow().strftime('%Y-%m-%d')
        with Session(self.eng) as s:
            cat = s.execute(select(Category).where(Category.name == category)).scalar_one_or_none()
            if not cat:
                cat = Category(name=category, type='expense')
                s.add(cat)
                s.flush()
            e = Expense(amount=float(amount), category_id=cat.id, note=note, date=date)
            s.add(e)
            s.commit()
            return {'id': e.id, 'amount': e.amount, 'category': cat.name, 'date': e.date, 'note': e.note}

    def add_income(self, amount: float, category: str = 'general', note: str = '', date: str | None = None) -> dict:
        date = date or datetime.utcnow().strftime('%Y-%m-%d')
        with Session(self.eng) as s:
            cat = s.execute(select(Category).where(Category.name == category)).scalar_one_or_none()
            if not cat:
                cat = Category(name=category, type='income')
                s.add(cat)
                s.flush()
            i = Income(amount=float(amount), category_id=cat.id, note=note, date=date)
            s.add(i)
            s.commit()
            return {'id': i.id, 'amount': i.amount, 'category': cat.name, 'date': i.date, 'note': i.note}

    def list_expenses(self, limit: int = 50, category: str | None = None, start: str | None = None, end: str | None = None) -> list[dict]:
        with Session(self.eng) as s:
            stmt = select(Expense, Category.name).join(Category).order_by(Expense.created_at.desc()).limit(limit)
            if category:
                stmt = stmt.where(Category.name == category)
            if start:
                stmt = stmt.where(Expense.date >= start)
            if end:
                stmt = stmt.where(Expense.date <= end)
            rows = s.execute(stmt).all()
            return [{'id': e.id, 'amount': e.amount, 'category': cname, 'note': e.note, 'date': e.date, 'created_at': e.created_at.isoformat()} for e, cname in rows]

    def list_incomes(self, limit: int = 50, category: str | None = None, start: str | None = None, end: str | None = None) -> list[dict]:
        with Session(self.eng) as s:
            stmt = select(Income, Category.name).join(Category).order_by(Income.created_at.desc()).limit(limit)
            if category:
                stmt = stmt.where(Category.name == category)
            if start:
                stmt = stmt.where(Income.date >= start)
            if end:
                stmt = stmt.where(Income.date <= end)
            rows = s.execute(stmt).all()
            return [{'id': i.id, 'amount': i.amount, 'category': cname, 'note': i.note, 'date': i.date, 'created_at': i.created_at.isoformat()} for i, cname in rows]

    def delete_expense(self, expense_id: int) -> dict:
        with Session(self.eng) as s:
            e = s.get(Expense, expense_id)
            if not e:
                raise KeyError('expense not found')
            cat = s.get(Category, e.category_id)
            amount = e.amount
            s.delete(e)
            s.commit()
            return {'id': expense_id, 'category': cat.name if cat else 'desconocida', 'amount': amount, 'deleted': True}

    def delete_income(self, income_id: int) -> dict:
        with Session(self.eng) as s:
            i = s.get(Income, income_id)
            if not i:
                raise KeyError('income not found')
            cat = s.get(Category, i.category_id)
            amount = i.amount
            s.delete(i)
            s.commit()
            return {'id': income_id, 'category': cat.name if cat else 'desconocida', 'amount': amount, 'deleted': True}

    # ── Cálculos deterministas (SQL) ────────────────────────────────────
    def summary(self, start: str | None = None, end: str | None = None) -> dict:
        with Session(self.eng) as s:
            exp_stmt = select(func.sum(Expense.amount))
            inc_stmt = select(func.sum(Income.amount))
            if start:
                exp_stmt = exp_stmt.where(Expense.date >= start)
                inc_stmt = inc_stmt.where(Income.date >= start)
            if end:
                exp_stmt = exp_stmt.where(Expense.date <= end)
                inc_stmt = inc_stmt.where(Income.date <= end)
            total_exp = s.execute(exp_stmt).scalar() or 0.0
            total_inc = s.execute(inc_stmt).scalar() or 0.0
            return {
                'total_income': _round2(total_inc),
                'total_expense': _round2(total_exp),
                'balance': _round2(total_inc - total_exp),
            }

    def expenses_by_category(self, start: str | None = None, end: str | None = None) -> list[dict]:
        with Session(self.eng) as s:
            stmt = (
                select(Category.name, func.sum(Expense.amount), func.count(Expense.id))
                .join(Expense)
                .group_by(Category.name)
                .order_by(func.sum(Expense.amount).desc())
            )
            if start:
                stmt = stmt.where(Expense.date >= start)
            if end:
                stmt = stmt.where(Expense.date <= end)
            rows = s.execute(stmt).all()
            return [{'category': r[0], 'total': _round2(r[1]), 'count': int(r[2])} for r in rows]

    def incomes_by_category(self, start: str | None = None, end: str | None = None) -> list[dict]:
        with Session(self.eng) as s:
            stmt = (
                select(Category.name, func.sum(Income.amount), func.count(Income.id))
                .join(Income)
                .group_by(Category.name)
                .order_by(func.sum(Income.amount).desc())
            )
            if start:
                stmt = stmt.where(Income.date >= start)
            if end:
                stmt = stmt.where(Income.date <= end)
            rows = s.execute(stmt).all()
            return [{'category': r[0], 'total': _round2(r[1]), 'count': int(r[2])} for r in rows]

    def monthly_totals(self, months: int = 6) -> list[dict]:
        with Session(self.eng) as s:
            exp = (
                select(Expense.date, func.sum(Expense.amount))
                .group_by(Expense.date)
                .order_by(Expense.date.desc())
                .limit(months)
            )
            inc = (
                select(Income.date, func.sum(Income.amount))
                .group_by(Income.date)
                .order_by(Income.date.desc())
                .limit(months)
            )
            exp_rows = s.execute(exp).all()
            inc_rows = s.execute(inc).all()
            exp_map = {r[0]: _round2(r[1]) for r in exp_rows}
            inc_map = {r[0]: _round2(r[1]) for r in inc_rows}
            dates = sorted(set(list(exp_map.keys()) + list(inc_map.keys())))
            return [{'date': d, 'income': inc_map.get(d, 0.0), 'expense': exp_map.get(d, 0.0), 'balance': _round2(inc_map.get(d, 0.0) - exp_map.get(d, 0.0))} for d in dates]

    # ── Importación desde Excel/CSV (carga inicial, no source of truth) ──
    def import_expenses_from_csv(self, csv_text: str) -> dict:
        """Importa gastos desde CSV. Formato: amount,category,note,date"""
        import csv
        reader = csv.DictReader(io.StringIO(csv_text))
        count = 0
        for row in reader:
            self.add_expense(
                amount=float(row['amount']),
                category=row.get('category', 'general'),
                note=row.get('note', ''),
                date=row.get('date', datetime.utcnow().strftime('%Y-%m-%d')),
            )
            count += 1
        return {'imported': count, 'type': 'expenses'}

    def import_expenses_from_excel(self, file_path: str) -> dict:
        """Importa gastos desde un archivo Excel (.xlsx)."""
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError('pandas y openpyxl no instalados. Ejecuta: pip install pandas openpyxl')
        df = pd.read_excel(file_path)
        required = {'amount', 'category'}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f'Columnas faltantes en Excel: {missing}')
        count = 0
        for _, row in df.iterrows():
            self.add_expense(
                amount=float(row['amount']),
                category=str(row.get('category', 'general')),
                note=str(row.get('note', '')),
                date=str(row.get('date', datetime.utcnow().strftime('%Y-%m-%d'))),
            )
            count += 1
        return {'imported': count, 'type': 'expenses', 'source': file_path}

    def import_incomes_from_excel(self, file_path: str) -> dict:
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError('pandas y openpyxl no instalados. Ejecuta: pip install pandas openpyxl')
        df = pd.read_excel(file_path)
        required = {'amount', 'category'}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f'Columnas faltantes en Excel: {missing}')
        count = 0
        for _, row in df.iterrows():
            self.add_income(
                amount=float(row['amount']),
                category=str(row.get('category', 'general')),
                note=str(row.get('note', '')),
                date=str(row.get('date', datetime.utcnow().strftime('%Y-%m-%d'))),
            )
            count += 1
        return {'imported': count, 'type': 'incomes', 'source': file_path}

    # ── Exportación (vista, no source of truth) ─────────────────────────
    def export_expenses_csv(self, start: str | None = None, end: str | None = None) -> str:
        rows = self.list_expenses(limit=10000, start=start, end=end)
        lines = ['id,amount,category,note,date,created_at']
        for r in rows:
            lines.append(f"{r['id']},{r['amount']},{r['category']},{r['note']},{r['date']},{r['created_at']}")
        return chr(10).join(lines)

    def export_incomes_csv(self, start: str | None = None, end: str | None = None) -> str:
        rows = self.list_incomes(limit=10000, start=start, end=end)
        lines = ['id,amount,category,note,date,created_at']
        for r in rows:
            lines.append(f"{r['id']},{r['amount']},{r['category']},{r['note']},{r['date']},{r['created_at']}")
        return chr(10).join(lines)

    def export_summary_csv(self, start: str | None = None, end: str | None = None) -> str:
        summary = self.summary(start, end)
        by_cat = self.expenses_by_category(start, end)
        lines = ['metric,value']
        lines.append(f"total_income,{summary['total_income']}")
        lines.append(f"total_expense,{summary['total_expense']}")
        lines.append(f"balance,{summary['balance']}")
        lines.append('')
        lines.append('category,total,count')
        for c in by_cat:
            lines.append(f"{c['category']},{c['total']},{c['count']}")
        return chr(10).join(lines)
