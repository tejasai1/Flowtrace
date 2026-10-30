import json
from types import SimpleNamespace

from .base import ModelProvider


class FakeProvider(ModelProvider):
    """Returns prepared answers instead of calling a real model (for offline testing)."""

    def __init__(self, replies=None):
        self.replies = replies or {}  # repository name -> {"flows": [...]}
        self.calls = 0

    def complete(self, messages, tools=None, **kwargs):
        self.calls += 1
        first_line = messages[-1]["content"].splitlines()[0]
        repo = first_line.removeprefix("Repository name: ").strip()
        reply = self.replies.get(repo, {"flows": []})
        # Same shape as a real reply: an object with a .content string.
        return SimpleNamespace(content=json.dumps(reply))