from __future__ import annotations
import httpx
from core.messaging.base import MessagingProvider, IncomingMessage, OutgoingMessage

class TelegramProvider(MessagingProvider):
    """Adapter real a Telegram Bot API.
    Solo necesita TELEGRAM_BOT_TOKEN. Falla cerrado si no hay token.
    Tu numero de telefono no se expone.
    """

    name: str = "telegram"

    def __init__(self, token: str = "") -> None:
        self.token = token
        self.base_url = "https://api.telegram.org/bot" + self.token if self.token else ""

    def is_configured(self) -> bool:
        return bool(self.token)

    def receive(self, payload: dict) -> IncomingMessage:
        msg = payload.get("message", {})
        chat = msg.get("chat", {})
        return IncomingMessage(
            from_number=str(chat.get("id", "")),
            text=msg.get("text", ""),
            provider="telegram",
            message_id=str(msg.get("message_id", "")),
        )

    def send(self, msg: OutgoingMessage) -> bool:
        if not self.is_configured():
            raise RuntimeError("Telegram no configurado. Falta TELEGRAM_BOT_TOKEN.")
        url = self.base_url + "/sendMessage"
        body = {"chat_id": msg.to_number, "text": msg.text}
        try:
            r = httpx.post(url, json=body, timeout=15.0)
            return r.status_code == 200
        except Exception:
            return False

    def set_webhook(self, url: str) -> bool:
        if not self.is_configured():
            return False
        try:
            r = httpx.post(self.base_url + "/setWebhook", json={"url": url}, timeout=15.0)
            return r.status_code == 200
        except Exception:
            return False
