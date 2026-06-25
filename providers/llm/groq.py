"""Groq LLM provider."""

from groq import Groq
from providers.llm.base import LLMProvider
import config


class GroqLLM(LLMProvider):
    
    MODEL = "llama-3.3-70b-versatile"
    
    def __init__(self):
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in .env")
        self.client = Groq(api_key=config.GROQ_API_KEY)
    
    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    @property
    def model_name(self) -> str:
        return self.MODEL
    