"""AgentMesh — мультиагентная оркестрация ИИ.

Мощный фреймворк для построения систем из нескольких ИИ-агентов:
планировщик задач, маршрутизация, слоистая память, MCP-инструменты,
провайдеры LLM и веб-панель управления.
"""

from agentmesh.core.agent import Agent
from agentmesh.core.message import Message, Role
from agentmesh.core.orchestrator import Orchestrator
from agentmesh.core.planner import Task, TaskStatus, plan

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "Message",
    "Orchestrator",
    "Role",
    "Task",
    "TaskStatus",
    "__version__",
    "plan",
]
