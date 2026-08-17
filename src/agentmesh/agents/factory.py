"""Пул готовых агентов: исследователь, код-ревьюер, критик.

Заводские функции создают агентов с профильными системными промптами
и ключевыми словами для маршрутизации.
"""

from __future__ import annotations

from agentmesh.core.agent import Agent
from agentmesh.core.memory import Memory


def researcher(llm, name: str = "researcher", memory: Memory | None = None) -> Agent:
    """Агент-исследователь: сбор фактов, поиск, анализ источников."""
    return Agent(
        name=name,
        llm=llm,
        system_prompt=(
            "Ты — исследователь. Собирай факты, анализируй источники, "
            "давай структурированные ответы с выводами и ссылками. "
            "Используй инструменты для получения данных."
        ),
        memory=memory,
        keywords=["найди", "исследуй", "поиск", "факт", "источник", "данные", "research", "find"],
    )


def coder(llm, name: str = "coder", memory: Memory | None = None) -> Agent:
    """Агент-разработчик: написание и анализ кода, ревью."""
    return Agent(
        name=name,
        llm=llm,
        system_prompt=(
            "Ты — разработчик. Пиши чистый, документированный код, "
            "объясняй решения, находи и исправляй ошибки. "
            "Используй инструменты для чтения файлов и анализа."
        ),
        memory=memory,
        keywords=["код", "программа", "файл", "скрипт", "bug", "ошибка", "code", "python", "функция"],
    )


def critic(llm, name: str = "critic", memory: Memory | None = None) -> Agent:
    """Агент-критик: выявляет слабые места, риски и противоречия."""
    return Agent(
        name=name,
        llm=llm,
        system_prompt=(
            "Ты — критик. Анализируй решения критически: находи слабые места, "
            "риски, упущенные детали и противоречия. Будь конструктивен."
        ),
        memory=memory,
        keywords=["критик", "оцени", "проверь", "риск", "слабые", "review", "улучши"],
    )


def register_builtins_tools(agent: Agent) -> None:
    """Подмешать встроенные инструменты агенту (если у него ещё нет)."""
    from agentmesh.agents.tools import register_builtins

    if not agent.tools.names():
        register_builtins(agent.tools)
