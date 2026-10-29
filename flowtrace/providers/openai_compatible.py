import os

from openai import OpenAI

from .base import ModelProvider


class OpenAICompatibleProvider(ModelProvider):
    def __init__(self, base_url, api_key_env, model):
        key = os.environ.get(api_key_env)
        if not key:
            raise RuntimeError(f"Missing API key: set {api_key_env} in your .env file")
        self.client = OpenAI(base_url=base_url, api_key=key)
        self.model = model

    def list_models(self):
        """Return the model names this account can use."""
        return [m.id for m in self.client.models.list().data]

    def complete(self, messages, tools=None, **kwargs):
        params = {"model": self.model, "messages": messages, **kwargs}
        if tools:
            params["tools"] = tools
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message