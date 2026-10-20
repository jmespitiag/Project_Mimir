from __future__ import annotations
from core.messaging.base import MessagingProvider, IncomingMessage, OutgoingMessage

class MockMessagingProvider(MessagingProvider):
    """Proveedor de mensajeria simulado para pruebas sin credenciales reales."""
    name: str = "mock"

    def receive(self, payload: dict) -> IncomingMessage:
        # Soporta formato mock ({from, text}) y formato Telegram ({message: {chat: {id}, text}})
        if 'message' in payload:
            msg = payload['message']
            chat = msg.get('chat', {})
            return IncomingMessage(
                from_number=str(chat.get('id', 'desconocido')),
                text=msg.get('text', ''),
                provider='mock',
                message_id=str(msg.get('message_id', '')),
            )
        return IncomingMessage(
            from_number=payload.get('from', 'desconocido'),
            text=payload.get('text', ''),
            provider=payload.get('provider', 'mock'),
            message_id=payload.get('message_id', 'mock-msg'),
        )

    def send(self, msg: OutgoingMessage) -> bool:
        # Solo registra, no envia realmente
        print(f'[MOCK MENSAJERIA] Enviando a {msg.to_number}: {msg.text[:80]}')
        return True
