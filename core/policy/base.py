from __future__ import annotations
import time
from pydantic import BaseModel
from core.tools.base import RiskLevel
class PolicyDecision(BaseModel):
    allowed: bool
    needs_confirmation: bool = False
    reason: str = ''
class PolicyInterface:
    def evaluate(self, tool_name: str, risk: RiskLevel, args: dict) -> PolicyDecision:
        raise NotImplementedError
class HeimdallBasicPolicy(PolicyInterface):
    def __init__(self, owner_id: str = 'owner') -> None:
        self.owner_id = owner_id
        self._hits: dict[str, list[float]] = {}
    def evaluate(self, tool_name: str, risk: RiskLevel, args: dict) -> PolicyDecision:
        now = time.time()
        lst = self._hits.get(tool_name, [])
        lst = [t for t in lst if now - t < 60]
        if len(lst) >= 30:
            return PolicyDecision(allowed=False, needs_confirmation=False, reason='rate limited')
        lst.append(now)
        self._hits[tool_name] = lst
        if risk == RiskLevel.LOW:
            return PolicyDecision(allowed=True, needs_confirmation=False, reason='LOW auto')
        if risk == RiskLevel.MEDIUM:
            return PolicyDecision(allowed=True, needs_confirmation=False, reason='MEDIUM auditado')
        if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return PolicyDecision(allowed=False, needs_confirmation=True, reason=risk.value + ' requiere confirmacion explicita del usuario')
        return PolicyDecision(allowed=False, needs_confirmation=False, reason='fail closed')
