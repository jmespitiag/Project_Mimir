from __future__ import annotations
import os
import httpx
from core.messaging.base import MessagingProvider, IncomingMessage, OutgoingMessage

class WhatsAppProvider(MessagingProvider):
    """Adapter real a WhatsApp Business API (Meta).
    Falla cerrado si no hay credenciales configuradas.
    Necesita: WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID.
    """

    name: str = "whatsapp"

    def __init__(self) -> None:
        self.access_token = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
        self.phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
        self.verify_token = os.environ.get('WHATSAPP_VERIFY_TOKEN', '')

    def is_configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    def receive(self, payload: dict) -> IncomingMessage:
        # WhatsApp Business API envia el payload en un formato especifico de Meta.
        # Aqui lo normalizamos a IncomingMessage.
        try:
            entry = payload['entry'][0]
            change = entry['changes'][0]
            value = change['value']
            message = value['messages'][0]
            return IncomingMessage(
                from_number=message['from'],
                text=message.get('text', {}).get('body', ''),
                provider='whatsapp',
                message_id=message['id'],
            )
        except Exception as e:
            raise ValueError('Payload de WhatsApp invalido: ' + str(e))

    def send(self, msg: OutgoingMessage) -> bool:
        if not self.is_configured():
            raise RuntimeError('WhatsApp no configurado. Falta WHATSAPP_ACCESS_TOKEN o WHATSAPP_PHONE_NUMBER_ID.')
        url = f'https://graph.facebook.com/v18.0/{self.phone_number_id}/messages'
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'Content-Type': 'application/json',
        }
        body = {
            'messaging_product': 'whatsapp',
            'to': msg.to_number,
            'type': 'text',
            'text': {'body': msg.text},
        }
        try:
            r = httpx.post(url, headers=headers, json=body, timeout=15.0)
            return r.status_code == 200
        except Exception:
            return False
