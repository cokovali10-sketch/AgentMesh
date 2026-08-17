"""Фиктивный LLM-клиент для тестов: возвращает заранее заданные ответы."""

from __future__ import annotations

from typing import Any

from agentmesh.core.message import Message, Role


class FakeLLM:
    """Имитация LLM. По очереди возвращает заданные ответы."""

    def __init__(self, responses: list[Message] | None = None) -> None:
        self.responses: list[Message] = responses or []
        self.calls: int = 0
        self.history: list[list[Message]] = []

    async def chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message:
        self.calls += 1
        self.history.append(list(messages))
        if self.calls <= len(self.responses):
            return self.responses[self.calls - 1]
        return Message(role=Role.ASSISTANT, content="(пустой ответ теста)", sender="fake")


def text_response(content: str) -> Message:
    return Message(role=Role.ASSISTANT, content=content, sender="fake")


def tool_response(tool_name: str, call_id: str = "call_1") -> Message:
    return Message(
        role=Role.ASSISTANT,
        content="",
        sender="fake",
        tool_calls=[{"id": call_id, "name": tool_name, "arguments": {}}],
    )