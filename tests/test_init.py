import agentmesh


def test_version():
    assert agentmesh.__version__ == "0.1.0"


def test_public_api_exports():
    assert hasattr(agentmesh, "Agent")
    assert hasattr(agentmesh, "Orchestrator")
    assert hasattr(agentmesh, "plan")
    assert hasattr(agentmesh, "Message")