from unittest.mock import MagicMock


def test_roman_empire_fall_uses_history_rag_fallback_when_web_empty():
    from agents.general_agent import GeneralAgent

    agent = GeneralAgent()
    agent.facts.lookup = MagicMock(return_value="")
    agent.huge_facts.lookup = MagicMock(return_value="")
    agent.knowledge_rag.search = MagicMock(return_value=[])
    agent.web_rag.search = MagicMock(return_value=[])
    agent.mcp.run = MagicMock(return_value={"answer": "", "tool_used": "", "all_results": []})
    agent.react_crew.run = MagicMock()

    result = agent.run("Why did the Roman Empire fall?")

    agent.web_rag.search.assert_called_once()
    agent.react_crew.run.assert_not_called()
    assert result["extra"]["source_stage"] == "reasoning_rag"
    assert result["extra"]["verification"]["verified"] is True
    assert result["extra"]["verification"]["sources_used"] >= 1
    answer = result["answer"].lower()
    assert "political instability" in answer
    assert "economic" in answer
    assert "military" in answer
    assert "476" in answer


def test_roman_empire_fall_uses_wiki_chunks_before_web_links():
    from agents.general_agent import GeneralAgent

    agent = GeneralAgent()
    agent.facts.lookup = MagicMock(return_value="")
    agent.huge_facts.lookup = MagicMock(return_value="")
    agent.knowledge_rag.search = MagicMock(return_value=[])
    agent.retrieve_wiki_rag_docs = MagicMock(return_value=[
        {
            "title": "Wikipedia - Fall of the Western Roman Empire",
            "url": "https://en.wikipedia.org/wiki/Fall_of_the_Western_Roman_Empire",
            "text": (
                "The Western Roman Empire declined because of political instability, "
                "economic problems, military pressure, and invasions."
            ),
            "source": "Wikipedia",
            "similarity_score": 0.95,
            "chunk_index": 1,
        }
    ])
    agent.web_rag.search = MagicMock(return_value=[
        {
            "title": "History - Fall of Rome",
            "url": "https://example.com/fall-of-rome",
            "text": "External invasions and internal instability contributed to Rome's fall in the west.",
            "source": "DuckDuckGo",
            "similarity_score": 0.82,
        }
    ])
    agent.react_crew.run = MagicMock()

    result = agent.run("Why did the Roman Empire fall?")

    agent.retrieve_wiki_rag_docs.assert_called_once()
    agent.web_rag.search.assert_called_once()
    assert result["extra"]["source_stage"] == "reasoning_rag"
    assert result["extra"]["verification"]["verified"] is True
    assert "political instability" in result["answer"].lower()


def test_world_war_ii_stop_uses_history_rag_date_answer_when_web_empty():
    from agents.general_agent import GeneralAgent

    agent = GeneralAgent()
    agent.facts.lookup = MagicMock(return_value="")
    agent.huge_facts.lookup = MagicMock(return_value="")
    agent.knowledge_rag.search = MagicMock(return_value=[])
    agent.web_rag.search = MagicMock(return_value=[])
    agent.mcp.run = MagicMock(return_value={"answer": "", "tool_used": "", "all_results": []})
    agent.react_crew.run = MagicMock()

    result = agent.run("when did world war II stop")

    agent.web_rag.search.assert_called_once()
    agent.react_crew.run.assert_not_called()
    assert result["extra"]["source_stage"] == "reasoning_rag"
    assert result["extra"]["verification"]["verified"] is True
    assert result["extra"]["verification"]["sources_used"] >= 1
    answer = result["answer"].lower()
    assert "2 september 1945" in answer
    assert "8 may 1945" in answer


def test_world_war_ii_detail_explanation_uses_general_knowledge_rag_when_web_empty():
    from agents.general_agent import GeneralAgent

    agent = GeneralAgent()
    agent.facts.lookup = MagicMock(return_value="")
    agent.huge_facts.lookup = MagicMock(return_value="")
    agent.knowledge_rag.search = MagicMock(return_value=[])
    agent.web_rag.search = MagicMock(return_value=[])
    agent.mcp.run = MagicMock(return_value={"answer": "", "tool_used": "", "all_results": []})
    agent.react_crew.run = MagicMock()

    result = agent.run("Explain World War II in detail.")

    agent.web_rag.search.assert_called_once()
    agent.react_crew.run.assert_not_called()
    assert result["extra"]["source_stage"] == "reasoning_rag"
    assert result["extra"]["verification"]["verified"] is True
    assert result["extra"]["verification"]["sources_used"] >= 1
    answer = result["answer"].lower()
    assert "1939" in answer
    assert "1945" in answer
    assert "allies" in answer
    assert "axis" in answer
    assert "cold war" in answer
