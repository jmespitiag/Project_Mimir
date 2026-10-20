from __future__ import annotations
from sqlalchemy import create_engine, String, Float, DateTime, ForeignKey, Integer, func, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Category(Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False, default='expense')  # expense | income
    color: Mapped[str] = mapped_column(String(16), nullable=False, default='#6366f1')
    description: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Expense(Base):
    __tablename__ = 'expenses'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), nullable=False)
    note: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    date: Mapped[str] = mapped_column(String(64), nullable=False)  # ISO date string YYYY-MM-DD
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Income(Base):
    __tablename__ = 'incomes'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), nullable=False)
    note: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    date: Mapped[str] = mapped_column(String(64), nullable=False)  # ISO date string YYYY-MM-DD
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Budget(Base):
    __tablename__ = 'budgets'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False, default='monthly')  # monthly | yearly
    start_date: Mapped[str] = mapped_column(String(64), nullable=False)
    end_date: Mapped[str] = mapped_column(String(64), nullable=False)
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

def ensure_default_categories(url: str):
    """Crea categorías por defecto si no existen."""
    eng = get_engine(url)
    Session = sessionmaker(bind=eng, future=True)
    with Session() as s:
        from sqlalchemy import select
        existing = s.execute(select(Category)).scalars().all()
        if existing:
            return
        defaults = [
            Category(name='Alimentación', type='expense', color='#ef4444', description='Compras de comida y restaurantes'),
            Category(name='Transporte', type='expense', color='#f97316', description='Combustible, taxi, transporte público'),
            Category(name='Vivienda', type='expense', color='#8b5cf6', description='Renta, servicios, mantenimiento'),
            Category(name='Salud', type='expense', color='#10b981', description='Médicos, medicamentos, seguro'),
            Category(name='Ocio', type='expense', color='#3b82f6', description='Entretenimiento, suscripciones'),
            Category(name='Salario', type='income', color='#22c55e', description='Ingreso principal'),
            Category(name='Otros Ingresos', type='income', color='#84cc16', description='Ventas, reembolsos, otros'),
        ]
        for c in defaults:
            s.add(c)
        s.commit()
