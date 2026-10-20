from __future__ import annotations
from pydantic import BaseModel
from core.memory.base import MemoryItem

class Conversation(BaseModel):
    turns: list[dict] = []  # {"role": "user"|"assistant"|"tool", "content": str}

    def add(self, role: str, content: str) -> None:
        self.turns.append({"role": role, "content": content})

class RelevantContext(BaseModel):
    history_tail: list[dict] = []
    memories: list[MemoryItem] = []
    tool_outputs: list[dict] = []

class ContextManager:
    """Separa conversacion / memoria / temporal / herramientas (sec. 15). Control de costes."""

    def __init__(self, max_chars: int = 4000, tail: int = 6) -> None:
        self.max_chars = max_chars
        self.tail = tail

    def build(self, conv: Conversation, memories: list[MemoryItem], tools: list[dict]) -> RelevantContext:
        ctx = RelevantContext(
            history_tail=conv.turns[-self.tail:],
            memories=memories,
            tool_outputs=tools[-3:],
        )
        # Presupuesto simple por caracteres
        total = sum(len(str(t)) for t in conv.turns[-self.tail:])
        if total > self.max_chars:
            ctx.history_tail = conv.turns[-2:]
        return ctx
