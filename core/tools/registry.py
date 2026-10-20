from __future__ import annotations
from core.tools.base import Tool

class ToolRegistry:
    """Registro estable de herramientas. La interfaz no cambia al pasar de mock a Google."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name]

    def definitions_for_llm(self) -> list[dict]:
        # Solo definiciones, nunca secretos ni tokens (sec. 5 / 17)
        return [
            {"name": t.name, "description": t.description, "risk": t.risk_level.value}
            for t in self._tools.values()
        ]

    def names(self) -> list[str]:
        return sorted(self._tools.keys())
