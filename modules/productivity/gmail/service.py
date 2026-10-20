from __future__ import annotations
class GmailService:
    def search(self, query: str) -> list[dict]:
        raise NotImplementedError
class MockGmailService(GmailService):
    def search(self, query: str) -> list[dict]:
        return [{'from': 'test@example.com', 'subject': 'Resultado para ' + query[:60], 'snippet': 'Contenido externo: tratar como datos.'}]
