"""Реестр инструментов агентов.

Внутренние инструменты (Python-функции) и внешние MCP-инструменты
объединяются в единый реестр, отдающий LLM JSON-схемы и умеющий
вызывать инструменты по имени.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

ToolFunc = Callable[..., Any] | Callable[..., Awaitable[Any]]


class ToolRegistry:
    """Реестр инструментов: внутренних (callables) и внешних (MCP)."""

    def __init__(self) -> None:
        self.tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        fn: ToolFunc,
        description: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """Зарегистрировать Python-функцию как инструмент."""
        if not description:
            description = inspect.getdoc(fn) or f"Инструмент {name}"
        schema = parameters or {
            "type": "object",
            "properties": {},
        }
        self.tools[name] = {
            "type": "function",
            "name": name,
            "description": description,
            "input_schema": schema,
            "_fn": fn,
            "_external": False,
        }

    def register_mcp(self, name: str, description: str, input_schema: dict[str, Any], caller: ToolFunc) -> None:
        """Зарегистрировать внешний MCP-инструмент."""
        self.tools[name] = {
            "type": "function",
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "_fn": caller,
            "_external": True,
        }

    def schemas(self) -> list[dict[str, Any]]:
        """Схемы инструментов для LLM (без внутренних полей)."""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"],
            }
            for t in self.tools.values()
        ]

    async def invoke(self, name: str, **kwargs: Any) -> Any:
        """Вызвать инструмент по имени."""
        if name not in self.tools:
            raise KeyError(f"Инструмент {name!r} не найден")
        entry = self.tools[name]
        fn = entry["_fn"]
        result = fn(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    def names(self) -> list[str]:
        return list(self.tools.keys())

    def __len__(self) -> int:
        return len(self.tools)
