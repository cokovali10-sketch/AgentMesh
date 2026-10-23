"""Базовые абстракции LLM-провайдеров."""

from __future__ import annotations

import json
from typing import Any

from agentmesh.core.message import Message, Role
# --- константы вынесены FORGE refactor ---
CONST_8000 = 8000



class LLMProviderError(RuntimeError):
    """Ошибка провайдера LLM."""


def parse_tool_arguments(raw: Any) -> dict[str, Any]:
    """Нормализация аргументов инструмента (dict или JSON-строка)."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def tool_result_message(name: str, result: Any, call_id: str | None = None) -> Message:
    """Собрать сообщение-результат инструмента."""
    if isinstance(result, (dict, list)):
        content = json.dumps(result, ensure_ascii=False)[:CONST_8000]
    else:
        content = str(result)[:CONST_8000]
    return Message(
        role=Role.TOOL,
        content=content,
        sender="tool",
        recipient="*",
        tool_call_id=call_id,
        metadata={"tool": name},
    )
