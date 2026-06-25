"""LLM provider interface."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Send prompt to LLM, return generated text."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier for logging."""
        pass