"""Встроенные инструменты агентов.

Безопасные, изолированные инструменты для типовых задач:
чтение файлов, веб-запросы, поиск в тексте, вычисления.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from agentmesh.mcp.tool_registry import ToolRegistry


def register_builtins(registry: ToolRegistry, workspace: str = ".") -> None:
    """Зарегистрировать безопасные встроенные инструменты."""

    def read_file(path: str) -> str:
        p = Path(path)
        if not p.is_file():
            return f"Файл не найден: {path}"
        text = p.read_text(encoding="utf-8", errors="replace")
        return text[:20000]

    def list_files(path: str = ".") -> str:
        p = Path(path)
        if not p.is_dir():
            return f"Папка не найдена: {path}"
        entries = []
        for child in sorted(p.iterdir()):
            kind = "DIR" if child.is_dir() else "FILE"
            entries.append(f"{kind} {child.name}")
        return "\n".join(entries[:200])

    def search_text(pattern: str, text: str) -> str:
        try:
            matches = re.findall(rf"(?i){pattern}", text)
        except re.error as exc:
            return f"Некорректный regex: {exc}"
        return json.dumps(matches[:50], ensure_ascii=False)

    def calculate(expression: str) -> str:
        safe = re.sub(r"[^0-9+\-*/().\s]", "", expression)
        if not safe:
            return "Пустое выражение"
        try:
            return str(eval(safe, {"__builtins__": {}}, {}))
        except Exception as exc:  # noqa: BLE001
            return f"Ошибка: {exc}"

    async def http_get(url: str, timeout: float = 10.0) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            return resp.text[:20000]

    registry.register(
        "read_file",
        read_file,
        "Читает содержимое текстового файла",
        {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    )
    registry.register(
        "list_files",
        list_files,
        "Список файлов в папке",
        {"type": "object", "properties": {"path": {"type": "string"}}},
    )
    registry.register(
        "search_text",
        search_text,
        "Ищет regex в тексте",
        {
            "type": "object",
            "properties": {"pattern": {"type": "string"}, "text": {"type": "string"}},
            "required": ["pattern", "text"],
        },
    )
    registry.register(
        "calculate",
        calculate,
        "Вычисляет арифметическое выражение",
        {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
    )
    registry.register(
        "http_get",
        http_get,
        "Выполняет HTTP GET-запрос и возвращает текст ответа",
        {"type": "object", "properties": {"url": {"type": "string"}, "timeout": {"type": "number"}}, "required": ["url"]},
    )
