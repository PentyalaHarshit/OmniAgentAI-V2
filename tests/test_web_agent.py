from agents.web_agent import WebAgent, WebSummaryCache


class NoopCache(WebSummaryCache):
    def __init__(self):
        self._memory = []
        self._collection = None
        self.backend = "memory"


def test_web_agent_searches_before_fetching_selected_pages():
    agent = WebAgent(top_links=3, fetch_links=2, cache=NoopCache())

    agent.rewriter.rewrite = lambda query: [query]
    agent.searcher.search_many = lambda variants: [
        {
            "title": "Relevant current source",
            "url": "https://example.com/relevant",
            "text": "Latest release notes say OmniAgentAI WebAgent searches first.",
            "source": "DuckDuckGo",
        },
        {
            "title": "Unrelated source",
            "url": "https://example.com/unrelated",
            "text": "Cooking tips and unrelated text.",
            "source": "DuckDuckGo",
        },
        {
            "title": "Second relevant source",
            "url": "https://example.com/second",
            "text": "WebAgent fetches only selected pages after reranking links.",
            "source": "DuckDuckGo",
        },
    ]

    fetched_urls = []

    def fake_fetch(url):
        fetched_urls.append(url)
        if "relevant" in url:
            return "OmniAgentAI WebAgent searches the web first, reranks links, fetches selected pages, then caches a summary."
        return "This selected page says the WebAgent should not prechunk millions of pages."

    agent.reader.fetch = fake_fetch

    result = agent.run("How should OmniAgentAI WebAgent work?")

    assert len(fetched_urls) == 2
    assert result["agent"] == "WebAgent"
    assert result["extra"]["pipeline"] == [
        "search_first",
        "rerank_links",
        "fetch_selected_pages_only",
        "extract_answer",
        "cache_summary",
    ]
    assert result["extra"]["cache"]["backend"] == "memory"
    assert result["answer"]


def test_web_agent_cache_retrieval_uses_stored_summary():
    cache = NoopCache()
    cache.store(
        "latest python release",
        "Python release summary",
        [{"title": "Python", "url": "https://python.org"}],
    )

    result = cache.retrieve("python release")

    assert result["backend"] == "memory"
    assert result["results"]
    assert "Python release summary" in result["results"][0]["text"]


def test_router_sends_explicit_live_queries_to_web_agent():
    from agents.agent_router import AgentRouter

    router = AgentRouter()
    route, agent = router.route("latest AI news today")

    assert route == "general"
    assert agent.name == "GeneralAgent"


def test_web_agent_uses_local_fallback_when_searches_are_empty():
    agent = WebAgent(cache=NoopCache())
    agent.searcher.search_many = lambda variants: []
    agent.search_wikipedia = lambda query, top_k=5: []

    results = agent.search_web("What is agentic AI?", top_k=5)

    assert results
    assert results[0]["url"].startswith("local://")
    assert "agentic ai" in results[0]["title"].lower()


def test_cache_returns_attachment_style_documents_and_metadatas():
    cache = NoopCache()
    cache.store_summary(
        "agentic ai",
        {"title": "Agentic AI Overview", "url": "local://agentic-ai"},
        "Agentic AI can plan, reason, use tools, and self-correct.",
    )

    result = cache.retrieve("agentic ai")

    assert result["documents"]
    assert result["metadatas"]
    assert result["metadatas"][0]["title"] == "Agentic AI Overview"


def test_chroma_cache_returns_empty_when_best_distance_above_threshold():
    class FakeCollection:
        def query(self, query_texts, n_results):
            return {
                "ids": [["doc-1"]],
                "documents": [["Unrelated cached summary"]],
                "metadatas": [[{"query": "agentic ai"}]],
                "distances": [[0.75]],
            }

    cache = NoopCache()
    cache._collection = FakeCollection()
    cache.backend = "chromadb"

    result = cache.retrieve("FIFA World Cup 2026 standings")

    assert result["results"] == []
    assert result["documents"] == []
    assert result["cache_miss"] is True
