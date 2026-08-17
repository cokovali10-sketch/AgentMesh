"""Типы сообщений и ролей в мультиагентной системе."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Role(str, Enum):
    """Роль отправителя/получателя сообщения."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    ORCHESTRATOR = "orchestrator"


class Message(BaseModel):
    """Единица обмена между агентами и внутри беседы."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    role: Role = Role.ASSISTANT
    content: str = ""
    sender: str = "unknown"
    recipient: str = "*"
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    tool_call_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

    def to_llm_dict(self) -> dict[str, str]:
        """Преобразование в формат, понятный LLM-провайдеру."""
        return {"role": self.role.value, "content": self.content}

    def short(self, limit: int = 120) -> str:
        """Короткое представление для логов."""
        body = self.content if len(self.content) <= limit else self.content[:limit] + "…"
        return f"[{self.sender}→{self.recipient}] {body}"

    def __str__(self) -> str:  # pragma: no cover
        return self.short()
