"""Оркестратор.

Высокоуровневый координатор: принимает цель, планирует, маршрутизирует,
исполняет подзадачи (параллельно, если есть зависимости), собирает итог
и складывает результат в эпизодическую память.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from agentmesh.core.agent import Agent
from agentmesh.core.memory import Memory
from agentmesh.core.planner import Plan, Task, TaskStatus
from agentmesh.core.router import Router

log = logging.getLogger(__name__)


class Orchestrator:
    """Оркестратор мультиагентного выполнения."""

    def __init__(
        self,
        router: Router,
        memory: Memory | None = None,
        max_concurrency: int = 3,
    ) -> None:
        self.router = router
        self.memory = memory or Memory(agent_id="orchestrator")
        self.max_concurrency = max_concurrency

    def register(self, agent: Agent) -> None:
        self.router.register(agent)

    @property
    def agents(self) -> dict[str, Agent]:
        return self.router.pool

    async def run(self, plan: Plan) -> Plan:
        """Исполнить план: задачи без зависимостей — параллельно, с учётом очереди."""
        done: set[str] = set()
        sem = asyncio.Semaphore(self.max_concurrency)

        while len(done) < len(plan.tasks):
            ready = plan.next_ready(done)
            if not ready:
                raise RuntimeError("Дедлок в плане: задачи с неразрешёнными зависимостями")

            async def _exec(task: Task, _sem: asyncio.Semaphore) -> None:
                async with _sem:
                    task.status = TaskStatus.RUNNING
                    agent = self.router.route(task.title, task.agent)
                    try:
                        if agent is None:
                            task.result = {"error": "нет агентов в пуле"}
                            task.status = TaskStatus.FAILED
                            return
                        log.info("→ %s выполняет %s", agent.name, task.title)
                        reply = await agent.run(task.description or task.title)
                        task.result = reply.content
                        task.status = TaskStatus.DONE
                        agent.memory.store_episode(task.title, reply.content)
                        self.memory.store_episode(task.title, reply.content)
                    except Exception as exc:
                        log.exception("Задача %s упала", task.id)
                        task.result = {"error": str(exc)}
                        task.status = TaskStatus.FAILED

            await asyncio.gather(*(_exec(t, sem) for t in ready))
            done.update(t.id for t in ready)

        return plan

    async def execute(self, goal: str, steps: list[str]) -> dict[str, Any]:
        """Удобный однострочный запуск: план из шагов -> исполнение."""
        from agentmesh.core.planner import plan as build_plan

        p = build_plan(goal, steps)
        await self.run(p)
        return {
            "goal": goal,
            "tasks": [t.model_dump() for t in p.tasks],
            "success": all(t.status == TaskStatus.DONE for t in p.tasks),
        }

    def stats(self) -> dict[str, Any]:
        return {
            "agents": list(self.agents.keys()),
            "load": self.router.stats(),
        }
