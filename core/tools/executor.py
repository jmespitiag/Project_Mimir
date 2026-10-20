from __future__ import annotations
import time
import uuid
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
        self.pending_confirmations: dict[str, dict] = {}

    def execute(self, req: ToolRequest, user_id: str = "owner", confirmed: bool = False) -> ToolResult:
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
        if decision.needs_confirmation and not confirmed and not decision.allowed:
            cid = str(uuid.uuid4())[:8]
            self.pending_confirmations[cid] = {
                'tool_request': req.model_dump(),
                'tool_name': tool.name,
                'arguments': req.arguments,
                'user_id': user_id,
            }
            self._audit(user_id, tool.name, "pending_confirmation", decision.reason, started)
            return ToolResult(
                ok=False,
                confirmation_required=True,
                confirmation_id=cid,
                confirmation_tool=tool.name,
                confirmation_args=req.arguments,
                error=decision.reason,
            )
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

    def approve_confirmation(self, confirmation_id: str, user_id: str = "owner") -> ToolResult:
        if confirmation_id not in self.pending_confirmations:
            return ToolResult(ok=False, error="confirmation not found or expired")
        pending = self.pending_confirmations.pop(confirmation_id)
        req = ToolRequest(**pending['tool_request'])
        tool = self.registry.get(req.tool)
        tool.validate(req.arguments)
        try:
            result = tool.run(req.arguments)
        except Exception as e:
            self._audit(user_id, tool.name, "error", str(e), time.time())
            return ToolResult(ok=False, error=f"tool error: {e}")
        self._audit(user_id, tool.name, "ok", "user confirmed", time.time())
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
