"""
tests/test_general_react_pipeline.py
=====================================
Unit tests for the General Agent's full ReAct + WebRAG + Answer Extraction +
Fact Verification pipeline.

Tests are structured in 3 layers:
  1. Unit tests for individual tools (no network)
  2. Integration tests for GeneralReActAgent (mocked network)
  3. Integration tests for GeneralAgent cascade (mocked pipeline)
"""

import re
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Layer 1: Individual tool unit tests (no network required)
# ---------------------------------------------------------------------------

class TestAnswerExtractor:
    """AnswerExtractor correctly identifies answer types and extracts facts."""

    def setup_method(self):
        from tools.answer_extractor import AnswerExtractor
        self.extractor = AnswerExtractor()

    def test_capital_extraction(self):
        context = "France is a country in Western Europe. The capital of France is Paris, a major European city."
        answer = self.extractor.extract("what is the capital of france", context)
        assert "paris" in answer.lower(), f"Expected Paris in: {answer}"

    def test_inventor_passive_voice(self):
        context = "The telephone was invented by Alexander Graham Bell in 1876."
        answer = self.extractor.extract("who invented the telephone", context)
        assert "bell" in answer.lower() or "alexander" in answer.lower(), f"Got: {answer}"

    def test_duration_extraction(self):
        context = (
            "The Chola dynasty was a Tamil thalassocratic empire. "
            "The dynasty ruled from approximately 300 BCE to 1279 CE, a period of over 1500 years. "
            "The Imperial Chola period lasted from 848 CE to 1279 CE."
        )
        answer = self.extractor.extract("how long did the chola dynasty rule", context)
        assert answer, "Expected non-empty answer for duration question"
        assert "300" in answer or "1279" in answer or "1500" in answer, f"Got: {answer}"

    def test_yes_no_affirmative(self):
        context = "Alexander Graham Bell is credited with inventing the telephone. He received the patent in 1876."
        answer = self.extractor.extract("did alexander graham bell invent the telephone", context)
        assert "yes" in answer.lower() or "credited" in answer.lower(), f"Got: {answer}"

    def test_date_extraction(self):
        context = "World War II ended on 2 September 1945 with the formal surrender of Japan."
        answer = self.extractor.extract("when did world war 2 end", context)
        assert "1945" in answer, f"Expected 1945 in: {answer}"

    def test_fallback_compress(self):
        context = "Photosynthesis is the process by which plants make food using sunlight. It occurs in the chloroplasts."
        answer = self.extractor.extract("what is photosynthesis", context)
        assert len(answer) > 10, "Fallback should return something"

    def test_empty_context_returns_empty(self):
        assert self.extractor.extract("any question", "") == ""


class TestFactVerifier:
    """FactVerifier correctly verifies answers against source documents."""

    def setup_method(self):
        from tools.fact_verifier import FactVerifier
        self.verifier = FactVerifier()

    def test_known_wrong_query(self):
        result = self.verifier.verify("what is the capital of paris", "Paris", [])
        assert result["verified"] is False
        assert result["confidence"] == 0.0
        assert "city" in result["corrected"].lower() or "paris" in result["corrected"].lower()

    def test_supported_answer_is_verified(self):
        docs = [
            {"text": "Paris is the capital of France and its largest city."},
            {"text": "France is governed from Paris, its capital."},
        ]
        result = self.verifier.verify("what is the capital of france", "Paris is the capital of France.", docs)
        assert result["verified"] is True
        assert result["confidence"] > 0.3

    def test_empty_answer_returns_unverified(self):
        result = self.verifier.verify("some question", "", [])
        assert result["verified"] is False
        assert result["confidence"] == 0.0

    def test_no_docs_returns_partial(self):
        result = self.verifier.verify("who discovered gravity", "Isaac Newton discovered gravity.", [])
        # No docs but has an answer → unverified but answer preserved
        assert result["corrected"] == "Isaac Newton discovered gravity."
        assert result["sources_used"] == 0

    def test_confidence_increases_with_more_sources(self):
        docs_1 = [{"text": "Alexander Bell invented the telephone."}]
        docs_3 = [
            {"text": "Alexander Graham Bell invented the telephone in 1876."},
            {"text": "The telephone was invented by Alexander Bell, a Scottish inventor."},
            {"text": "Bell received the telephone patent in 1876."},
        ]
        answer = "Alexander Graham Bell invented the telephone."
        r1 = self.verifier.verify("who invented telephone", answer, docs_1)
        r3 = self.verifier.verify("who invented telephone", answer, docs_3)
        assert r3["confidence"] >= r1["confidence"], "More docs should give equal or higher confidence"


class TestQueryRewriter:
    """QueryRewriter generates meaningful search variant expansion."""

    def setup_method(self):
        from tools.web_search_tool import QueryRewriter
        self.rewriter = QueryRewriter()

    def test_duration_query_expands(self):
        variants = self.rewriter.rewrite("How long did the Chola dynasty rule?")
        assert len(variants) >= 3
        # Should include dynasty-focused variants
        combined = " ".join(variants).lower()
        assert "chola" in combined

    def test_inventor_query_expands(self):
        variants = self.rewriter.rewrite("Who invented the telephone?")
        assert len(variants) >= 2
        combined = " ".join(variants).lower()
        assert "telephone" in combined or "inventor" in combined

    def test_capital_query_expands(self):
        variants = self.rewriter.rewrite("What is the capital of Germany?")
        combined = " ".join(variants).lower()
        assert "germany" in combined
        assert "capital" in combined

    def test_no_duplicates(self):
        variants = self.rewriter.rewrite("What is the capital of France?")
        keys = [v.strip().lower() for v in variants]
        assert len(keys) == len(set(keys)), "Variants should be unique"

    def test_original_preserved(self):
        query = "Where is the Eiffel Tower?"
        variants = self.rewriter.rewrite(query)
        assert variants[0] == query, "First variant should be the original query"


class TestSimilarityRanker:
    """SimilarityRanker correctly ranks documents with domain boosts."""

    def setup_method(self):
        from tools.similarity_ranker import SimilarityRanker
        self.ranker = SimilarityRanker()

    def _make_docs(self, texts):
        return [{"title": t[:40], "text": t, "url": f"http://ex.com/{i}"} for i, t in enumerate(texts)]

    def test_relevant_doc_ranks_higher(self):
        docs = self._make_docs([
            "The Chola dynasty ruled South India for many centuries from 300 BCE to 1279 CE.",
            "Unrelated article about cooking techniques and recipes.",
        ])
        ranked = self.ranker.rank("How long did the Chola dynasty rule", docs)
        assert ranked[0]["text"].startswith("The Chola"), "Chola doc should rank first"

    def test_dynasty_boost_applied(self):
        docs = self._make_docs([
            "The Chola dynasty ruled South India from 300 BCE to 1279 CE.",
        ])
        ranked = self.ranker.rank("how long did the chola dynasty rule", docs)
        assert ranked[0]["similarity_score"] > 0.5, "Dynasty boost should push score above 0.5"

    def test_off_topic_penalty_applied(self):
        docs = self._make_docs([
            "Chola navy and maritime trade architecture temples.",
            "Chola dynasty ruled from 300 BCE to 1279 CE.",
        ])
        ranked = self.ranker.rank("how long did the Chola dynasty rule", docs)
        # The temple/navy page should score lower
        assert ranked[0]["text"].count("ruled") > 0 or ranked[1]["similarity_score"] < ranked[0]["similarity_score"]

    def test_all_docs_get_score(self):
        docs = self._make_docs(["hello world", "foo bar baz"])
        ranked = self.ranker.rank("test query", docs)
        for doc in ranked:
            assert "similarity_score" in doc
            assert doc["similarity_score"] >= 0.0


# ---------------------------------------------------------------------------
# Layer 2: GeneralReActAgent integration tests (mocked network calls)
# ---------------------------------------------------------------------------

class TestGeneralReActAgent:
    """GeneralReActAgent wires all components correctly."""

    def _make_agent(self):
        from tools.general_react_agent import GeneralReActAgent
        return GeneralReActAgent()

    def test_returns_expected_keys(self):
        agent = self._make_agent()
        # Mock the searcher to return empty so we don't need network
        agent.searcher.search_many = MagicMock(return_value=[])
        result = agent.run("What is the capital of France?")
        assert "answer" in result
        assert "sources" in result
        assert "verified" in result
        assert "thoughts" in result
        assert "tool_used" in result

    def test_thoughts_are_logged(self):
        agent = self._make_agent()
        agent.searcher.search_many = MagicMock(return_value=[])
        result = agent.run("Who invented the telephone?")
        assert isinstance(result["thoughts"], list)
        assert len(result["thoughts"]) >= 2

    def test_run_safe_returns_empty_on_error(self):
        agent = self._make_agent()
        # Make run() raise an exception
        agent.run = MagicMock(side_effect=RuntimeError("network down"))
        result = agent.run_safe("any query")
        assert result["answer"] == ""
        assert result["verified"]["verified"] is False
        assert isinstance(result["thoughts"], list)
        assert result["tool_used"] == "general_react_webrag"

    def test_with_mock_search_results(self):
        agent = self._make_agent()
        mock_docs = [
            {
                "title": "Alexander Graham Bell",
                "url": "https://en.wikipedia.org/wiki/Alexander_Graham_Bell",
                "text": (
                    "Alexander Graham Bell was a Scottish-born inventor. "
                    "The telephone was invented by Alexander Graham Bell in 1876. "
                    "He received a patent for the telephone on March 7, 1876."
                ),
                "source": "DuckDuckGo",
                "query_variant": "who invented the telephone",
            }
        ]
        agent.searcher.search_many = MagicMock(return_value=mock_docs)
        result = agent.run("Who invented the telephone?")
        # With a good mock doc the agent should produce an answer
        assert isinstance(result["answer"], str)
        # Verification dict should be populated
        assert "verified" in result
        assert isinstance(result["verified"], dict)

    def test_fetches_pages_chunks_and_answers_from_relevant_chunk(self):
        agent = self._make_agent()
        agent.searcher.max_pages_to_fetch = 2
        agent.searcher.search_many = MagicMock(return_value=[
            {
                "title": "Ada Lovelace overview",
                "url": "https://example.com/ada",
                "text": "Short snippet that does not contain the direct answer.",
                "source": "DuckDuckGo",
                "query_variant": "who created the first computer program",
            }
        ])
        agent.searcher.fetch_page_text = MagicMock(return_value=(
            "Ada Lovelace wrote notes about the Analytical Engine. "
            "Ada Lovelace created the first computer program for Charles Babbage's Analytical Engine. "
            "Her work is often discussed in histories of computing."
        ))

        result = agent.run("who created the first computer program")

        agent.searcher.fetch_page_text.assert_called_once_with("https://example.com/ada")
        assert "ada lovelace" in result["answer"].lower()
        assert any("Built" in t and "chunks" in t for t in result["thoughts"])
        assert any("Similarity rank extracted chunks" in t for t in result["thoughts"])

    def test_empty_search_returns_empty_answer(self):
        agent = self._make_agent()
        agent.searcher.search_many = MagicMock(return_value=[])
        result = agent.run("xyzzy frobnicator quux")
        assert result["answer"] == ""
        assert result["verified"]["verified"] is False


class TestReActGeneralCrew:
    """ReActGeneralCrew falls back from Wikipedia to web search content."""

    def test_search_agent_uses_web_fallback_when_wikipedia_empty(self, monkeypatch):
        import crews.react_general_crew as crew_module
        from crews.react_general_crew import SearchAgent

        monkeypatch.setattr(crew_module, "_wiki_search", lambda query, prefer="": ("", ""))
        monkeypatch.setattr(crew_module, "_web_search_duckduckgo", lambda query, max_results=3: [
            {
                "title": "Ada Lovelace biography",
                "url": "https://example.com/ada",
                "text": "Ada Lovelace is often regarded as the first computer programmer.",
                "source": "DuckDuckGo Web",
            }
        ])

        result = SearchAgent().run("Ada Lovelace", "general")
        assert result["source"] == "DuckDuckGo Web"
        assert result["url"] == "https://example.com/ada"
        assert "first computer programmer" in result["text"]

    def test_crew_labels_web_fallback_result(self, monkeypatch):
        import crews.react_general_crew as crew_module
        from crews.react_general_crew import ReActGeneralCrew

        monkeypatch.setattr(crew_module, "_wiki_search", lambda query, prefer="": ("", ""))
        monkeypatch.setattr(crew_module, "_web_search_duckduckgo", lambda query, max_results=3: [
            {
                "title": "Ada Lovelace biography",
                "url": "https://example.com/ada",
                "text": "Ada Lovelace is often regarded as the first computer programmer.",
                "source": "DuckDuckGo Web",
            }
        ])

        result = ReActGeneralCrew().run("Who was Ada Lovelace?")
        assert result["tool_used"] == "web_react_crew"
        assert result["answer"]
        assert any(
            step.get("output", {}).get("source") == "DuckDuckGo Web"
            for step in result["crew_steps"]
            if isinstance(step.get("output"), dict)
        )


# ---------------------------------------------------------------------------
# Layer 3: GeneralAgent cascade tests (mocked sub-agents)
# ---------------------------------------------------------------------------

class TestGeneralAgentCascade:
    """GeneralAgent correctly cascades through pipeline stages."""

    def _make_agent(self):
        from agents.general_agent import GeneralAgent
        agent = GeneralAgent()
        # Silence all external calls
        agent.live_apis.run = MagicMock(return_value={"answer": "", "tool_used": "", "all_results": []})
        agent.mcp.run = MagicMock(return_value={"answer": ""})
        return agent

    def test_builtin_facts_short_circuits(self):
        """BuiltInFacts should answer before any web call."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()  # Should NOT be called
        result = agent.run("who invented the telephone")
        # react_crew should not be called since BuiltInFacts answers
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        assert "bell" in result["answer"].lower()
        assert result["extra"]["source_stage"] == "built_in_facts"

    @pytest.mark.parametrize(
        "query, expected",
        [
            ("who was first mughal emperor", "Babur"),
            ("who was akbar?", "1556"),
            ("who invented c++?", "Bjarne Stroustrup"),
            ("what is rag", "Retrieval-Augmented Generation"),
            ("capital of japan", "Tokyo"),
        ],
    )
    def test_exact_builtin_facts_answer_common_questions(self, query, expected):
        """Exact common facts should answer before broader web/reasoning stages."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run(query)
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        assert expected in result["answer"]
        assert result["extra"]["source_stage"] == "built_in_facts"

    def test_qdrant_knowledge_answers_before_web_search(self):
        """Vector knowledge chunks should answer after built-ins and before web stages."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        agent.knowledge_rag.search = MagicMock(return_value=[
            {
                "title": "Ada Lovelace",
                "source": "manual",
                "url": "manual",
                "text": "Ada Lovelace was an English mathematician known for early computer programming work.",
                "similarity_score": 0.91,
            }
        ])
        agent.knowledge_rag.build_context = MagicMock(
            return_value=(
                "Source: Ada Lovelace\n"
                "URL: manual\n"
                "Text: Ada Lovelace was an English mathematician known for early computer programming work."
            )
        )

        result = agent.run("according to the knowledge base, who was Ada Lovelace")

        agent.knowledge_rag.search.assert_called_once()
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        assert "Ada Lovelace" in result["answer"]
        assert result["extra"]["source_stage"] == "qdrant_knowledge"

    def test_huge_general_facts_answers_before_vector_and_web(self, tmp_path):
        """Large local fact index should answer after built-ins and before vector/web."""
        from tools.huge_general_facts import HugeGeneralFacts

        jsonl = tmp_path / "facts.jsonl"
        jsonl.write_text(
            '{"query":"who was hypatia","answer":"Hypatia was a philosopher and mathematician in Alexandria.","category":"history","source":"test"}',
            encoding="utf-8",
        )

        agent = self._make_agent()
        agent.huge_facts = HugeGeneralFacts(db_path=str(tmp_path / "missing.sqlite"), jsonl_path=str(jsonl))
        agent.knowledge_rag.search = MagicMock(return_value=[])
        agent.react_crew.run = MagicMock()

        result = agent.run("Who was Hypatia?")

        agent.knowledge_rag.search.assert_not_called()
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        assert "philosopher and mathematician" in result["answer"]
        assert result["extra"]["source_stage"] == "huge_general_facts"

    def test_math_route_uses_calculator_inside_general_agent(self):
        """Math queries should route directly to CalculatorTool."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("calculate 12 * 8")
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        assert "96" in result["answer"]
        assert result["extra"]["source_stage"] == "calculator_tool"

    def test_live_route_runs_before_builtins_for_current_queries(self):
        """Live/current queries should use live tools before local facts."""
        agent = self._make_agent()
        agent.live_apis.run = MagicMock(return_value={
            "answer": "Live checked answer.",
            "tool_used": "web_search",
            "all_results": [{"tool": "web_search", "result": "Live checked answer."}],
        })
        agent.react_crew.run = MagicMock()
        result = agent.run("current president of USA")
        agent.live_apis.run.assert_called_once()
        agent.react_crew.run.assert_not_called()
        assert result["answer"] == "Live checked answer."
        assert result["extra"]["source_stage"] == "real_api:web_search"

    def test_general_knowledge_route_prefers_llm_guidance(self):
        """General knowledge should use LLM reasoning without requiring web verification."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        query = (
            "Why did the Roman Empire collapse? "
            "[Free LLM Tree Guidance] The Roman Empire declined because of political instability, "
            "economic pressure, military overextension, and repeated invasions."
        )
        result = agent.run(query)
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        assert "political instability" in result["answer"].lower()
        assert result["extra"]["source_stage"] == "llm_knowledge"

    def test_world_war_one_causes_effects_uses_builtin_fact(self):
        """WWI causes/effects should answer directly instead of hitting the guard."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("Explain the causes and effects of World War I.")
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        answer = result["answer"].lower()
        assert "militarism" in answer
        assert "alliances" in answer
        assert "treaty of versailles" in answer
        assert result["extra"]["source_stage"] == "built_in_facts"

    def test_ai_theorem_question_uses_general_knowledge_fact(self):
        """Conceptual can/could AI questions should not require live verification."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("Can AI discover a new theorem?")
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        answer = result["answer"].lower()
        assert "yes" in answer
        assert "theorem" in answer
        assert "rigorous proof" in answer
        assert result["extra"]["source_stage"] == "built_in_facts"

    @pytest.mark.parametrize(
        "query, expected",
        [
            ("What is the Solar System?", "Sun"),
            ("Who was the first person on the Moon?", "Neil Armstrong"),
            ("What is Mars?", "Red Planet"),
            ("What is Jupiter?", "largest planet"),
            ("What is a galaxy?", "gravity"),
            ("What is the Milky Way?", "Solar System"),
            ("What is a supernova?", "stellar explosion"),
            ("What is a neutron star?", "dense collapsed core"),
            ("What is a comet?", "tail"),
            ("What is an asteroid?", "asteroid belt"),
        ],
    )
    def test_astronomy_questions_use_builtin_facts(self, query, expected):
        """Common astronomy questions should answer directly from built-in facts."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run(query)
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        assert expected.lower() in result["answer"].lower()
        assert result["extra"]["source_stage"] == "built_in_facts"

    def test_summary_variant_reuses_local_fact(self):
        """Summary-style wording should reuse local what-is facts before web."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("give me a short summary of mars")
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        assert "red planet" in result["answer"].lower()
        assert result["extra"]["source_stage"] == "fact_variant"

    def test_more_population_uses_builtin_facts(self):
        """Informal population ranking phrasing should not drift into Wikipedia snippets."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("which country has more population")
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        assert "india" in result["answer"].lower()
        assert "european countries" not in result["answer"].lower()
        assert result["extra"]["source_stage"] == "built_in_facts"

    def test_napoleon_importance_uses_specific_fact_not_placeholder(self):
        """Historical importance questions should return substance, not generated corpus filler."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("why is napoleon bonaparte important")
        agent.react_crew.run.assert_not_called()
        answer = result["answer"].lower()
        assert "short answer" in answer
        assert "more detail" in answer
        assert "napoleonic code" in answer
        assert "waterloo" in answer
        assert "key topic in history" not in answer
        assert result["extra"]["source_stage"] == "built_in_facts"

    def test_explain_more_followup_expands_last_importance_topic(self):
        """A terse elaboration follow-up should reuse the last topic from memory."""
        from tools.chat_memory import ChatMemory

        session_id = "test_napoleon_explain_more"
        memory = ChatMemory()
        memory.clear(session_id)
        memory.add(session_id, "user", "why is napoleon bonaparte important")
        memory.add(
            session_id,
            "assistant",
            "Napoleon Bonaparte is important because he reshaped France and Europe.",
        )

        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("Explain more.", session_id=session_id)
        agent.react_crew.run.assert_not_called()
        answer = result["answer"].lower()
        assert "short answer" in answer
        assert "more detail" in answer
        assert "napoleonic code" in answer
        assert "goal reasoning" not in answer
        assert result["extra"]["source_stage"] == "built_in_facts"

    def test_us_president_uses_builtin_current_fact(self):
        """Current officeholder phrasing should answer the person, not the office definition."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("who is president of USA")
        agent.react_crew.run.assert_not_called()
        assert "donald" in result["answer"].lower()
        assert "j. trump" in result["answer"].lower()
        assert "head of state and head of government" not in result["answer"].lower()
        assert result["extra"]["source_stage"] == "built_in_facts"

    def test_facebook_owner_uses_builtin_fact(self):
        """Facebook ownership questions should not drift into unrelated retrieval snippets."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("who is owner of facebook")
        agent.react_crew.run.assert_not_called()
        assert "meta platforms" in result["answer"].lower()
        assert "mark zuckerberg" in result["answer"].lower()
        assert "donald trump" not in result["answer"].lower()
        assert result["extra"]["source_stage"] == "built_in_facts"

    @pytest.mark.parametrize(
        "query, expected_terms",
        [
            ("who is owner of google", ["alphabet", "sundar pichai"]),
            ("who is ceo of tesla", ["elon musk"]),
            ("who is prime minister of india", ["narendra modi"]),
            ("who is founder of amazon", ["jeff bezos"]),
            ("who is owner of instagram", ["meta platforms"]),
            ("what is machine learning", ["artificial intelligence", "patterns from data"]),
            ("who invented the internet", ["no single person", "vint cerf", "bob kahn", "tcp/ip"]),
            ("who invented the world wide web", ["tim berners-lee", "cern", "http", "html"]),
        ],
    )
    def test_common_questions_use_builtin_facts(self, query, expected_terms):
        """Common stable questions should not depend on web retrieval."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run(query)
        agent.react_crew.run.assert_not_called()
        answer = result["answer"].lower()
        for term in expected_terms:
            assert term in answer
        assert "search error" not in answer
        assert result["extra"]["source_stage"] == "built_in_facts"

    @pytest.mark.parametrize(
        "query, expected_terms",
        [
            ("When did Mughal ruled in India?", ["1526", "1857"]),
            ("how long did Mughal rule in India", ["331 years"]),
        ],
    )
    def test_mughal_rule_questions_use_builtin_facts(self, query, expected_terms):
        """Mughal rule questions should answer with dates instead of a generic definition."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run(query)
        agent.react_crew.run.assert_not_called()
        answer = result["answer"].lower()
        for term in expected_terms:
            assert term.lower() in answer
        assert "early modern empire in south asia" not in answer
        assert result["extra"]["source_stage"] == "built_in_facts"

    @pytest.mark.parametrize(
        "query",
        [
            "how is india country?",
            "how is India as a country",
            "tell me about India country",
        ],
    )
    def test_india_overview_questions_use_builtin_fact(self, query):
        """Broad India overview questions should answer conversationally."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run(query)
        agent.react_crew.run.assert_not_called()
        answer = result["answer"].lower()
        assert "diverse democratic country" in answer
        assert "south asia" in answer
        assert "challenges" in answer
        assert "officially the republic of india" not in answer
        assert result["extra"]["source_stage"] == "built_in_facts"

    def test_gpt_claude_comparison_uses_verified_multi_reasoning_fact(self):
        """Known model comparison prompt should return a useful verified comparison."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("Compare GPT-4, GPT-5, and Claude.")
        agent.react_crew.run.assert_not_called()
        answer = result["answer"].lower()
        assert "multi-reasoning view" in answer
        assert "gpt-4" in answer
        assert "gpt-5" in answer
        assert "claude" in answer
        assert result["extra"]["source_stage"] == "built_in_facts"

    def test_generic_compare_uses_multi_reasoning_framework(self):
        """Generic compare prompts should get multiple reasoning lenses instead of guard refusal."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("compare mysql and mongodb")
        agent.react_crew.run.assert_not_called()
        answer = result["answer"].lower()
        assert "goal reasoning" in answer
        assert "risk reasoning" in answer
        assert "decision reasoning" in answer
        assert result["extra"]["source_stage"] == "multi_reasoning"
        assert result["extra"]["verification"]["verified"] is True

    def test_llm_guidance_general_knowledge_is_allowed_without_live_verification(self):
        """General knowledge LLM guidance should not be blocked for missing web sources."""
        agent = self._make_agent()
        agent.huge_facts.lookup = MagicMock(return_value="")
        agent.react_crew.run = MagicMock()
        query = (
            "Explain Agentic RAG "
            "[Free LLM Tree Guidance] Agentic RAG combines retrieval with an agent that can plan, "
            "choose tools, inspect retrieved context, and revise its answer."
        )
        result = agent.run(query)
        agent.react_crew.run.assert_not_called()
        assert "agentic rag combines retrieval" in result["answer"].lower()
        assert result["extra"]["source_stage"] == "llm_knowledge"
        assert result["extra"]["verification"]["confidence"] >= 0.8

    @pytest.mark.parametrize(
        "query",
        [
            "Who was king of Mars in 1800?",
            "Capital of Atlantis?",
        ],
    )
    def test_unknown_fictional_facts_are_blocked(self, query):
        """Invalid unknown-fact prompts should be blocked instead of guessed."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run(query)
        agent.react_crew.run.assert_not_called()
        assert result["answer"] == "I could not verify this answer, so I will not guess."
        assert result["extra"]["source_stage"] == "query_validation"

    @pytest.mark.parametrize(
        "query",
        [
            "who was first king of mughal?",
            "who was the first emperor of the Mughals",
            "first ruler of Mughal",
        ],
    )
    def test_first_mughal_ruler_uses_info_card(self, query):
        """First Mughal ruler questions should return Babur in the rich card payload."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run(query)
        agent.react_crew.run.assert_not_called()
        answer = result["answer"].lower()
        assert "info_card" in answer
        assert "babur" in answer
        assert "21 april 1526" in answer
        assert "emperor_babur.jpg" in answer
        assert result["extra"]["source_stage"] == "built_in_facts"

    def test_similar_query_reuses_previous_memory_answer(self, tmp_path):
        """A later similar query should reuse the previous assistant answer from memory."""
        from tools.chat_memory import ChatMemory

        agent = self._make_agent()
        agent.memory = ChatMemory(str(tmp_path / "chat_memory.json"))
        agent.react_crew.run = MagicMock()
        session_id = "similar_memory_test"

        first = agent.run("who was first king of mughal?", session_id=session_id)
        agent.memory.add(session_id, "user", "who was first king of mughal?")
        agent.memory.add(session_id, "assistant", first["answer"])

        second = agent.run("tell me first mughal emperor", session_id=session_id)
        assert second["extra"]["source_stage"] == "memory_similar"
        assert "babur" in second["answer"].lower()
        assert second["answer"] == first["answer"]
        assert second["extra"]["memory_match"]["similarity"] >= 0.55

    def test_country_info_short_circuits(self):
        """CountryInfoTool should answer capital/population before crew."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        result = agent.run("what is the capital of france")
        agent.react_crew.run.assert_not_called()
        assert "paris" in result["answer"].lower()
        assert result["extra"]["source_stage"] == "country_info_tool"

    def test_reasoning_engine_general_knowledge_answer_is_allowed(self):
        """LLM-tree guidance can answer general knowledge without live verification."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock()
        query = (
            "what is gradient clipping\n\n"
            "[Free LLM Tree Guidance]\n"
            "Gradient clipping limits large neural-network gradients to stabilize training."
        )
        result = agent.run(query)
        agent.live_apis.run.assert_not_called()
        agent.react_crew.run.assert_not_called()
        assert "gradient clipping limits" in result["answer"].lower()
        assert result["extra"]["source_stage"] == "llm_knowledge"
        assert result["extra"]["verification"]["confidence"] >= 0.8
        assert result["extra"]["verification"]["verified"] is True

    def test_live_api_only_for_current_query_after_local_checks(self):
        """Current/live queries should still trigger live tools."""
        agent = self._make_agent()
        agent.live_apis.run = MagicMock(return_value={
            "answer": "Current weather: clear.",
            "tool_used": "weather",
            "all_results": [{"tool": "weather", "result": "Current weather: clear."}],
        })
        result = agent.run("what is the weather in Dallas today")
        agent.live_apis.run.assert_called_once()
        assert result["answer"] == "Current weather: clear."
        assert result["extra"]["source_stage"] == "real_api:weather"

    def test_react_webrag_called_when_crew_empty(self):
        """GeneralReActAgent should be called when ReActGeneralCrew returns empty."""
        agent = self._make_agent()
        # Make crew return empty
        agent.react_crew.run = MagicMock(return_value={
            "crew_steps": [], "answer": "", "tool_used": "", "all_results": [], "verification": {}
        })
        # Make react_agent return an answer
        agent.react_agent.run_safe = MagicMock(return_value={
            "answer": "No single person invented the Internet; Vint Cerf and Bob Kahn designed TCP/IP.",
            "sources": [{"title": "Internet history", "url": "http://example.com"}],
            "verified": {"verified": True, "confidence": 0.8, "reason": "Mock.", "corrected": "No single person invented the Internet; Vint Cerf and Bob Kahn designed TCP/IP.", "sources_used": 1},
            "thoughts": ["Thought: searched for internet inventor", "Action: found result"],
            "tool_used": "general_react_webrag",
        })
        result = agent.run("who invented the arpanet-era internet protocols")
        agent.react_agent.run_safe.assert_called_once()
        answer = result["answer"].lower()
        assert "no single person" in answer
        assert "cerf" in answer
        assert "kahn" in answer
        assert "react_webrag" in result["extra"]["source_stage"]

    def test_web_rag_fallback_when_react_webrag_empty(self):
        """WebRAGTool fallback should be called when both crews return empty."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock(return_value={
            "crew_steps": [], "answer": "", "tool_used": "", "all_results": [], "verification": {}
        })
        agent.react_agent.run_safe = MagicMock(return_value={
            "answer": "", "sources": [], "verified": {}, "thoughts": [], "tool_used": "general_react_webrag"
        })
        agent.web_rag.search = MagicMock(return_value=[
            {"title": "Test", "url": "http://t.com", "text": "Paris is the capital of France.", "similarity_score": 0.8}
        ])
        agent.web_rag.build_context = MagicMock(return_value="Source: Test\nText: Paris is the capital of France.")
        result = agent.run("what is the capital city of france in europe")
        agent.react_agent.run_safe.assert_called_once()
        agent.web_rag.search.assert_called_once()

    def test_offline_fallback_when_all_stages_empty(self):
        """Offline fallback message returned when all stages produce nothing."""
        agent = self._make_agent()
        agent.react_crew.run = MagicMock(return_value={
            "crew_steps": [], "answer": "", "tool_used": "", "all_results": [], "verification": {}
        })
        agent.react_agent.run_safe = MagicMock(return_value={
            "answer": "", "sources": [], "verified": {}, "thoughts": [], "tool_used": "general_react_webrag"
        })
        agent.web_rag.search = MagicMock(return_value=[])
        result = agent.run("xyzzy totally unknown query 12345")
        assert result["answer"] == "I could not verify this answer, so I will not guess."
        assert result["extra"]["source_stage"] == "hallucination_guard"

    def test_response_always_has_verification(self):
        """Every response from GeneralAgent should include a verification dict."""
        agent = self._make_agent()
        result = agent.run("what is the speed of light")
        assert "verification" in result["extra"]
        v = result["extra"]["verification"]
        assert "verified" in v
        assert "confidence" in v
        assert "reason" in v
        assert "corrected" in v
        assert "sources_used" in v

    def test_thoughts_list_always_returned(self):
        """Thoughts list should always be a non-empty list."""
        agent = self._make_agent()
        result = agent.run("who won world war 2")
        assert isinstance(result["thoughts"], list)
        assert len(result["thoughts"]) > 0

    def test_query_validation_rejects_bad_query(self):
        """Nonsensical query like 'capital of Paris' should be rejected at validation."""
        agent = self._make_agent()
        result = agent.run("what is the capital of paris")
        assert result["extra"]["source_stage"] == "query_validation"
        assert "paris" in result["answer"].lower()
