from __future__ import annotations
from sqlalchemy import create_engine, String, Float, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from datetime import datetime
class Base(DeclarativeBase):
    pass
class Expense(Base):
    __tablename__ = 'expenses'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default='general')
    note: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
class TaskRow(Base):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    done: Mapped[int] = mapped_column(default=0)
    due: Mapped[str] = mapped_column(String(64), default='')
def get_engine(url: str):
    return create_engine(url, future=True)
def init_db(url: str):
    eng = get_engine(url)
    Base.metadata.create_all(eng)
    return eng
def SessionLocal(url: str):
    eng = get_engine(url)
    return sessionmaker(bind=eng, future=True)
