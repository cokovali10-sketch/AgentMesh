import pytest

from agentmesh.agents.factory import coder, critic, researcher
from agentmesh.mcp.tool_registry import ToolRegistry
from tests.fake_llm import FakeLLM


def test_researcher_has_keywords():
    a = researcher(FakeLLM())
    assert "найди" in a.keywords


def test_coder_has_keywords():
    a = coder(FakeLLM())
    assert "код" in a.keywords


def test_critic_has_keywords():
    a = critic(FakeLLM())
    assert "риск" in a.keywords


def test_builtin_tools_register():
    reg = ToolRegistry()
    from agentmesh.agents.tools import register_builtins

    register_builtins(reg)
    names = reg.names()
    assert "read_file" in names
    assert "calculate" in names
    assert "http_get" in names


@pytest.mark.asyncio
async def test_calculate_tool():
    reg = ToolRegistry()
    from agentmesh.agents.tools import register_builtins

    register_builtins(reg)
    result = await reg.invoke("calculate", expression="2+2*2")
    assert "6" in result


@pytest.mark.asyncio
async def test_http_get_tool():
    reg = ToolRegistry()
    from agentmesh.agents import tools as tools_mod

    # проверяем, что инструмент зарегистрирован и его можно вызвать (выполнится реальный GET к example.com — разрешённый)
    register_builtins = tools_mod.register_builtins
    register_builtins(reg)
    assert "http_get" in reg.names()
    result = await reg.invoke("http_get", url="https://example.com", timeout=5.0)
    assert "Example Domain" in result or "example" in result.lower()