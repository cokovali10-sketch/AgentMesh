<div align="center">

# AgentMesh

**Multi-agent AI orchestration framework — planner, router, layered memory, MCP tools, and a web panel in one package.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![CI](https://img.shields.io/github/actions/workflow/status/yourname/AgentMesh/ci.yml?branch=main&label=CI)](https://github.com/yourname/AgentMesh/actions)
[![Tests](https://img.shields.io/badge/tests-30+-brightgreen.svg)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI version](https://img.shields.io/badge/PyPI-agentmesh-blue.svg?logo=pypi&logoColor=white)](https://pypi.org/project/agentmesh/)

**AgentMesh** solves the core problem of modern LLM applications: **coordinating multiple AI agents** to work together toward a complex goal — not just responding in isolation.

</div>

---

```
┌─────────────────────────────────────────────────────────────┐
│                       Orchestrator                         │
│   goal → Planner → Router → { agent₁, agent₂, agent₃ }    │
│                                │  memory │  MCP │  LLM      │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---|---|
| **Multi-Agent Orchestration** | A leader-coordinator breaks goals into subtasks, executes them in parallel (respecting dependencies), and assembles results |
| **Task Planner** | DAG of tasks with dependencies and priorities, automatic deadlock resolution |
| **Smart Router** | Assigns tasks to agents by keywords, explicit assignment, or least-load strategy |
| **Layered Memory** | Working / episodic / semantic memory with JSON persistence |
| **MCP Integration** | Connect any Model Context Protocol server (filesystem, browser, DB, HTTP) as agent tools |
| **Built-in Tools** | Safe file reading, web requests, arithmetic + bring your own Python functions |
| **Multi-Provider LLM** | OpenAI, Anthropic, and any OpenAI-compatible API (OpenRouter, local vLLM/Ollama) |
| **CLI + Web Panel** | Terminal interface via Typer/Rich + REST API and dashboard via FastAPI |

---

## Architecture

```
src/agentmesh/
├── core/                    # Framework core
│   ├── agent.py             # Universal agent with LLM + tools
│   ├── message.py           # Messages and roles
│   ├── memory.py            # Layered memory (working/episodic/semantic)
│   ├── planner.py           # Task graph with dependencies
│   ├── router.py            # Task-to-agent routing
│   └── orchestrator.py      # Coordinator: plan → execute
├── llm/                     # LLM providers
│   ├── providers.py         # OpenAI-compatible + Anthropic
│   └── registry.py          # Provider registry
├── mcp/                     # Model Context Protocol
│   ├── client.py            # stdio/HTTP client
│   └── tool_registry.py     # Unified tool registry
├── agents/                  # Pre-built agents
│   ├── factory.py           # researcher / coder / critic
│   └── tools.py             # Built-in tools
├── api/                     # Web panel (FastAPI + REST + WebSocket)
└── cli/                     # Terminal interface (Typer + Rich)
```

---

## Quick Start

```bash
# Install from source
pip install -e ".[dev]"

# Or install from PyPI
pip install agentmesh

# Set your LLM API key
export OPENAI_API_KEY="sk-..."
```

### Python API

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
    p = plan("Develop a product launch plan", [
        "Research the market",
        "Propose MVP features",
        "Assess risks",
    ])
    await orch.run(p)

    for task in p.tasks:
        print(f"[{task.agent}] {task.title} -> {task.status.value}")

asyncio.run(main())
```

### CLI

```bash
agentmesh run "Develop a product launch plan" \
  --steps "Research the market|Propose MVP features|Assess risks"

# Start the web panel
agentmesh web --port 8000
# Open http://127.0.0.1:8000
```

---

## MCP Tool Integration

```python
from agentmesh.mcp import MCPConnector
from agentmesh.mcp.tool_registry import ToolRegistry

registry = ToolRegistry()
connector = MCPConnector("filesystem")
await connector.connect_stdio(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])
tools = await connector.list_tools()
connector.attach(registry)  # MCP tools are now available to agents
```

---

## Configuration

| Environment Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (or OpenAI-compatible provider) |
| `ANTHROPIC_API_KEY` | Anthropic API key (for Claude models) |

### LLM Provider Options

```python
from agentmesh.llm.providers import OpenAICompatClient, AnthropicClient

# OpenAI / OpenRouter / local Ollama
llm = OpenAICompatClient(model="gpt-4o-mini")
llm = OpenAICompatClient(model="anthropic/claude-3-haiku", base_url="https://openrouter.ai/api/v1")

# Anthropic direct
llm = AnthropicClient(model="claude-sonnet-4-20250514")

# Local Ollama
llm = OpenAICompatClient(model="llama3", base_url="http://localhost:11434/v1")
```

---

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=agentmesh --cov-report=term-missing
```

The test suite covers: planner, memory, router, orchestrator (including parallelism and failure handling), agents, tools, and MCP registry.

---

## Project Structure

```
AgentMesh/
├── src/agentmesh/           # Main package
├── tests/                   # 30+ test files
│   ├── test_planner.py
│   ├── test_memory.py
│   ├── test_orchestrator.py
│   ├── test_agents.py
│   ├── test_tools.py
│   ├── test_message.py
│   ├── test_agent.py
│   ├── test_init.py
│   └── conftest.py
├── examples/
│   └── basic_run.py         # Demo with scripted LLM
├── pyproject.toml
├── .github/workflows/ci.yml
├── LICENSE
└── README.md
```

---

## Technologies

Python 3.10+ | Pydantic v2 | httpx | Typer | Rich | FastAPI | MCP SDK | pytest

---

## License

MIT — use freely for personal and commercial projects.
