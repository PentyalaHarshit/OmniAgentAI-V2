from unittest.mock import MagicMock


def test_high_complex_reasoning_runs_all_agents_and_votes():
    from agents.high_complex_reasoning_agent import HighComplexReasoningAgent

    result = HighComplexReasoningAgent().run("compare mysql and mongodb")

    assert "mysql" in result["answer"].lower()
    assert "mongodb" in result["answer"].lower()
    assert "goal reasoning" in result["answer"].lower()
    assert result["verification"]["verified"] is True
    assert result["verification"]["confidence"] >= 0.8

    path = result["reasoning_path"]
    agent_names = {agent["agent"] for agent in path["agents"]}
    assert {
        "CoT Agent",
        "ToT Agent",
        "ReAct Agent",
        "Self-Reflect Agent",
    } <= agent_names
    assert path["winner"]
    assert len(path["votes"]) == 4


def test_general_agent_exposes_multi_reasoning_path():
    from agents.general_agent import GeneralAgent

    agent = GeneralAgent()
    agent.react_crew.run = MagicMock()

    result = agent.run("compare mysql and mongodb")

    agent.react_crew.run.assert_not_called()
    assert result["extra"]["source_stage"] == "multi_reasoning"
    assert result["extra"]["verification"]["verified"] is True
    assert "reasoning_path" in result["extra"]
    assert result["extra"]["reasoning_path"]["winner"]
    assert "decision reasoning" in result["answer"].lower()
