from __future__ import annotations
import os
from core.llm.base import LLMProvider, LLMResponse

class GeminiProvider(LLMProvider):
    """Adapter Bifrost -> Gemini. Desacoplado: solo se activa con GOOGLE_API_KEY.
    Nunca recibe secretos ni tokens (sec. 17). Falla cerrado si no hay clave.
    """
    name: str = "gemini"

    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        self.model = model

    def complete(self, system: str, context: str, tools: list[dict]) -> LLMResponse:
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            return LLMResponse(text="Gemini no configurado: falta GOOGLE_API_KEY. Uso MockProvider.")
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            m = genai.GenerativeModel(self.model)
            # Solo system + contexto relevante, nunca memoria completa ni secretos
            r = m.generate_content(f"{system}\n\n{context}")
            return LLMResponse(text=r.text or "")
        except Exception as e:
            return LLMResponse(text=f"Gemini error (fail closed): {e}")
