import pytest

from agentmesh.core.agent import Agent
from agentmesh.core.orchestrator import Orchestrator
from agentmesh.core.planner import TaskStatus, plan
from agentmesh.core.router import Router
from tests.fake_llm import FakeLLM, text_response


def _make_agent(name: str, keywords: list[str] | None = None) -> Agent:
    a = Agent(name=name, llm=FakeLLM([text_response(f"ответ от {name}")]))
    if keywords:
        a.keywords = keywords
    return a


@pytest.mark.asyncio
async def test_orchestrator_executes_plan():
    router = Router()
    router.register(_make_agent("researcher", ["найди"]))
    orch = Orchestrator(router)
    p = plan("задача", ["найди данные", "оцени"])
    await orch.run(p)
    assert all(t.status == TaskStatus.DONE for t in p.tasks)
    assert router.active.get("researcher", 0) >= 1


@pytest.mark.asyncio
async def test_orchestrator_parallel_tasks():
    router = Router()
    router.register(_make_agent("a"))
    orch = Orchestrator(router, max_concurrency=5)
    p = plan("x", ["1", "2", "3", "4"])
    await orch.run(p)
    assert len([t for t in p.tasks if t.status == TaskStatus.DONE]) == 4


@pytest.mark.asyncio
async def test_orchestrator_execute_helper():
    router = Router()
    router.register(_make_agent("a"))
    orch = Orchestrator(router)
    res = await orch.execute("цель", ["шаг"])
    assert res["success"] is True
    assert res["goal"] == "цель"


@pytest.mark.asyncio
async def test_orchestrator_failed_agent():
    class Boom:
        async def chat(self, *a, **k):
            raise RuntimeError("сбой")

    router = Router()
    router.register(Agent(name="bad", llm=Boom()))
    orch = Orchestrator(router)
    p = plan("цель", ["шаг"])
    await orch.run(p)
    assert p.tasks[0].status == TaskStatus.FAILED
    assert "сбой" in p.tasks[0].result["error"]


def test_router_preferred_agent():
    router = Router()
    router.register(_make_agent("a"))
    router.register(_make_agent("b"))
    chosen = router.route("задача", preferred="b")
    assert chosen.name == "b"


def test_router_keyword():
    router = Router()
    router.register(_make_agent("researcher", ["код"]))
    chosen = router.route("напиши код функции")
    assert chosen.name == "researcher"


def test_router_least_loaded():
    router = Router()
    router.register(_make_agent("a"))
    router.register(_make_agent("b"))
    router.route("задача1", preferred="a")
    chosen = router.route("задача2")
    assert chosen.name == "b"