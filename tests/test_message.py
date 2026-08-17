from agentmesh.core.message import Message, Role


def test_message_defaults():
    m = Message(role=Role.USER, content="привет", sender="user")
    assert m.recipient == "*"
    assert m.to_llm_dict() == {"role": "user", "content": "привет"}


def test_message_short_truncates():
    m = Message(role=Role.ASSISTANT, content="x" * 500, sender="a")
    assert "…" in m.short()


def test_message_short_full():
    m = Message(role=Role.ASSISTANT, content="короткий", sender="a", recipient="b")
    assert "[a→b] короткий" == m.short()