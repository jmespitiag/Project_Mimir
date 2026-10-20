from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field

class IncomingMessage(BaseModel):
    from_number: str = Field(description="Numero de telefono del remitente (ej. +521234567890)")
    text: str = Field(description="Texto del mensaje entrante")
    provider: str = Field(default="whatsapp", description="Proveedor de mensajeria")
    message_id: str = Field(default="", description="ID del mensaje en el proveedor")

class OutgoingMessage(BaseModel):
    to_number: str = Field(description="Numero de telefono del destinatario")
    text: str = Field(description="Texto a enviar")
    provider: str = Field(default="whatsapp")

class MessagingProvider:
    """Abstracion de proveedor de mensajeria (como LLMProvider).
    El core nunca llama a WhatsApp directamente.
    """
    name: str = "base"

    def receive(self, payload: dict) -> IncomingMessage:
        raise NotImplementedError

    def send(self, msg: OutgoingMessage) -> bool:
        raise NotImplementedError
