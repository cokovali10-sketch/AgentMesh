"""Пример: мультиагентная оркестрация без реального API.

Использует фиктивного «LLM», который возвращает заранее заданные ответы,
поэтому запускается без ключей. Демонстрирует поток:
план → маршрутизация → параллельное исполнение → сборка результатов.
"""

import asyncio

from agentmesh.core.message import Message, Role
from agentmesh.core.orchestrator import Orchestrator
from agentmesh.core.router import Router
from agentmesh.core.planner import plan


class ScriptedLLM:
    """Фиктивный LLM: отвечает по шаблону имени агента."""

    def __init__(self, tag: str) -> None:
        self.tag = tag

    async def chat(self, messages, temperature=0.7, max_tokens=None, tools=None):
        last_user = next(
            (m.content for m in reversed(messages) if m.role == Role.USER),
            "задача",
        )
        return Message(role=Role.ASSISTANT, content=f"[{self.tag}] обработал: {last_user[:60]}", sender=self.tag)


async def main() -> None:
    router = Router()
    router.register(Agent("researcher", ScriptedLLM("researcher"), keywords=["найди"]))
    router.register(Agent("coder", ScriptedLLM("coder"), keywords=["код"]))
    router.register(Agent("critic", ScriptedLLM("critic"), keywords=["оцени"]))

    orch = Orchestrator(router)
    p = plan(
        "Выпустить продукт",
        ["найди рынок", "напиши код MVP", "оцени риски"],
    )
    await orch.run(p)

    print("Результаты:")
    for t in p.tasks:
        print(f"  [{t.agent}] {t.title} -> {t.status.value}")
    print(f"Загрузка: {orch.stats()['load']}")


from agentmesh.core.agent import Agent  # noqa: E402


if __name__ == "__main__":
    asyncio.run(main())