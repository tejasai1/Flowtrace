from abc import ABC, abstractmethod


class ModelProvider(ABC):
    """Every model provider (Meta, Groq, Ollama, ...) must implement this."""

    @abstractmethod
    def complete(self, messages, tools=None, **kwargs):
        """Send messages to the model and return its reply."""