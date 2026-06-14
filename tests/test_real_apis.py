from agents.general_agent import GeneralAgent
from tools import mcp_live_tools
from tools.mcp_live_tools import LiveAPIRunner, NewsTool, SearchAPITool, SportsTool, WeatherTool


def test_weather_tool_uses_open_meteo(monkeypatch):
    calls = []

    def fake_get(url, as_text=False):
        calls.append(url)
        if "geocoding-api.open-meteo.com" in url:
            return {"results": [{"latitude": 32.77, "longitude": -96.79, "name": "Dallas", "country": "United States"}]}
        if "api.open-meteo.com" in url:
            return {"current": {"temperature_2m": 25, "relative_humidity_2m": 50, "wind_speed_10m": 12, "weathercode": 0}}
        return None

    monkeypatch.setattr(mcp_live_tools, "_get", fake_get)

    answer = WeatherTool().execute("What is the weather in Dallas today?")

    assert "Current Weather in Dallas, United States" in answer
    assert "Open-Meteo" in answer
    assert len(calls) == 2


def test_news_tool_uses_google_news_rss(monkeypatch):
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)
    rss = """
    <rss><channel>
      <item><title>AI headline</title><link>https://example.com/ai</link><pubDate>Sat, 13 Jun 2026 10:00:00 GMT</pubDate></item>
    </channel></rss>
    """
    monkeypatch.setattr(mcp_live_tools, "_get", lambda url, as_text=False: rss if as_text else None)

    answer = NewsTool().execute("latest news about AI")

    assert "Latest News" in answer
    assert "AI headline" in answer
    assert "Google News RSS" in answer


def test_news_tool_uses_newsapi_when_key_is_set(monkeypatch):
    monkeypatch.setenv("NEWSAPI_KEY", "test-key")
    monkeypatch.setattr(mcp_live_tools, "_get", lambda url, as_text=False: {
        "status": "ok",
        "articles": [{
            "title": "NewsAPI headline",
            "url": "https://example.com/newsapi",
            "source": {"name": "Example News"},
            "publishedAt": "2026-06-13T10:00:00Z",
        }],
    })

    answer = NewsTool().execute("latest news about AI")

    assert "NewsAPI headline" in answer
    assert "NewsAPI.org" in answer


def test_sports_tool_uses_sportsdb(monkeypatch):
    def fake_get(url, as_text=False):
        if "searchteams.php" in url:
            return {"teams": [{"strTeam": "Golden State Warriors", "idTeam": "134860", "strSport": "Basketball", "strLeague": "NBA", "strCountry": "USA", "strStadium": "Chase Center"}]}
        if "eventslast.php" in url:
            return {"results": [{"dateEvent": "2026-06-01", "strHomeTeam": "Warriors", "intHomeScore": "110", "strAwayTeam": "Lakers", "intAwayScore": "100"}]}
        return None

    monkeypatch.setattr(mcp_live_tools, "_get", fake_get)

    answer = SportsTool().execute("latest score for Warriors")

    assert "Golden State Warriors" in answer
    assert "Recent Results" in answer
    assert "TheSportsDB" in answer


def test_search_api_tool_uses_duckduckgo_without_key(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    monkeypatch.setattr(mcp_live_tools, "_get", lambda url, as_text=False: {
        "Heading": "OmniAgentAI",
        "AbstractText": "OmniAgentAI is an agent project.",
        "AbstractURL": "https://example.com/omni",
        "RelatedTopics": [],
    })

    answer = SearchAPITool().execute("search OmniAgentAI")

    assert "Search Result" in answer
    assert "OmniAgentAI is an agent project." in answer
    assert "DuckDuckGo Instant Answer API" in answer


def test_live_api_runner_returns_first_matching_tool(monkeypatch):
    monkeypatch.setattr(WeatherTool, "execute", lambda self, query: "weather answer")

    result = LiveAPIRunner().run("weather in Dallas")

    assert result["answer"] == "weather answer"
    assert result["tool_used"] == "weather"


def test_general_agent_returns_real_api_stage(monkeypatch):
    monkeypatch.setattr(LiveAPIRunner, "run", lambda self, query: {
        "answer": "weather answer",
        "tool_used": "weather",
        "all_results": [{"tool": "weather", "result": "weather answer"}],
    })

    result = GeneralAgent().run("What is the weather in Dallas?", session_id="real_api_test")

    assert result["answer"] == "weather answer"
    assert result["extra"]["source_stage"] == "real_api:weather"
    assert result["extra"]["verification"]["verified"]
