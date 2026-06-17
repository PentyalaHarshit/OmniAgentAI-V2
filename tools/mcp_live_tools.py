"""
MCP Live Data Tools
====================
Real-time data tools wired into GeneralAgent via MCPToolRunner.

Tools:
  WeatherTool        – Open-Meteo (free, no key) + geocoding
  NewsTool           – GNews RSS + optional NewsAPI key
  SportsTool         – TheSportsDB free API + ESPN public endpoint
  TrendingTool       – DuckDuckGo news search + Wikipedia current events
  CurrencyTool       – Open Exchange Rates (no key needed for latest)
  QuakeTool          – USGS real-time earthquake feed

All tools follow the same MCP contract:
    tool.execute(query: str) -> str   (empty string = no result)
"""

import re
import json
import logging
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
TIMEOUT = 8

HEADERS = {
    "User-Agent": "OmniAgentAI/1.0 (live-tools; contact@omniagentai.local)"
}


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get(url: str, as_text: bool = False):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read().decode("utf-8", errors="replace")
            return raw if as_text else json.loads(raw)
    except Exception as e:
        logger.warning("MCP HTTP GET error %s: %s", url, e)
        return None


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Tool 1 – Weather  (Open-Meteo, completely free, no key)
# ─────────────────────────────────────────────────────────────────────────────

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light showers", 81: "Showers", 82: "Heavy showers",
    85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


class WeatherTool:
    name = "weather"
    description = "Gets current weather for any city using Open-Meteo (free, no API key)."
    input_schema = {"query": "string – natural language weather question mentioning a city"}

    # Patterns that indicate a weather question
    TRIGGERS = re.compile(
        r"\b(weather|temperature|temp|rain|snow|sunny|cloudy|forecast|humidity|wind|hot|cold|climate)\b",
        re.I
    )
    # Extract city name from query. Word boundaries avoid matching "at" in
    # words such as "What", which used to capture "is the weather in Dallas".
    CITY_PATTERNS = [
        re.compile(
            r"\b(?:weather|temperature|forecast|rain|snow|humidity|wind)\s+"
            r"(?:in|at|for|of)\s+([A-Za-z][A-Za-z\s,.'-]*?)"
            r"(?:\?|$|\s+(?:today|now|tomorrow|tonight|this\s+week|next\s+week))",
            re.I,
        ),
        re.compile(
            r"\b(?:in|at|for)\s+([A-Za-z][A-Za-z\s,.'-]*?)"
            r"(?:\?|$|\s+(?:today|now|tomorrow|tonight|this\s+week|next\s+week))",
            re.I,
        ),
    ]

    def _geocode(self, city: str) -> tuple[float, float, str] | None:
        url = ("https://geocoding-api.open-meteo.com/v1/search?"
               + urllib.parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"}))
        data = _get(url)
        if not data or not data.get("results"):
            return None
        r = data["results"][0]
        return r["latitude"], r["longitude"], r.get("name", city) + ", " + r.get("country", "")

    def _extract_city(self, query: str) -> str:
        for pattern in self.CITY_PATTERNS:
            match = pattern.search(query)
            if match:
                city = match.group(1).strip().strip(",")
                city = re.sub(r"\s+", " ", city)
                return city

        # Fallback: grab the last capitalised word sequence.
        words = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*", query)
        return words[-1] if words else ""

    def execute(self, query: str) -> str:
        if not self.TRIGGERS.search(query):
            return ""

        city = self._extract_city(query)
        if not city:
            return ""

        geo = self._geocode(city)
        if not geo:
            return f"⚠️ Could not find location: **{city}**"

        lat, lon, label = geo
        wants_tomorrow = bool(re.search(r"\btomorrow\b", query, re.I))
        forecast_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weathercode",
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        }
        if wants_tomorrow:
            forecast_params.update({
                "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
                "forecast_days": 2,
            })

        url = (
            "https://api.open-meteo.com/v1/forecast?"
            + urllib.parse.urlencode(forecast_params)
        )
        data = _get(url)
        if not data:
            return ""

        if wants_tomorrow and data.get("daily"):
            daily = data["daily"]
            if len(daily.get("time", [])) > 1:
                code = daily.get("weathercode", [0, 0])[1]
                condition = WMO_CODES.get(code, "Unknown")
                high = daily.get("temperature_2m_max", ["N/A", "N/A"])[1]
                low = daily.get("temperature_2m_min", ["N/A", "N/A"])[1]
                rain = daily.get("precipitation_probability_max", ["N/A", "N/A"])[1]
                wind = daily.get("wind_speed_10m_max", ["N/A", "N/A"])[1]
                date = daily.get("time", ["", "tomorrow"])[1]
                return (
                    f"🌤️ **Tomorrow's Weather in {label}** ({date})\n\n"
                    f"- **Condition**: {condition}\n"
                    f"- **High / Low**: {high}°C / {low}°C\n"
                    f"- **Rain Chance**: {rain}%\n"
                    f"- **Max Wind Speed**: {wind} km/h\n\n"
                    f"*Source: [Open-Meteo](https://open-meteo.com) (forecast)*"
                )

        if "current" not in data:
            return ""

        c = data["current"]
        temp = c.get("temperature_2m", "N/A")
        humidity = c.get("relative_humidity_2m", "N/A")
        wind = c.get("wind_speed_10m", "N/A")
        code = c.get("weathercode", 0)
        condition = WMO_CODES.get(code, "Unknown")

        return (
            f"🌤️ **Current Weather in {label}**\n\n"
            f"- **Condition**: {condition}\n"
            f"- **Temperature**: {temp}°C\n"
            f"- **Humidity**: {humidity}%\n"
            f"- **Wind Speed**: {wind} km/h\n\n"
            f"*Source: [Open-Meteo](https://open-meteo.com) (real-time)*"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 2 – News  (GNews RSS, free + optional NewsAPI key)
# ─────────────────────────────────────────────────────────────────────────────

class NewsTool:
    name = "news"
    description = "Fetches latest news headlines from NewsAPI.org when configured, otherwise Google News RSS."
    input_schema = {"query": "string – news topic or question"}

    TRIGGERS = re.compile(
        r"\b(news|headline|latest|breaking|today|update|announce|report|current event)\b",
        re.I
    )

    def execute(self, query: str) -> str:
        if not self.TRIGGERS.search(query):
            return ""

        # Strip question words to get a clean search term
        topic = re.sub(
            r"\b(what|is|the|latest|news|about|on|any|tell me|give me|show|recent)\b", "",
            query, flags=re.I
        ).strip()
        topic = re.sub(r"\s+", " ", topic).strip() or query

        newsapi_key = os.getenv("NEWSAPI_KEY", "").strip()
        if newsapi_key:
            newsapi_result = self._newsapi(topic, newsapi_key)
            if newsapi_result:
                return newsapi_result

        url = ("https://news.google.com/rss/search?"
               + urllib.parse.urlencode({"q": topic, "hl": "en-US", "gl": "US", "ceid": "US:en"}))

        raw = _get(url, as_text=True)
        if not raw:
            return ""

        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            return ""

        items = root.findall(".//item")[:5]
        if not items:
            return ""

        lines = [f"📰 **Latest News: {topic.title()}**\n"]
        for item in items:
            title = _strip_html(item.findtext("title", ""))
            link = item.findtext("link", "")
            pub = item.findtext("pubDate", "")[:16] if item.findtext("pubDate") else ""
            if title:
                lines.append(f"- [{title}]({link}) *{pub}*")

        return "\n".join(lines) + "\n\n*Source: Google News RSS*"

    def _newsapi(self, topic: str, api_key: str) -> str:
        url = (
            "https://newsapi.org/v2/everything?"
            + urllib.parse.urlencode({
                "q": topic,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 5,
                "apiKey": api_key,
            })
        )
        data = _get(url)
        if not data or data.get("status") != "ok":
            return ""

        articles = data.get("articles", [])[:5]
        if not articles:
            return ""

        lines = [f"ðŸ“° **Latest News: {topic.title()}**\n"]
        for article in articles:
            title = _strip_html(article.get("title", ""))
            link = article.get("url", "")
            source = article.get("source", {}).get("name", "")
            published = (article.get("publishedAt") or "")[:10]
            if title and link:
                suffix = " ".join(p for p in [source, published] if p)
                lines.append(f"- [{title}]({link}) *{suffix}*")

        return "\n".join(lines) + "\n\n*Source: NewsAPI.org*"


# ─────────────────────────────────────────────────────────────────────────────
# Tool 3 – Sports  (TheSportsDB free API + ESPN public)
# ─────────────────────────────────────────────────────────────────────────────

class SportsTool:
    name = "sports"
    description = "Fetches live scores, team info, and recent match results."
    input_schema = {"query": "string – sports question (team, league, score, match)"}

    TRIGGERS = re.compile(
        r"\b(sport|football|soccer|basketball|cricket|tennis|nba|nfl|ipl|premier league|"
        r"la liga|bundesliga|serie a|score|match|game|team|player|standings|fixture|result)\b",
        re.I
    )

    # Team name → TheSportsDB team ID (common ones)
    TEAM_IDS = {
        "manchester united": "133604", "chelsea": "133610",
        "arsenal": "133602", "liverpool": "133602",
        "real madrid": "133739", "barcelona": "133739",
        "lakers": "134870", "warriors": "134860",
        "india": "135264",  # cricket
    }

    def _search_team(self, name: str) -> dict | None:
        url = ("https://www.thesportsdb.com/api/v1/json/3/searchteams.php?"
               + urllib.parse.urlencode({"t": name}))
        data = _get(url)
        if data and data.get("teams"):
            return data["teams"][0]
        return None

    def _last_events(self, team_id: str) -> list:
        url = f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={team_id}"
        data = _get(url)
        return data.get("results", []) if data else []

    def execute(self, query: str) -> str:
        if not self.TRIGGERS.search(query):
            return ""

        # Extract potential team/player name
        clean = re.sub(
            r"\b(what|is|the|score|result|latest|news|about|match|game|did|win|lose|"
            r"played|team|standing|fixture|of|for|in)\b", "",
            query, flags=re.I
        ).strip()
        clean = re.sub(r"\s+", " ", clean).strip()

        if not clean:
            return ""

        team_data = self._search_team(clean)
        if not team_data:
            return ""

        team_name = team_data.get("strTeam", clean)
        team_id = team_data.get("idTeam", "")
        sport = team_data.get("strSport", "")
        league = team_data.get("strLeague", "")
        country = team_data.get("strCountry", "")
        formed = team_data.get("intFormedYear", "")
        stadium = team_data.get("strStadium", "")

        lines = [
            f"🏆 **{team_name}** ({sport})",
            f"- **League**: {league}",
            f"- **Country**: {country}",
            f"- **Stadium**: {stadium}" if stadium else "",
            f"- **Founded**: {formed}" if formed else "",
            "",
        ]

        # Recent results
        if team_id:
            events = self._last_events(team_id)
            if events:
                lines.append("**Recent Results:**")
                for ev in events[:3]:
                    home = ev.get("strHomeTeam", "")
                    away = ev.get("strAwayTeam", "")
                    hscore = ev.get("intHomeScore", "?")
                    ascore = ev.get("intAwayScore", "?")
                    date = ev.get("dateEvent", "")
                    lines.append(f"- {date}: **{home} {hscore} – {ascore} {away}**")

        lines.append("\n*Source: [TheSportsDB](https://www.thesportsdb.com)*")
        return "\n".join(l for l in lines if l is not None)


# ─────────────────────────────────────────────────────────────────────────────
# Tool 4 – Trending / Live Search  (DuckDuckGo news + Wikipedia current events)
# ─────────────────────────────────────────────────────────────────────────────

class TrendingTool:
    name = "trending"
    description = "Returns trending news/events using DuckDuckGo news search and Wikipedia current events."
    input_schema = {"query": "string – what is happening, trending, or live events"}

    TRIGGERS = re.compile(
        r"\b(trending|viral|happening|live|right now|today|current event|what.s new|"
        r"breaking|recently|just happened|2024|2025|2026)\b",
        re.I
    )

    def _ddg_news(self, query: str) -> str:
        url = ("https://api.duckduckgo.com/?"
               + urllib.parse.urlencode({
                   "q": f"{query} news",
                   "format": "json",
                   "no_html": "1",
                   "t": "OmniAgentAI",
               }))
        data = _get(url)
        if not data:
            return ""

        results = data.get("RelatedTopics", [])[:5]
        lines = []
        for r in results:
            if isinstance(r, dict) and r.get("Text"):
                text = _strip_html(r["Text"])
                url_link = r.get("FirstURL", "")
                lines.append(f"- [{text[:120]}]({url_link})" if url_link else f"- {text[:120]}")

        return "\n".join(lines)

    def _wikipedia_current(self) -> str:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/Portal:Current_events"
        data = _get(url)
        if data and data.get("extract"):
            return _strip_html(data["extract"])[:600]
        return ""

    def execute(self, query: str) -> str:
        if not self.TRIGGERS.search(query):
            return ""

        lines = [f"🔥 **Trending / Live: {query.strip('?').title()}**\n"]

        ddg = self._ddg_news(query)
        if ddg:
            lines.append("**From DuckDuckGo:**")
            lines.append(ddg)
            lines.append("")

        wiki = self._wikipedia_current()
        if wiki:
            lines.append("**From Wikipedia Current Events:**")
            lines.append(wiki)

        if len(lines) <= 1:
            return ""

        lines.append("\n*Sources: DuckDuckGo · Wikipedia*")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Tool 5 – Currency / Exchange Rates  (Frankfurter, free, no key)
# ─────────────────────────────────────────────────────────────────────────────

class CurrencyTool:
    name = "currency"
    description = "Gets live currency exchange rates using Frankfurter API (free, no key)."
    input_schema = {"query": "string – currency conversion or exchange rate question"}

    TRIGGERS = re.compile(
        r"\b(currency|exchange rate|convert|usd|eur|gbp|inr|jpy|cny|aud|cad|"
        r"dollar|euro|pound|rupee|yen|yuan|franc|krona|peso)\b",
        re.I
    )
    PAIR_RE = re.compile(
        r"(\d+\.?\d*)\s*([A-Za-z]{3})\s+(?:to|in|=|into)\s+([A-Za-z]{3})", re.I
    )
    FROM_RE = re.compile(r"\b([A-Za-z]{3})\s+(?:to|in|into)\s+([A-Za-z]{3})\b", re.I)

    def execute(self, query: str) -> str:
        if not self.TRIGGERS.search(query):
            return ""

        amount = 1.0
        from_cur = "USD"
        to_cur = "EUR"

        m = self.PAIR_RE.search(query)
        if m:
            amount = float(m.group(1))
            from_cur = m.group(2).upper()
            to_cur = m.group(3).upper()
        else:
            m2 = self.FROM_RE.search(query)
            if m2:
                from_cur = m2.group(1).upper()
                to_cur = m2.group(2).upper()

        url = f"https://api.frankfurter.app/latest?from={from_cur}&to={to_cur}"
        data = _get(url)
        if not data or "rates" not in data:
            return ""

        rate = data["rates"].get(to_cur)
        if rate is None:
            return ""

        converted = round(amount * rate, 4)
        date = data.get("date", "today")

        return (
            f"💱 **Exchange Rate** ({date})\n\n"
            f"**{amount} {from_cur}** = **{converted} {to_cur}**\n"
            f"- Rate: 1 {from_cur} = {rate} {to_cur}\n\n"
            f"*Source: [Frankfurter API](https://www.frankfurter.app)*"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 6 – Earthquakes  (USGS real-time feed, free, no key)
# ─────────────────────────────────────────────────────────────────────────────

class EarthquakeTool:
    name = "earthquake"
    description = "Fetches recent significant earthquakes from USGS real-time feed."
    input_schema = {"query": "string – earthquake or seismic activity question"}

    TRIGGERS = re.compile(r"\b(earthquake|quake|seismic|tremor|richter|magnitude)\b", re.I)

    def execute(self, query: str) -> str:
        if not self.TRIGGERS.search(query):
            return ""

        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson"
        data = _get(url)
        if not data or "features" not in data:
            return ""

        features = data["features"][:5]
        if not features:
            return "No significant earthquakes reported this week. 🟢"

        lines = ["🌍 **Recent Significant Earthquakes** (past 7 days, USGS)\n"]
        for f in features:
            props = f["properties"]
            place = props.get("place", "Unknown location")
            mag = props.get("mag", "?")
            ts = props.get("time", 0)
            dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            detail_url = props.get("url", "")
            lines.append(f"- **M{mag}** – {place} ({dt}) [details]({detail_url})")

        lines.append("\n*Source: [USGS Earthquake Hazards Program](https://earthquake.usgs.gov)*")
        return "\n".join(lines)


class SearchAPITool:
    name = "search"
    description = "Searches the web using SerpApi when configured, otherwise DuckDuckGo Instant Answer API."
    input_schema = {"query": "string - explicit web/search question"}

    TRIGGERS = re.compile(
        r"\b(search|web search|look up|lookup|find online|sources for|source for|google)\b",
        re.I,
    )

    def __init__(self):
        self.serpapi_key = os.getenv("SERPAPI_API_KEY", "").strip()

    def execute(self, query: str) -> str:
        if not self.TRIGGERS.search(query):
            return ""

        search_query = self._clean_query(query)
        if not search_query:
            return ""

        if self.serpapi_key:
            result = self._serpapi(search_query)
            if result:
                return result

        return self._duckduckgo(search_query)

    def _clean_query(self, query: str) -> str:
        cleaned = re.sub(
            r"\b(please|can you|could you|search|web search|look up|lookup|find online|google|for|me)\b",
            " ",
            query,
            flags=re.I,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ?.")
        return cleaned or query.strip(" ?.")

    def _serpapi(self, query: str) -> str:
        url = (
            "https://serpapi.com/search.json?"
            + urllib.parse.urlencode({
                "engine": "google",
                "q": query,
                "num": 5,
                "api_key": self.serpapi_key,
            })
        )
        data = _get(url)
        if not data:
            return ""

        results = data.get("organic_results", [])[:5]
        if not results:
            return ""

        lines = [f"**Search Results: {query}**", ""]
        for item in results:
            title = _strip_html(item.get("title", "Untitled"))
            link = item.get("link", "")
            snippet = _strip_html(item.get("snippet", ""))
            if title and link:
                lines.append(f"- [{title}]({link})")
                if snippet:
                    lines.append(f"  {snippet}")

        lines.append("\n*Source: SerpApi Google Search API*")
        return "\n".join(lines)

    def _duckduckgo(self, query: str) -> str:
        url = (
            "https://api.duckduckgo.com/?"
            + urllib.parse.urlencode({
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            })
        )
        data = _get(url)
        if not data:
            return ""

        lines = [f"**Search Result: {query}**", ""]
        abstract = _strip_html(data.get("AbstractText", ""))
        abstract_url = data.get("AbstractURL", "")
        heading = data.get("Heading", query)
        if abstract:
            if abstract_url:
                lines.append(f"- [{heading}]({abstract_url})")
            else:
                lines.append(f"- {heading}")
            lines.append(f"  {abstract}")

        related = data.get("RelatedTopics", [])
        for item in related:
            if len(lines) >= 9:
                break
            if not isinstance(item, dict):
                continue
            text = _strip_html(item.get("Text", ""))
            link = item.get("FirstURL", "")
            if text and link:
                lines.append(f"- [{text[:140]}]({link})")

        if len(lines) <= 2:
            return ""

        lines.append("\n*Source: DuckDuckGo Instant Answer API*")
        return "\n".join(lines)


class LiveAPIRunner:
    """
    Runs real/live API tools before the slower open-domain RAG path.

    Contract:
        run(query) -> {"answer": str, "tool_used": str, "all_results": list}
    """

    def __init__(self):
        self.tools = [
            WeatherTool(),
            NewsTool(),
            SportsTool(),
            SearchAPITool(),
            TrendingTool(),
            CurrencyTool(),
            EarthquakeTool(),
        ]

    def run(self, query: str) -> dict:
        all_results = []
        for tool in self.tools:
            try:
                result = tool.execute(query)
            except Exception as e:
                logger.warning("Live API tool %s raised: %s", tool.name, e)
                result = ""

            all_results.append({"tool": tool.name, "result": result})
            if result:
                return {
                    "answer": result,
                    "tool_used": tool.name,
                    "all_results": all_results,
                }

        return {"answer": "", "tool_used": "", "all_results": all_results}
