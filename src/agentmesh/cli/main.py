"""CLI-интерфейс AgentMesh."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentmesh.agents.factory import coder, critic, researcher
from agentmesh.core.orchestrator import Orchestrator
from agentmesh.core.planner import plan
from agentmesh.core.router import Router
from agentmesh.llm.providers import OpenAICompatClient
from agentmesh.llm.registry import build_default_registry

app = typer.Typer(help="AgentMesh — мультиагентная оркестрация ИИ.", no_args_is_help=True)
console = Console()


def _require_client() -> OpenAICompatClient:
    reg = build_default_registry()
    if not reg.names():
        console.print(
            "[red]Нет ключей API.[/red] Установите OPENAI_API_KEY или ANTHROPIC_API_KEY, "
            "либо передайте --api-key/--base-url."
        )
        raise typer.Exit(1)
    client = reg.get(reg.names()[0])
    if not isinstance(client, OpenAICompatClient):
        from agentmesh.llm.providers import AnthropicClient

        if isinstance(client, AnthropicClient):
            console.print("[yellow]Anthropic-клиент в CLI пока поддерживается через --model openai-совместимости.[/yellow]")
    return client


@app.command()
def run(
    task: str = typer.Argument(..., help="Цель для оркестратора"),
    steps: str = typer.Option("", help="Шаги через '|' (план). Пусто = один шаг."),
    agent: str = typer.Option("any", help="Предпочитаемый агент"),
    api_key: str | None = typer.Option(None, "--api-key", help="OPENAI-совместимый ключ"),
    base_url: str = typer.Option("https://api.openai.com/v1", "--base-url"),
    model: str = typer.Option("gpt-4o-mini", "--model"),
) -> None:
    """Запустить оркестрацию цели с пулом агентов."""

    def _make_llm():
        if api_key or base_url != "https://api.openai.com/v1":
            return OpenAICompatClient(api_key=api_key, base_url=base_url, model=model)
        return _require_client()

    llm = _make_llm()

    router = Router()
    router.register(researcher(llm))
    router.register(coder(llm))
    router.register(critic(llm))
    orch = Orchestrator(router)

    step_list = [s.strip() for s in steps.split("|") if s.strip()] or [task]
    p = plan(task, step_list, agent_for_step=lambda i: agent if agent != "any" else None)

    console.print(Panel.fit(f"[bold cyan]{task}[/]", title="AgentMesh"))

    async def _go():
        await orch.run(p)

    asyncio.run(_go())

    table = Table(title="Результаты задач")
    table.add_column("Агент")
    table.add_column("Задача")
    table.add_column("Статус")
    for t in p.tasks:
        table.add_row(t.agent, t.title, t.status.value)
    console.print(table)
    for t in p.tasks:
        if t.status.value == "done":
            console.print(Panel(t.result[:500], title=f"[green]{t.title}[/]", border_style="green"))
    console.print(f"\n[bold]Загрузка агентов:[/bold] {orch.stats()['load']}")


@app.command()
def agents() -> None:
    """Показать информацию о пуле агентов."""
    table = Table(title="Агенты AgentMesh")
    table.add_column("Имя")
    table.add_column("Роль")
    table.add_row("researcher", "Исследование, поиск, факты")
    table.add_row("coder", "Код, файлы, ревью")
    table.add_row("critic", "Оценка, риски, улучшения")
    console.print(table)


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
) -> None:
    """Запустить веб-панель управления (требуется agentmesh[web])."""
    try:
        import uvicorn
    except ImportError:
        console.print("[red]Нужен пакет web: pip install agentmesh[web][/red]")
        raise typer.Exit(1)
    from agentmesh.api.server import create_app

    uvicorn.run(create_app(), host=host, port=port)


def main() -> None:  # pragma: no cover
    app()