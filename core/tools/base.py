from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
class RiskLevel(str, Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'
class ToolRequest(BaseModel):
    tool: str = Field(description='Nombre tecnico estable, ej. calendar_get_events')
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default='')
class ToolResult(BaseModel):
    ok: bool
    data: Any = None
    error: str = ''
    untrusted: bool = True
class Tool(BaseModel):
    name: str
    description: str
    risk_level: RiskLevel
    input_schema: dict[str, Any] = Field(default_factory=dict)
    concept: str = ''
    required_permissions: list[str] = Field(default_factory=list)
    confirmation_policy: str = 'auto-low'
    timeout_s: int = 20
    rate_limit_per_min: int = 30
    audit_policy: str = 'basic'
    def validate(self, args: dict[str, Any]) -> None:
        required = self.input_schema.get('required', [])
        for key in required:
            if key not in args:
                raise ValueError('missing required arg: ' + key)
    def run(self, args: dict[str, Any]) -> ToolResult:
        raise NotImplementedError
