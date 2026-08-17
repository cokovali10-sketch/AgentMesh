"""Планировщик задач.

Разбивает сложную задачу на граф подзадач с зависимостями,
оценивает приоритеты и выдаёт исполнимый план.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Task(BaseModel):
    """Отдельная подзадача в плане."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str
    description: str = ""
    agent: str = "any"
    depends_on: list[str] = Field(default_factory=list)
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def ready(self, done_ids: set[str]) -> bool:
        return all(d in done_ids for d in self.depends_on)


@dataclass
class Plan:
    """Исполнимый план из задач."""

    goal: str
    tasks: list[Task] = field(default_factory=list)

    def add(self, task: Task) -> None:
        self.tasks.append(task)

    def by_id(self, task_id: str) -> Task | None:
        return next((t for t in self.tasks if t.id == task_id), None)

    def next_ready(self, done_ids: set[str]) -> list[Task]:
        return [
            t
            for t in self.tasks
            if t.status == TaskStatus.PENDING and t.ready(done_ids)
        ]

    def estimate(self) -> int:
        return len(self.tasks)

    def to_dict(self) -> dict[str, Any]:
        return {"goal": self.goal, "tasks": [t.model_dump() for t in self.tasks]}


def plan(
    goal: str,
    steps: list[str],
    agent_for_step: Callable[[int], str] | None = None,
) -> Plan:
    """Создать линейный план из списка шагов.

    При желании можно задать функцию, сопоставляющую индекс шага с агентом.
    """
    p = Plan(goal=goal)
    prev_id: str | None = None
    for i, step in enumerate(steps):
        t = Task(
            title=step,
            agent=agent_for_step(i) if agent_for_step else "any",
            depends_on=[prev_id] if prev_id else [],
        )
        p.add(t)
        prev_id = t.id
    return p
