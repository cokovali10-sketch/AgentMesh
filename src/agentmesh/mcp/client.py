"""MCP-клиент для подключения внешних инструментов.

Позволяет агентам вызывать любые серверы Model Context Protocol
(стандарт Anthropic/OpenAI) — файловые системы, браузеры, базы данных,
HTTP-запросы и т.д. — как собственные инструменты.

Реализация опциональна: если пакет `mcp` не установлен, агенты
работают только со встроенными инструментами.
"""

from __future__ import annotations

import importlib.util
import logging
from typing import Any

from agentmesh.mcp.tool_registry import ToolRegistry

log = logging.getLogger(__name__)

_HAS_MCP = importlib.util.find_spec("mcp") is not None


class MCPError(RuntimeError):
    """Ошибка MCP-подключения."""


class MCPConnector:
    """Подключает MCP-сервер и регистрирует его инструменты в реестре."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._session = None
        self._tools: list[dict[str, Any]] = []

    @property
    def connected(self) -> bool:
        return self._session is not None

    async def connect_stdio(self, command: list[str], env: dict[str, str] | None = None) -> list[dict[str, Any]]:
        """Подключение к MCP-серверу через stdio (python -m server, node server.js...)."""
        if not _HAS_MCP:
            raise MCPError("Пакет 'mcp' не установлен. Выполните: pip install agentmesh[mcp]")

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(command=command[0], args=command[1:], env=env)
        self._read, self._write = await stdio_client(params).__aenter__()
        self._session = await ClientSession(self._read, self._write).__aenter__()
        await self._session.initialize()
        return await self.list_tools()

    async def connect_http(self, url: str, headers: dict[str, str] | None = None) -> list[dict[str, Any]]:
        """Подключение к MCP-серверу через HTTP/SSE."""
        if not _HAS_MCP:
            raise MCPError("Пакет 'mcp' не установлен. Выполните: pip install agentmesh[mcp]")

        from mcp import ClientSession
        from mcp.client.sse import sse_client

        self._read, self._write = await sse_client(url, headers=headers).__aenter__()
        self._session = await ClientSession(self._read, self._write).__aenter__()
        await self._session.initialize()
        return await self.list_tools()

    async def list_tools(self) -> list[dict[str, Any]]:
        if not self._session:
            raise MCPError("Сессия MCP не инициализирована")
        result = await self._session.list_tools()
        self._tools = [
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema or {"type": "object", "properties": {}},
            }
            for t in result.tools
        ]
        return self._tools

    def attach(self, registry: ToolRegistry) -> None:
        """Зарегистрировать все инструменты сервера в реестре агента."""
        if not self._session:
            raise MCPError("Сессия MCP не инициализирована")

        async def _call(name: str, **kwargs: Any) -> Any:
            result = await self._session.call_tool(name, kwargs)
            parts = [r.text for r in result.content if getattr(r, "type", None) == "text"]
            return "\n".join(parts) or str(result)

        for t in self._tools:
            registry.register_mcp(t["name"], t["description"], t["input_schema"], _call)
            log.info("MCP-инструмент подключён: %s.%s", self.name, t["name"])

    async def close(self) -> None:
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None
        if hasattr(self, "_write"):
            await self._write.__aexit__(None, None, None)


__all__ = ["MCPConnector", "MCPError"]
