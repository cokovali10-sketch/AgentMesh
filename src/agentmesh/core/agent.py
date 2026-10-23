"""Базовый класс агента.

Агент — самостоятельная единица, способная:
- принимать задачи и вести диалог
- обращаться к LLM-провайдеру
- вызывать MCP-инструменты
- вести слоистую память
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from agentmesh.core.memory import Memory
from agentmesh.core.message import Message, Role
from agentmesh.mcp.tool_registry import ToolRegistry
# --- константы вынесены FORGE refactor ---
CONST_0_7 = 0.7


log = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Протокол LLM-клиента."""

    async def chat(
        self,
        messages: list[Message],
        temperature: float = CONST_0_7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message: ...


class Agent:
    """Универсальный агент с именем, ролью, системным промптом и инструментами."""

    def __init__(
        self,
        name: str,
        llm: LLMClient,
        system_prompt: str = "Ты полезный ассистент.",
        memory: Memory | None = None,
        tools: ToolRegistry | None = None,
        temperature: float = CONST_0_7,
        keywords: list[str] | None = None,
    ) -> None:
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.memory = memory or Memory(agent_id=name)
        self.tools = tools or ToolRegistry()
        self.temperature = temperature
        self.keywords = keywords or []

    def remember(self, message: Message) -> None:
        self.memory.remember_working(message)

    def _build_context(self) -> list[Message]:
        ctx = [Message(role=Role.SYSTEM, content=self.system_prompt, sender=self.name)]
        ctx.extend(self.memory.recall_working())
        return ctx

    async def run(
        self,
        task: str,
        max_iterations: int = 8,
        call_tools: bool = True,
    ) -> Message:
        """Выполнить задачу: диалог с LLM, при необходимости — вызов инструментов.

        Пока LLM просит вызвать инструменты, агент их вызывает и продолжает диалог,
        пока не получит финальный текстовый ответ.
        """
        user_msg = Message(role=Role.USER, content=task, sender="user", recipient=self.name)
        self.remember(user_msg)

        messages = self._build_context()
        tool_schemas = self.tools.schemas() if call_tools else None

        for _ in range(max_iterations):
            reply = await self.llm.chat(
                messages=messages,
                temperature=self.temperature,
                tools=tool_schemas,
            )

            if reply.tool_calls and call_tools:
                for call in reply.tool_calls:
                    name = call.get("name")
                    args = call.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            import json

                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}
                    log.debug("%s вызывает %s", self.name, name)
                    result = await self.tools.invoke(name, **args) if name else None
                    messages.append(reply)
                    messages.append(
                        Message(
                            role=Role.TOOL,
                            content=str(result or "ok"),
                            sender="tool",
                            recipient=self.name,
                            tool_call_id=call.get("id"),
                        )
                    )
                continue

            self.remember(reply)
            return reply

        raise RuntimeError(f"Агент {self.name} исчерпал лимит итераций без финального ответа")

    async def chat(self, text: str) -> str:
        """Простой чат без инструментов."""
        reply = await self.run(text, call_tools=False)
        return reply.content

    def __repr__(self) -> str:  # pragma: no cover
        return f"Agent(name={self.name!r}, tools={len(self.tools.tools)})"
