# ⚡ AgentMesh

> **Мультиагентная оркестрация ИИ**: планировщик, маршрутизатор, слоистая память, MCP-инструменты и веб-панель — в одном фреймворке.

AgentMesh — мощный Python-фреймворк для построения систем из нескольких ИИ-агентов. Он решает главную проблему современных LLM-приложений: **как скоординировать несколько агентов**, чтобы они вместе выполняли сложную цель, а не отвечали в одиночку.

```
┌─────────────────────────────────────────────────────────────┐
│                       Orchestrator                         │
│   цель → Planner → Router → { agent₁, agent₂, agent₃ }    │
│                                │  память │  MCP │  LLM      │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Возможности

- **🧠 Мультиагентная оркестрация** — лидер-координатор разбивает цель на подзадачи, исполняет их (параллельно, с учётом зависимостей) и собирает итог.
- **🗺️ Планировщик** — граф задач с зависимостями и приоритетами, автоматическое разрешение дедлоков.
- **🧭 Маршрутизатор** — выбирает агента под задачу по ключевым словам, явному указанию или наименьшей загрузке.
- **💾 Слоистая память** — рабочая / эпизодическая / семантическая память с персистентностью в JSON.
- **🔌 MCP-интеграция** — подключайте любые серверы Model Context Protocol (файлы, браузер, БД, HTTP) как инструменты агентов.
- **🔧 Инструменты** — встроенные безопасные инструменты (чтение файлов, веб-запросы, вычисления) + собственные Python-функции.
- **🌐 Мультипровайдер** — OpenAI, Anthropic и любые OpenAI-совместимые API (OpenRouter, локальные vLLM/Ollama).
- **🖥️ CLI + веб-панель** — управление из терминала и через REST API / веб-интерфейс.
- **✅ 30+ тестов** — покрытие core, памяти, агентов, оркестрации и инструментов.

---

## 🚀 Быстрый старт

```bash
pip install -e ".[dev]"
export OPENAI_API_KEY="sk-..."
```

### Оркестрация из кода

```python
import asyncio
from agentmesh import Orchestrator, plan
from agentmesh.agents.factory import researcher, coder, critic
from agentmesh.core.router import Router
from agentmesh.llm.providers import OpenAICompatClient

async def main():
    llm = OpenAICompatClient(model="gpt-4o-mini")

    router = Router()
    router.register(researcher(llm))
    router.register(coder(llm))
    router.register(critic(llm))

    orch = Orchestrator(router)
    p = plan("Разработать план запуска продукта", [
        "Исследовать рынок",
        "Предложить MVP-функции",
        "Оценить риски",
    ])
    await orch.run(p)

    for task in p.tasks:
        print(f"[{task.agent}] {task.title} → {task.status.value}")

asyncio.run(main())
```

### Оркестрация из CLI

```bash
export OPENAI_API_KEY="sk-..."
agentmesh run "Разработать план запуска продукта" \
  --steps "Исследовать рынок|Предложить MVP-функции|Оценить риски"
```

### Веб-панель

```bash
pip install "agentmesh[web]"
agentmesh web --port 8000
# откройте http://127.0.0.1:8000
```

---

## 🧩 Подключение MCP-сервера

```python
from agentmesh.mcp import MCPConnector
from agentmesh.mcp.tool_registry import ToolRegistry

registry = ToolRegistry()
connector = MCPConnector("filesystem")
await connector.connect_stdio(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])
tools = await connector.list_tools()
connector.attach(registry)  # инструменты MCP стали доступны агентам
```

---

## 📦 Архитектура

```
src/agentmesh/
├── core/            # ядро
│   ├── agent.py        # универсальный агент с LLM+инструментами
│   ├── message.py      # сообщения и роли
│   ├── memory.py       # слоистая память (working/episodic/semantic)
│   ├── planner.py      # граф задач с зависимостями
│   ├── router.py       # маршрутизация задач по агентам
│   └── orchestrator.py # координатор: план → исполнение
├── llm/             # провайдеры LLM
│   ├── providers.py    # OpenAI-совместимый + Anthropic
│   └── registry.py     # реестр провайдеров
├── mcp/             # Model Context Protocol
│   ├── client.py       # клиент stdio/HTTP
│   └── tool_registry.py# единый реестр инструментов
├── agents/          # готовые агенты
│   ├── factory.py      # researcher / coder / critic
│   └── tools.py        # встроенные инструменты
├── api/             # веб-панель (FastAPI + REST + WS)
└── cli/             # терминальный интерфейс (Typer + Rich)
```

---

## 🧪 Тесты

```bash
pytest -v
```

Покрывают: планировщик, память, маршрутизатор, оркестрацию (включая параллельность и сбои), агентов, инструменты и MCP-реестр.

---

## 🛠️ Технологии

Python 3.10+ · Pydantic v2 · httpx · Typer · Rich · FastAPI · MCP SDK · pytest

---

## 📄 Лицензия

MIT — используйте свободно в учебных и коммерческих целях.