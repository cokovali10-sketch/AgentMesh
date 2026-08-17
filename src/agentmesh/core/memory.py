"""Слоистая память агента.

Реализует три классических слоя памяти:
- Working (рабочая): контекст текущей задачи
- Episodic (эпизодическая): история выполненных задач и решений
- Semantic (семантическая): факты и знания, извлечённые из опыта

Всё хранится в памяти по умолчанию и может быть персистентно
сохранено через встраиваемые хранилища (JSON/SQLite).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentmesh.core.message import Message


@dataclass
class Memory:
    """Слоистая память агента."""

    agent_id: str = "agent"
    working: list[Message] = field(default_factory=list)
    episodic: list[dict[str, Any]] = field(default_factory=list)
    semantic: dict[str, Any] = field(default_factory=dict)
    max_working: int = 20
    max_episodic: int = 200

    def remember_working(self, message: Message) -> None:
        """Добавить сообщение в рабочую память (контекст)."""
        self.working.append(message)
        if len(self.working) > self.max_working:
            self.working = self.working[-self.max_working :]

    def recall_working(self, limit: int | None = None) -> list[Message]:
        """Вернуть рабочую память."""
        if limit is None:
            return list(self.working)
        return self.working[-limit:]

    def store_episode(
        self,
        task: str,
        result: str,
        outcome: str = "success",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Записать завершённую задачу в эпизодическую память."""
        self.episodic.append(
            {
                "task": task,
                "result": result,
                "outcome": outcome,
                "ts": time.time(),
                "metadata": metadata or {},
            }
        )
        if len(self.episodic) > self.max_episodic:
            self.episodic = self.episodic[-self.max_episodic :]

    def recall_episodes(self, task: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
        """Найти похожие прошлые задачи (простое ключевое соответствие)."""
        if not task:
            return list(self.episodic[-limit:])
        keywords = {w.lower() for w in task.split() if len(w) > 3}
        scored = []
        for ep in self.episodic:
            hay = f"{ep['task']} {ep['result']}".lower()
            score = sum(1 for kw in keywords if kw in hay)
            if score:
                scored.append((score, ep))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:limit]]

    def store_fact(self, key: str, value: Any) -> None:
        """Сохранить факт в семантическую память."""
        self.semantic[key] = value

    def get_fact(self, key: str, default: Any = None) -> Any:
        return self.semantic.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "working": [m.model_dump() for m in self.working],
            "episodic": self.episodic,
            "semantic": self.semantic,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Memory:
        mem = cls(agent_id=data.get("agent_id", "agent"))
        mem.working = [Message(**m) for m in data.get("working", [])]
        mem.episodic = data.get("episodic", [])
        mem.semantic = data.get("semantic", {})
        return mem

    def save(self, path: str | Path) -> None:
        """Сохранить память в JSON-файл."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> Memory:
        p = Path(path)
        if p.exists():
            self.__dict__.update(self.from_dict(json.loads(p.read_text(encoding="utf-8"))).__dict__)
        return self
