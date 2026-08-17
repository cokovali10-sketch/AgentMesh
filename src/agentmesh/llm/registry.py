"""Реестр LLM-провайдеров и фабрики.

Позволяет описать провайдеров в конфиге (JSON/в коде) и получать
готовые клиенты по имени.
"""

from __future__ import annotations

import os

from agentmesh.llm.providers import AnthropicClient, OpenAICompatClient


class LLMRegistry:
    """Реестр клиентов по имени."""

    def __init__(self) -> None:
        self._clients: dict[str, object] = {}

    def register(self, name: str, client: object) -> None:
        self._clients[name] = client

    def get(self, name: str) -> object:
        if name not in self._clients:
            raise KeyError(f"Провайдер {name!r} не зарегистрирован. Доступно: {list(self._clients)}")
        return self._clients[name]

    def names(self) -> list[str]:
        return list(self._clients)


def build_default_registry() -> LLMRegistry:
    """Реестр из переменных окружения: OPENAI_API_KEY, ANTHROPIC_API_KEY."""
    reg = LLMRegistry()
    if os.getenv("OPENAI_API_KEY"):
        reg.register("openai", OpenAICompatClient(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")))
    if os.getenv("ANTHROPIC_API_KEY"):
        reg.register("anthropic", AnthropicClient(model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")))
    return reg


__all__ = ["AnthropicClient", "LLMRegistry", "OpenAICompatClient", "build_default_registry"]
