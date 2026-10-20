from __future__ import annotations
from modules.productivity.gmail.service import GmailService
from infrastructure.google.oauth import NeedsGoogleAuth
class GmailAdapter(GmailService):
    def search(self, query: str) -> list[dict]:
        raise NeedsGoogleAuth('Gmail no conectado. Se requiere OAuth con scope gmail.readonly.')
