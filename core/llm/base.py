from __future__ import annotations
from pydantic import BaseModel
from core.tools.base import ToolRequest

class ChatMessage(BaseModel):
    role: str
    content: str

class LLMResponse(BaseModel):
    text: str = ""
    tool_requests: list[ToolRequest] = []

class LLMProvider:
    """Abstraccion de proveedor (sec. 10). El Core nunca llama a Gemini directamente."""
    name: str = "base"

    def complete(self, system: str, context: str, tools: list[dict]) -> LLMResponse:
        raise NotImplementedError
