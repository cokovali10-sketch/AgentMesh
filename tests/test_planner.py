from agentmesh.core.planner import Task, TaskStatus, plan


def test_plan_linear_dependencies():
    p = plan("цель", ["шаг 1", "шаг 2", "шаг 3"])
    assert p.estimate() == 3
    assert p.tasks[0].depends_on == []
    assert p.tasks[1].depends_on == [p.tasks[0].id]
    assert p.tasks[2].depends_on == [p.tasks[1].id]


def test_task_ready():
    t1 = Task(title="a")
    t2 = Task(title="b", depends_on=[t1.id])
    assert t1.ready(set())
    assert not t2.ready(set())
    assert t2.ready({t1.id})


def test_next_ready_ordering():
    p = plan("цель", ["x", "y"])
    done = set()
    first = p.next_ready(done)
    assert len(first) == 1
    assert first[0].title == "x"
    first[0].status = TaskStatus.DONE
    assert p.next_ready({first[0].id})[0].title == "y"


def test_plan_agent_for_step():
    p = plan("цель", ["a", "b"], agent_for_step=lambda i: "researcher" if i == 0 else "coder")
    assert p.tasks[0].agent == "researcher"
    assert p.tasks[1].agent == "coder"


def test_plan_to_dict():
    p = plan("цель", ["a"])
    d = p.to_dict()
    assert d["goal"] == "цель"
    assert len(d["tasks"]) == 1