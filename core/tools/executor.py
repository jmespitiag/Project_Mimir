from __future__ import annotations
import time
from core.tools.registry import ToolRegistry
from core.tools.base import ToolRequest, ToolResult
from core.policy.base import PolicyInterface

class ToolExecutor:
    """Frontera LLM <-> infraestructura (sec. 5):
    LLM -> ToolRequest -> validacion -> policy -> ejecucion -> audit -> resultado.
    El LLM nunca toca infraestructura directamente.
    """

    def __init__(self, registry: ToolRegistry, policy: PolicyInterface) -> None:
        self.registry = registry
        self.policy = policy
        self.audit_log: list[dict] = []

    def execute(self, req: ToolRequest, user_id: str = "owner") -> ToolResult:
        started = time.time()
        try:
            tool = self.registry.get(req.tool)
        except KeyError:
            return ToolResult(ok=False, error=f"unknown tool: {req.tool}")
        try:
            tool.validate(req.arguments)
        except ValueError as e:
            return ToolResult(ok=False, error=f"schema validation: {e}")
        decision = self.policy.evaluate(tool.name, tool.risk_level, req.arguments)
        if not decision.allowed:
            self._audit(user_id, tool.name, "denied", decision.reason, started)
            return ToolResult(ok=False, error=f"policy denied: {decision.reason}")
        try:
            result = tool.run(req.arguments)
        except Exception as e:  # fail seguro y recuperable
            self._audit(user_id, tool.name, "error", str(e), started)
            return ToolResult(ok=False, error=f"tool error: {e}")
        self._audit(user_id, tool.name, "ok", decision.reason, started)
        return result

    def _audit(self, user_id: str, tool: str, outcome: str, reason: str, started: float) -> None:
        # Nunca cuerpos completos ni secretos (sec. 18)
        self.audit_log.append({
            "user_id": user_id,
            "tool": tool,
            "outcome": outcome,
            "reason": reason,
            "duration_ms": int((time.time() - started) * 1000),
        })
