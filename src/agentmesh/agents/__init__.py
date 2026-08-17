"""Пакет агентов."""

from agentmesh.agents.factory import coder, critic, researcher
from agentmesh.agents.tools import register_builtins

__all__ = ["coder", "critic", "register_builtins", "researcher"]
