from __future__ import annotations
from enum import Enum
from pydantic import BaseModel

class MemoryCategory(str, Enum):
    PROFILE = "profile"
    PREFERENCES = "preferences"
    ROUTINES = "routines"
    PROJECTS = "projects"
    IMPORTANT_FACTS = "important_facts"
    TEMPORARY = "temporary"
    SEMANTIC = "semantic"

class MemoryItem(BaseModel):
    category: MemoryCategory
    text: str
    weight: float = 1.0

class MemoryStore:
    def save(self, item: MemoryItem) -> None:
        raise NotImplementedError

    def retrieve(self, query: str, limit: int = 3) -> list[MemoryItem]:
        raise NotImplementedError

class InMemoryStore(MemoryStore):
    """Muninn conceptual. Fase Core: local/simple. Postgres/persistente despues."""

    def __init__(self) -> None:
        self._items: list[MemoryItem] = []

    def save(self, item: MemoryItem) -> None:
        # Evitar duplicados simples
        if item.text not in {i.text for i in self._items}:
            self._items.append(item)

    def retrieve(self, query: str, limit: int = 3) -> list[MemoryItem]:
        # Relevancia ingenua por solape de palabras: nunca enviar toda la memoria (sec. 14)
        q = set(query.lower().split())
        scored = sorted(
            self._items,
            key=lambda i: len(q & set(i.text.lower().split())) * i.weight,
            reverse=True,
        )
        relevant = [i for i in scored if len(q & set(i.text.lower().split())) > 0]
        return relevant[:limit]
