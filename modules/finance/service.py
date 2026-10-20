from __future__ import annotations
from sqlalchemy import func, select
from infrastructure.database.base import Expense, init_db, get_engine
from sqlalchemy.orm import Session
class FinanceService:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url
        self.eng = init_db(db_url)
    def add_expense(self, amount: float, category: str = 'general', note: str = '') -> dict:
        with Session(self.eng) as s:
            e = Expense(amount=float(amount), category=category, note=note)
            s.add(e)
            s.commit()
            return {'id': e.id, 'amount': e.amount, 'category': e.category}
    def totals_by_category(self) -> list[dict]:
        with Session(self.eng) as s:
            rows = s.execute(select(Expense.category, func.sum(Expense.amount), func.count(Expense.id)).group_by(Expense.category)).all()
            return [{'category': r[0], 'total': float(r[1]), 'count': int(r[2])} for r in rows]
    def total(self) -> float:
        with Session(self.eng) as s:
            v = s.execute(select(func.sum(Expense.amount))).scalar()
            return float(v or 0.0)
    def export_csv(self) -> str:
        with Session(self.eng) as s:
            rows = s.execute(select(Expense.id, Expense.amount, Expense.category, Expense.note)).all()
            lines = ['id,amount,category,note']
            for r in rows:
                lines.append(str(r[0]) + ',' + str(r[1]) + ',' + str(r[2]) + ',' + str(r[3]))
            return chr(10).join(lines)
