"""Маршрутизатор задач.

Выбирает, какой агент из пула возьмёт задачу, на основе:
- явного указания агента в задаче
- ключевых слов в заголовке задачи
- загрузки агентов (числа активных задач)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agentmesh.core.agent import Agent


@dataclass
class Router:
    """Маршрутизатор задач по агентам."""

    pool: dict[str, Agent] = field(default_factory=dict)
    active: dict[str, int] = field(default_factory=dict)  # агент -> число задач

    def register(self, agent: Agent) -> None:
        self.pool[agent.name] = agent
        self.active.setdefault(agent.name, 0)

    def route(self, task_title: str, preferred: str | None = None) -> Agent | None:
        """Выбрать агента под задачу."""
        if not self.pool:
            return None
        if preferred and preferred in self.pool:
            self.active[preferred] = self.active.get(preferred, 0) + 1
            return self.pool[preferred]

        title_l = task_title.lower()
        for name, agent in self.pool.items():
            keywords = getattr(agent, "keywords", [])
            if any(kw in title_l for kw in keywords):
                self.active[name] = self.active.get(name, 0) + 1
                return agent

        least_loaded = min(self.pool, key=lambda n: self.active.get(n, 0))
        self.active[least_loaded] = self.active.get(least_loaded, 0) + 1
        return self.pool[least_loaded]

    def stats(self) -> dict[str, int]:
        return dict(self.active)
