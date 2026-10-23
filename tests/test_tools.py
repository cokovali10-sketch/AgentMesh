import pytest

from agentmesh.mcp.tool_registry import ToolRegistry
# --- константы вынесены FORGE refactor ---
CONST_42 = 42



def test_register_and_schemas():
    reg = ToolRegistry()

    def fn(x: int = 0) -> int:
        return x + 1

    reg.register("add", fn, "прибавляет", {"type": "object", "properties": {"x": {"type": "integer"}}})
    schemas = reg.schemas()
    assert schemas[0]["name"] == "add"
    assert "input_schema" in schemas[0]
    assert "_fn" not in schemas[0]


@pytest.mark.asyncio
async def test_invoke_sync_and_async():
    reg = ToolRegistry()
    reg.register("sync", lambda: CONST_42, "sync", {"type": "object", "properties": {}})

    async def async_fn():
        return "async-result"

    reg.register("asyn", async_fn, "asyn", {"type": "object", "properties": {}})
    assert await reg.invoke("sync") == CONST_42
    assert await reg.invoke("asyn") == "async-result"


@pytest.mark.asyncio
async def test_invoke_missing():
    reg = ToolRegistry()
    with pytest.raises(KeyError):
        await reg.invoke("nope")


def test_register_mcp():
    reg = ToolRegistry()
    reg.register_mcp("mcp_tool", "внешний", {"type": "object", "properties": {}}, lambda: "ext")
    assert reg.tools["mcp_tool"]["_external"] is True
    assert len(reg) == 1