import pytest

from agentmesh.core.agent import Agent
from agentmesh.mcp.tool_registry import ToolRegistry
from tests.fake_llm import FakeLLM, text_response, tool_response


@pytest.mark.asyncio
async def test_agent_plain_chat():
    llm = FakeLLM([text_response("ответ агента")])
    a = Agent(name="t", llm=llm, system_prompt="система")
    result = await a.run("вопрос")
    assert result.content == "ответ агента"
    assert a.memory.recall_working()[0].content == "вопрос"


@pytest.mark.asyncio
async def test_agent_with_tool_loop():
    def echo(**kw):
        return {"got": kw}

    reg = ToolRegistry()
    reg.register("echo", echo, "вернёт аргументы", {"type": "object", "properties": {"x": {"type": "string"}}})

    llm = FakeLLM(
        [
            tool_response("echo", "call_1"),
            text_response("финал"),
        ]
    )
    a = Agent(name="t", llm=llm, tools=reg)
    result = await a.run("вызови echo")
    assert result.content == "финал"
    assert llm.calls == 2


@pytest.mark.asyncio
async def test_agent_tool_arguments_parsed():
    def echo(**kw):
        return {"got": kw}

    reg = ToolRegistry()
    reg.register("echo", echo, "вернёт аргументы", {"type": "object", "properties": {"x": {"type": "string"}}})

    msg = tool_response("echo", "call_1")
    msg.tool_calls = [{"id": "call_1", "name": "echo", "arguments": '{"x":"hello"}'}]
    llm = FakeLLM([msg, text_response("ok")])
    a = Agent(name="t", llm=llm, tools=reg)
    await a.run("вызови")
    assert llm.history[0][0].role.value == "system"


@pytest.mark.asyncio
async def test_agent_max_iterations():
    llm = FakeLLM([tool_response("echo", "c1")])  # всегда просит инструмент
    reg = ToolRegistry()
    reg.register("echo", lambda **kw: "x", "echo", {"type": "object", "properties": {}})
    a = Agent(name="t", llm=llm, tools=reg)
    # на 9-м вызове FakeLLM вернёт текст, т.к. responses исчерпаны — ок
    result = await a.run("задача", max_iterations=8)
    assert result.content == "(пустой ответ теста)"


def test_agent_repr():
    a = Agent(name="t", llm=FakeLLM())
    assert "t" in repr(a)