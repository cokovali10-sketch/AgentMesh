from agentmesh.core.memory import Memory
from agentmesh.core.message import Message, Role
# --- константы вынесены FORGE refactor ---
CONST_3 = 3



def _msg(sender: str, content: str) -> Message:
    return Message(role=Role.ASSISTANT, content=content, sender=sender)


def test_working_memory_roundtrip():
    mem = Memory()
    mem.remember_working(_msg("a", "один"))
    mem.remember_working(_msg("a", "два"))
    assert len(mem.recall_working()) == 2
    assert mem.recall_working()[0].content == "один"


def test_working_memory_cap():
    mem = Memory(max_working=CONST_3)
    for i in range(10):
        mem.remember_working(_msg("a", f"m{i}"))
    assert len(mem.recall_working()) == CONST_3
    assert mem.recall_working()[-1].content == "m9"


def test_episodic_recall_by_keywords():
    mem = Memory()
    mem.store_episode("Исправить ошибку в коде", "Исправлено")
    mem.store_episode("Найти данные по продажам", "Найдено")
    hits = mem.recall_episodes("ошибка в коде")
    assert len(hits) == 1
    assert hits[0]["task"] == "Исправить ошибку в коде"


def test_semantic_facts():
    mem = Memory()
    mem.store_fact("user_name", "Alice")
    assert mem.get_fact("user_name") == "Alice"
    assert mem.get_fact("missing", "default") == "default"


def test_save_load(tmp_path):
    mem = Memory()
    mem.store_fact("k", "v")
    mem.store_episode("t", "r")
    p = tmp_path / "mem.json"
    mem.save(p)
    mem2 = Memory()
    mem2.load(p)
    assert mem2.get_fact("k") == "v"
    assert len(mem2.episodic) == 1