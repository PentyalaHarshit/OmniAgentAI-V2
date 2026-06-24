from agents.agent_router import AgentRouter
from agents.research_agent import ResearchAgent


def test_research_agent_general_agentic_rag_report():
    result = ResearchAgent().run("Research Agentic RAG architectures.")

    assert result["extra"]["selected_research_agent"] == "ResearchAgent"
    assert "observation_guided_tot_react" in result["extra"]
    assert any("Observation-Guided ToT-ReAct" in thought for thought in result["thoughts"])
    assert "Research Report" in result["answer"]
    assert "Research Gaps" in result["answer"]
    assert "Verifier Agent" in result["answer"]


def test_paper_agent_attention_summary():
    result = ResearchAgent().run("Explain the Attention Is All You Need paper.")

    assert result["extra"]["selected_research_agent"] == "PaperAgent"
    assert "Paper Summary" in result["answer"]
    assert "Key Contributions" in result["answer"]
    assert "Transformer architecture" in result["answer"]


def test_ai_trend_agent_latest_news_caveat():
    result = ResearchAgent().run("Latest AI news this week.")

    assert result["extra"]["selected_research_agent"] == "AITrendAgent"
    assert "Latest AI Trend Summary" in result["answer"]
    assert "Live news search is not connected" in result["answer"]


def test_research_planner_stress_query_uses_innovation_agent():
    result = ResearchAgent().run(
        "Research whether AI can invent new algorithms. Search existing papers. "
        "Identify research gaps. Generate 5 possible approaches. Evaluate novelty. "
        "Create a research roadmap. Provide benchmarks and evaluation metrics."
    )

    assert result["extra"]["selected_research_agent"] == "InnovationAgent"
    assert "Novelty Score" in result["answer"]
    assert "Generate 5 Possible Approaches" in result["answer"]
    assert "Evaluation Metrics" in result["answer"]


def test_benchmark_agent_model_comparison():
    result = ResearchAgent().run("Compare GPT-5, Claude, Gemini, DeepSeek and Qwen.")

    assert result["extra"]["selected_research_agent"] == "BenchmarkAgent"
    assert "Model Ranking" in result["answer"]
    assert "Best Use Cases" in result["answer"]


def test_router_sends_research_examples_to_general_agent():
    router = AgentRouter()

    for query in [
        "Latest AI news this week.",
        "Explain the Attention Is All You Need paper.",
        "Compare GPT-5, Claude, Gemini, DeepSeek and Qwen.",
        "Can AI invent new algorithms?",
    ]:
        route, agent = router.route(query)
        assert route == "general"
        assert agent.name == "GeneralAgent"
